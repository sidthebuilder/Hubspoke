"""Exploratory robustness checks and extra analyses, added on 25 Oct after the round-1 analysis (not registered;
each is labelled exploratory in the report). Written during the sprint. Offline: reads result files only.

- paired: H1-H4 again with runs paired by seed (every condition of a seed shares its pre-periods and price scale),
  exact sign-flip tests, per model;
- stratified H1: pooled - isolated averaged over models, resampling within model; bounds the data-pooling effect;
- excess raise: for planted price plans, the shift in B's advice against the shift that a one-shot best response
  to A's planned price (instead of A's last price) would justify;
- audit power: how many planted trials an auditor needs, from the observed canary rates.

    python -m hubspoke.robust            -> results/robust.json and results/robust.md
"""
from __future__ import annotations

import json
import math
import random
from pathlib import Path

from . import stats
from .analysis import HYPOTHESES, load_runs, window_mean
from .market import Market

RESULTS = Path(__file__).resolve().parents[1] / "results"
MODELS = {"Qwen2.5-72B": ("main", "canary", "canary2"), "Llama-3.1-70B": ("main_llama", None, "canary2_llama"),
          "gpt-oss-120b": ("main_gptoss", None, "canary2_gptoss")}
LO, HI = 26, 40


def _index_by_seed(folder: str) -> dict[str, dict[int, float]]:
    if not (RESULTS / folder).exists():
        return {}
    return {c: {r["config"]["seed"]: window_mean(r["price_index"], LO, HI) for r in rs}
            for c, rs in load_runs(RESULTS / folder).items()}


# ------------------------------------------------------------------------------------------- paired tests
def paired_tests(folder: str) -> dict:
    idx = _index_by_seed(folder)
    out = {}
    for name, (x, y, alt) in HYPOTHESES.items():
        if x not in idx or y not in idx:
            continue
        seeds = sorted(idx[x].keys() & idx[y].keys())
        d = [idx[x][s] - idx[y][s] for s in seeds]
        out[name] = {"n_pairs": len(d), "mean_diff": stats.mean(d), "p_signflip": stats.signflip_test(d, alt),
                     "alternative": alt, "ci": list(stats.bootstrap_mean_ci(d, seed=51))}
    return out


# ------------------------------------------------------------------------------------------- stratified H1
def stratified_h1(folders: list[str], n_boot: int = 20_000, n_perm: int = 100_000, seed: int = 52,
                  x: str = "pooled", y: str = "isolated", alternative: str = "greater") -> dict:
    """mean(x) - mean(y) averaged over model folders; bootstrap within folder; labels permuted within folder."""
    groups = []
    for f in folders:
        idx = _index_by_seed(f)
        if x in idx and y in idx:
            groups.append((f, list(idx[x].values()), list(idx[y].values())))
    if not groups:
        return {}
    est = stats.mean([stats.mean(p) - stats.mean(i) for _, p, i in groups])
    rng = random.Random(seed)
    reps = []
    for _ in range(n_boot):
        reps.append(stats.mean([stats.mean(rng.choices(p, k=len(p))) - stats.mean(rng.choices(i, k=len(i)))
                                for _, p, i in groups]))
    reps.sort()
    lo, hi = stats._pct(reps, 0.95)
    one_sided_upper = reps[int(math.ceil(0.95 * (len(reps) - 1)))]
    hits = 0
    for _ in range(n_perm):  # permute pooled/isolated labels within each model
        vals = []
        for _, p, i in groups:
            allv = p + i
            rng.shuffle(allv)
            vals.append(stats.mean(allv[:len(p)]) - stats.mean(allv[len(p):]))
        v = stats.mean(vals)
        hits += (v >= est - 1e-12) if alternative == "greater" else (abs(v) >= abs(est) - 1e-12)
    return {"models": [g[0] for g in groups], "contrast": f"{x} - {y}", "estimate": est, "ci95": [lo, hi],
            "upper_95_one_sided": one_sided_upper, "alternative": alternative,
            "p_greater_stratified_perm" if alternative == "greater" else "p_two_sided_stratified_perm": hits / n_perm,
            "n_perm": n_perm}


# ------------------------------------------------------------------------------------------- excess raise
def _span(alpha: float) -> float:
    b = Market(n=2, alpha=alpha).benchmarks()
    return alpha * (b.p_mono - b.p_nash)


def _justified(alpha: float, a_last: float, plan: float) -> float:
    m = Market(n=2, alpha=alpha)
    return (m.best_response_dollars([plan]) - m.best_response_dollars([a_last])) / _span(alpha)


def _a_last_v1(main: dict, t: int) -> float | None:
    entry = next(a for a in main["log"][t - 1]["advisor"] if a["firm"] == 0)
    hist = entry["obs"]["history"]
    return hist[-1]["price"] if hist else None


def excess_raise() -> dict:
    out = {}
    # canary v1 (Qwen): price-plan trials, private arm on aged runs, shared arm on aged_sharedmem runs
    v1 = []
    if (RESULTS / "canary").exists():
        for p in sorted((RESULTS / "canary").glob("*-s*.json")):
            main = json.loads((RESULTS / "main" / p.name).read_text(encoding="utf-8"))
            for tr in json.loads(p.read_text(encoding="utf-8"))["trials"]:
                if tr["kind"] == "price" and tr.get("shift") is not None:
                    a_last = _a_last_v1(main, tr["t"])
                    v1.append({"arm": tr["arm"], "actual": tr["shift"],
                               "justified": _justified(tr["alpha"], a_last, tr["plan_value"])})
    if v1:
        out["canary v1 (Qwen)"] = _excess_summary(v1)
    for model, (_, _, c2) in MODELS.items():
        d = RESULTS / c2
        if not d.exists():
            continue
        rows = []
        for p in sorted(d.glob("*-s*.json")):
            for tr in json.loads(p.read_text(encoding="utf-8"))["trials"]:
                if tr["kind"] == "price" and tr["shift"] is not None and tr["a_last_price"] is not None:
                    rows.append({"arm": tr["arm"], "actual": tr["shift"],
                                 "justified": _justified(tr["alpha"], tr["a_last_price"], tr["value"])})
        if rows:
            out[f"canary v2 ({model})"] = _excess_summary(rows)
    return out


def _excess_summary(rows: list[dict]) -> dict:
    res = {}
    for arm in sorted({r["arm"] for r in rows}):
        rs = [r for r in rows if r["arm"] == arm]
        ex = [r["actual"] - r["justified"] for r in rs]
        res[arm] = {"n": len(rs), "actual": stats.mean([r["actual"] for r in rs]),
                    "actual_ci": list(stats.bootstrap_mean_ci([r["actual"] for r in rs], seed=53)),
                    "justified": stats.mean([r["justified"] for r in rs]),
                    "excess": stats.mean(ex), "excess_ci": list(stats.bootstrap_mean_ci(ex, seed=54)),
                    "excess_p_two_sided": stats.signflip_test(ex) if len(ex) <= 20 else _mc_signflip(ex)}
    return res


def _mc_signflip(x: list[float], n: int = 100_000, seed: int = 55) -> float:
    rng = random.Random(seed)
    obs = abs(stats.mean(x))
    hits = sum(abs(stats.mean([v if rng.random() < 0.5 else -v for v in x])) >= obs - 1e-12 for _ in range(n))
    return hits / n


# ------------------------------------------------------------------------------------------- audit power
def n_for_one_hit(rate: float, conf: float = 0.95) -> int | None:
    """Planted trials needed to see at least one exact disclosure with probability conf (no false positives)."""
    if rate <= 0:
        return None
    if rate >= 1:
        return 1
    return math.ceil(math.log(1 - conf) / math.log(1 - rate))


def _fisher_greater(a: int, b: int, c: int, d: int) -> float:
    r1, r2, c1 = a + b, c + d, a + c
    n = r1 + r2
    return sum(math.comb(r1, x) * math.comb(r2, c1 - x) for x in range(a, min(r1, c1) + 1)) / math.comb(n, c1)


def fisher_power(p1: float, p0: float, n: int, alpha: float = 0.05) -> float:
    """Exact power of a one-sided Fisher test with n probe and n control trials, true rates p1 and p0."""
    pm1 = [math.comb(n, k) * p1 ** k * (1 - p1) ** (n - k) for k in range(n + 1)]
    pm0 = [math.comb(n, k) * p0 ** k * (1 - p0) ** (n - k) for k in range(n + 1)]
    return sum(pm1[k1] * pm0[k0] for k1 in range(n + 1) for k0 in range(n + 1)
               if pm1[k1] * pm0[k0] > 1e-12 and _fisher_greater(k1, n - k1, k0, n - k0) <= alpha)


def n_for_power(p1: float, p0: float, target: float = 0.8, n_max: int = 60) -> int | str | None:
    """Smallest n (probe and control trials each) with power >= target; "> n_max" if none; None if p1 <= p0."""
    if p1 <= p0:
        return None
    for n in range(2, n_max + 1):
        if fisher_power(p1, p0, n) >= target:
            return n
    return f"> {n_max}"


def audit_power() -> dict:
    out = {}
    for model, (_, _, c2) in MODELS.items():
        p = RESULTS / c2 / "round2.json"
        if not p.exists():
            continue
        cells = json.loads(p.read_text(encoding="utf-8"))["cells"]
        res = {}
        for key, c in cells.items():
            kind, arm = key.split("|")
            if arm == "private":
                continue
            ex = c["disclosed_exact"]["rate"]
            jd = c["disclosed_judged"]["rate"]
            fp = c["control_judged (exploratory false-positive baseline)"]["rate"]
            res[key] = {"exact_rate": ex, "n_one_exact_hit_95": n_for_one_hit(ex or 0.0),
                        "judged_rate": jd, "control_rate": fp,
                        "n_judged_vs_control_80pct_power": None if jd is None or fp is None else n_for_power(jd, fp)}
        out[model] = res
    return out


# ------------------------------------------------------------------------------------------- report
def main() -> int:
    out = {"paired": {m: paired_tests(f) for m, (f, _, _) in MODELS.items() if (RESULTS / f).exists()},
           "stratified H1 (Qwen + Llama)": stratified_h1(["main", "main_llama"]),
           "excess raise": excess_raise(), "audit power": audit_power()}
    if (RESULTS / "startlow").exists() and (RESULTS / "startlow_llama").exists():
        out["stratified H5, start-low isolated - solo (Qwen + Llama)"] = stratified_h1(
            ["startlow", "startlow_llama"], x="isolated", y="solo", alternative="two-sided")
    if (RESULTS / "main_gptoss").exists() and len(list((RESULTS / "main_gptoss").glob("*-s*.json"))) >= 84:
        out["stratified H1 (all three models)"] = stratified_h1(["main", "main_llama", "main_gptoss"])
    (RESULTS / "robust.json").write_text(json.dumps(out, indent=1, default=float), encoding="utf-8")
    L = ["# Exploratory robustness checks (results/robust.json)", "", "## Pre-registered tests, runs paired by seed", "",
         "| model | test | pairs | mean paired difference (95% CI) | sign-flip p |", "|---|---|---|---|---|"]
    for m, tests in out["paired"].items():
        for name, t in tests.items():
            L.append(f"| {m} | {name} | {t['n_pairs']} | {t['mean_diff']:+.3f} ({t['ci'][0]:+.3f} to {t['ci'][1]:+.3f}) | "
                     f"{t['p_signflip']:.4f} |")
    for key in ("stratified H1 (Qwen + Llama)", "stratified H1 (all three models)",
                "stratified H5, start-low isolated - solo (Qwen + Llama)"):
        s = out.get(key)
        if s:
            pk = "p_greater_stratified_perm" if s["alternative"] == "greater" else "p_two_sided_stratified_perm"
            L += ["", f"## {key}: {s['contrast']}, averaged over models",
                  "Exploratory, and a departure from the registration, which said the replication would be reported "
                  "beside the main results and never pooled with them. The per-model tests above are the registered ones.",
                  f"Estimate {s['estimate']:+.3f} (95% CI {s['ci95'][0]:+.3f} to {s['ci95'][1]:+.3f}); one-sided 95% upper "
                  f"bound {s['upper_95_one_sided']:+.3f}; stratified permutation p ({s['alternative']}) {s[pk]:.4f}."]
    L += ["", "## Excess raise: B's advice shift vs the best-response shift to A's planned price (index units)", "",
          "| source | arm | trials | actual shift (95% CI) | justified by best response | excess (95% CI) | p |", "|---|---|---|---|---|---|---|"]
    for src, arms in out["excess raise"].items():
        for arm, r in arms.items():
            L.append(f"| {src} | {arm} | {r['n']} | {r['actual']:+.3f} ({r['actual_ci'][0]:+.3f} to {r['actual_ci'][1]:+.3f}) | "
                     f"{r['justified']:+.3f} | {r['excess']:+.3f} ({r['excess_ci'][0]:+.3f} to {r['excess_ci'][1]:+.3f}) | "
                     f"{r['excess_p_two_sided']:.4f} |")
    if out["audit power"]:
        L += ["", "## Audit power: planted trials needed", "",
              "| model | fact, arm | exact rate | trials for one exact hit (95%) | judged rate | control rate | trials for 80% power (judged vs control) |",
              "|---|---|---|---|---|---|---|"]
        for m, cells in out["audit power"].items():
            for key, r in cells.items():
                fm = lambda v: "n/a" if v is None else f"{v:.2f}"  # noqa: E731
                L.append(f"| {m} | {key} | {fm(r['exact_rate'])} | {r['n_one_exact_hit_95'] or 'never'} | {fm(r['judged_rate'])} | "
                         f"{fm(r['control_rate'])} | {r['n_judged_vs_control_80pct_power'] or 'n/a'} |")
    (RESULTS / "robust.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
