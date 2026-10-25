"""verify: rebuild every result from the cached model replies, then recompute the headline numbers independently.
Written during the sprint.

1. Replay. Every main run is played again with HUBSPOKE_OFFLINE=1: every model call must be answered from the
   cache (a cache miss is an error), and the replayed prices must equal the stored ones. The fork, replay,
   canary and (exploratory) live-replay measures are recomputed the same way. This shows the stored run files
   follow from the raw replies.
2. Recompute. The outcome of every run is recomputed from raw posted prices with numpy and freshly computed
   benchmarks, and the H1-H4 p-values with scipy's exact permutation test. Both are compared with numbers.json.
Round 2: start-low folders are compared with their round2.json (H5 with scipy, H6 by brute-force sign flips);
canary-v2 folders are rebuilt from the cache and every cell and Fisher test is recounted (scipy); `--src judge`
re-runs the judge on every judged note from the cache.
Writes results/verify_<src>.txt; exits 1 if anything differs.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
TOL = 1e-9
SUFFIX_CONFIG = {"_llama": "modal_llama70b.json", "_gptoss": "modal_gptoss120b.json"}
CANARY2_BASE = {"canary2": "main", "canary2_llama": "main_llama", "canary2_gptoss": "main_gptoss"}


def config_for(folder: str) -> str:
    """The config of the model a result folder was made with (folder names end in _llama / _gptoss, or Qwen)."""
    for suffix, conf in SUFFIX_CONFIG.items():
        if folder.endswith(suffix):
            return conf
    return "modal_qwen72b.json"


def verify_round2(src: str) -> int:
    """Round 2: rebuild a canary-v2 folder from the cache (offline), or re-run the disclosure judge on every judged
    note from the cache (src = "judge") and compare its labels with results/judged.json."""
    os.environ["HUBSPOKE_OFFLINE"] = "1"
    from . import canary2, judge
    from .agents import LLMAdvisor
    from .cli import load_config
    from .llm import LLMClient

    lines, bad = [], 0

    def check(ok: bool, msg: str):
        nonlocal bad
        lines.append(("ok   " if ok else "FAIL ") + msg)
        bad += 0 if ok else 1

    if src == "judge":
        cfg, spec = load_config(str(ROOT / "configs" / "modal_qwen72b.json"))  # the registered judge model
        client = LLMClient(spec, ROOT / cfg["cache"])
        stored = json.loads((RESULTS / "judged.json").read_text(encoding="utf-8"))
        items = judge.v1_items(RESULTS)
        for folder in CANARY2_BASE:
            if (RESULTS / folder).exists():
                items += judge.v2_items(RESULTS / folder)
        same = missing = 0
        for it in items:
            if it["key"] not in stored:
                missing += 1
                continue
            try:
                same += judge.judge_one(client, it)["label"] == stored[it["key"]]["label"]
            except Exception as e:  # a cache miss: the stored label does not follow from a stored reply
                check(False, f"judge {it['key']}: {type(e).__name__}: {e}")
        n = len(items) - missing
        check(same == n, f"judge: {same}/{n} stored labels rebuilt from the cache ({missing} notes not judged yet)")
    else:
        cfg, spec = load_config(str(ROOT / "configs" / config_for(src)))
        client = LLMClient(spec, ROOT / cfg["cache"])
        base = CANARY2_BASE[src]
        for p in sorted((RESULTS / src).glob("*-s*.json")):
            stored = json.loads(p.read_text(encoding="utf-8"))["trials"]
            res = json.loads((RESULTS / base / p.name).read_text(encoding="utf-8"))
            try:
                again = canary2.canary2_trials(res, LLMAdvisor(client, res["config"]["temperature"]))
                key = lambda t: (t["arm"], t["kind"], t["t"], t["written"], t["exposed"], t["disclosed_exact"],  # noqa: E731
                                 t["b_price"], t["b_price_control"], t["b_note"])
                check([key(t) for t in again] == [key(t) for t in stored], f"canary2 {src}/{p.stem}: rebuilt from cache")
            except Exception as e:
                check(False, f"canary2 {src}/{p.stem}: {type(e).__name__}: {e}")
        recompute_canary2(src, check)
    lines.append(f"\n{bad} failure(s); client stats {client.stats}")
    (RESULTS / f"verify_{src}.txt").write_text("\n".join(lines), encoding="utf-8")
    return 1 if bad else 0


def main(argv=None) -> int:
    os.environ["HUBSPOKE_OFFLINE"] = "1"
    import numpy as np
    from scipy import stats as sps

    from . import canary, forks, replay
    from .agents import LLMAdvisor
    from .cli import llm_agents, load_config
    from .game import Game, RunConfig
    from .llm import LLMClient
    from .market import Market

    src = (argv or sys.argv[1:] or ["main"])[0]
    if src.startswith("canary2") or src == "judge":
        return verify_round2(src)
    cfg, spec = load_config(str(ROOT / "configs" / config_for(src)))
    client = LLMClient(spec, ROOT / cfg["cache"])
    lines, bad = [], 0

    def check(ok: bool, msg: str):
        nonlocal bad
        lines.append(("ok   " if ok else "FAIL ") + msg)
        bad += 0 if ok else 1

    runs = {}
    for p in sorted((RESULTS / src).glob("*-s*.json")):
        r = json.loads(p.read_text(encoding="utf-8"))
        runs[p.stem] = r
        rc = RunConfig(**r["config"])
        sellers, advisor = llm_agents(rc, client)
        g = Game(rc, sellers, advisor)
        try:
            g.run()
            same = [row["prices"] for row in g.log] == [row["prices"] for row in r["log"]]
            check(same, f"replay {p.stem}: {len(g.log)} periods rebuilt from cache")
        except Exception as e:  # a cache miss means the run file does not follow from the stored replies
            check(False, f"replay {p.stem}: {type(e).__name__}: {e}")

    secondary = () if src != "main" else (
                    ("forks", lambda res: forks.fork_run(res, lambda rc: llm_agents(rc, client))),
                     ("replay", lambda res: replay.replay_run(res, LLMAdvisor(client, res["config"]["temperature"]))),
                     ("canary", lambda res: {"trials": canary.canary_trials(res, LLMAdvisor(client, res["config"]["temperature"]))}),
                     ("livereplay", lambda res: replay.live_replay_run(res, LLMAdvisor(client, res["config"]["temperature"]))))
    for kind, fn in secondary:
        for p in sorted((RESULTS / kind).glob("*-s*.json")) if (RESULTS / kind).exists() else []:
            stored = json.loads(p.read_text(encoding="utf-8"))
            try:
                again = fn(runs[p.stem])
                keys = {"forks": ["excess_cut", "net_gain_pct", "placebo_gain_pct", "reaction"],
                        "replay": ["data_effect", "memo_effect", "abs_noise"],
                        "livereplay": ["dist_same", "dist_nolive"]}.get(kind)
                if keys:
                    same = all((again[k] is None and stored[k] is None) or abs(again[k] - stored[k]) < TOL for k in keys)
                else:
                    same = [(t["disclosed"], t["written"], t["b_price"]) for t in again["trials"]] == \
                           [(t["disclosed"], t["written"], t["b_price"]) for t in stored["trials"]]
                check(same, f"{kind} {p.stem}: recomputed from cache")
            except Exception as e:
                check(False, f"{kind} {p.stem}: {type(e).__name__}: {e}")

    nfile = RESULTS / src / "numbers.json"
    if nfile.exists():
        numbers = json.loads(nfile.read_text(encoding="utf-8"))
        lo, hi = numbers["summary"]["window"]
        by_cond: dict[str, list[float]] = {}
        for stem, r in sorted(runs.items()):
            m = Market(n=r["config"]["n"], alpha=r["alpha"])
            pn, pm = m.nash_price(), m.monopoly_price()
            prices = np.array([row["prices"] for row in r["log"]], dtype=float)[lo - 1: hi] / r["alpha"]
            by_cond.setdefault(r["config"]["condition"], []).append(float(((prices - pn) / (pm - pn)).mean()))
        for c, xs in by_cond.items():
            if c not in numbers["summary"]["conditions"]:  # exploratory conditions are not in the main tables
                continue
            stored = numbers["summary"]["conditions"][c]["index_mean"]
            check(abs(float(np.mean(xs)) - stored) < 1e-9, f"index mean {c}: {np.mean(xs):.6f} vs numbers.json {stored:.6f}")
        for name, t in numbers["tests"].items():
            if "p" not in t:
                continue
            x, y = np.array(by_cond[t["x"]]), np.array(by_cond[t["y"]])
            alt = {"greater": "greater", "less": "less", "two-sided": "two-sided"}[t["alternative"]]
            res = sps.permutation_test((x, y), lambda a, b, axis=-1: np.mean(a, axis=axis) - np.mean(b, axis=axis),
                                       permutation_type="independent", alternative=alt, n_resamples=np.inf,
                                       vectorized=True, batch=100_000)
            check(abs(res.pvalue - t["p"]) < 1e-9, f"{name}: p = {res.pvalue:.4f} (scipy, exact) vs {t['p']:.4f}")
    elif (RESULTS / src / "round2.json").exists():
        recompute_startlow(src, runs, check)
    else:
        lines.append(f"note: {nfile} not found; run `python -m hubspoke analyse --src {src}` first")

    lines.append(f"\n{bad} failure(s); client stats {client.stats}")
    (RESULTS / f"verify_{src}.txt").write_text("\n".join(lines), encoding="utf-8")
    return 1 if bad else 0


def _index_np(r: dict, prices_dollars) -> "object":
    """Price index of dollar prices, with benchmarks computed afresh (not read from the run file)."""
    import numpy as np

    from .market import Market

    m = Market(n=r["config"]["n"], alpha=r["alpha"])
    pn, pm = m.nash_price(), m.monopoly_price()
    return (np.asarray(prices_dollars, dtype=float) / r["alpha"] - pn) / (pm - pn)


def _signflip_np(x) -> float:
    """Two-sided exact sign-flip p-value by brute force over every sign pattern (independent of stats.py)."""
    import itertools

    import numpy as np

    x = np.asarray(x, dtype=float)
    obs = abs(x.mean())
    hits = total = 0
    for signs in itertools.product((1.0, -1.0), repeat=len(x)):
        total += 1
        hits += abs((np.asarray(signs) * x).mean()) >= obs - 1e-12
    return hits / total


def recompute_startlow(src: str, runs: dict, check) -> None:
    """Start-low (R2.3): recompute every condition's outcome and pre-period level from raw prices, and H5 / H6
    with scipy (exact permutation test) and a brute-force sign flip; compare with round2.json."""
    import numpy as np
    from scipy import stats as sps

    stored = json.loads((RESULTS / src / "round2.json").read_text(encoding="utf-8"))
    lo, hi = stored["window"]
    by: dict[str, dict[int, tuple[float, float]]] = {}
    for r in runs.values():
        win = np.array([row["prices"] for row in r["log"]], dtype=float)[lo - 1: hi]
        out = float(_index_np(r, win).mean())
        pre = [row["price"] for rows in r["final_state"]["rows"] for row in rows if row["t"] <= 0]
        start = float(_index_np(r, pre).mean())
        by.setdefault(r["config"]["condition"], {})[r["config"]["seed"]] = (out, start)
    for c, v in stored["conditions"].items():
        xs = np.array([o for o, _ in by[c].values()])
        ch = np.array([o - s for o, s in by[c].values()])
        check(abs(xs.mean() - v["index"]["mean"]) < 1e-9, f"start-low {c}: index {xs.mean():+.6f} vs round2.json "
              f"{v['index']['mean']:+.6f}")
        check(abs(ch.mean() - v["change"]["mean"]) < 1e-9, f"start-low {c}: change from pre-periods {ch.mean():+.6f} vs "
              f"{v['change']['mean']:+.6f}")
    h5 = stored["H5 isolated vs solo"]
    x = np.array([o for o, _ in by["isolated"].values()])
    y = np.array([o for o, _ in by["solo"].values()])
    res = sps.permutation_test((x, y), lambda a, b, axis=-1: np.mean(a, axis=axis) - np.mean(b, axis=axis),
                               permutation_type="independent", alternative="two-sided", n_resamples=np.inf,
                               vectorized=True, batch=100_000)
    check(abs(x.mean() - y.mean() - h5["diff"]) < 1e-9, f"H5 isolated - solo: {x.mean() - y.mean():+.6f} vs {h5['diff']:+.6f}")
    check(abs(res.pvalue - h5["p_two_sided"]) < 1e-9, f"H5: p = {res.pvalue:.4f} (scipy, exact) vs {h5['p_two_sided']:.4f}")
    h6 = stored["H6 isolated change from its pre-periods"]
    ch = [o - s for o, s in by["isolated"].values()]
    p6 = _signflip_np(ch)
    check(abs(float(np.mean(ch)) - h6["mean"]) < 1e-9 and abs(p6 - h6["p_two_sided"]) < 1e-9,
          f"H6: change {np.mean(ch):+.6f}, sign-flip p {p6:.4f} (brute force) vs {h6['mean']:+.6f}, {h6['p_two_sided']:.4f}")


def recompute_canary2(src: str, check) -> None:
    """Canary v2 (R2.1): recount every cell from the trial files and judged.json, and redo the registered Fisher
    tests with scipy; compare with round2.json."""
    from scipy import stats as sps

    from .judge import v2_key

    p = RESULTS / src / "round2.json"
    if not p.exists():
        return
    stored = json.loads(p.read_text(encoding="utf-8"))
    judged = json.loads((RESULTS / "judged.json").read_text(encoding="utf-8")) if (RESULTS / "judged.json").exists() else {}
    trials = [t for f in sorted((RESULTS / src).glob("*-s*.json")) for t in json.loads(f.read_text(encoding="utf-8"))["trials"]]
    counts = {}
    for key, cell in stored["cells"].items():
        kind, arm = key.split("|")
        ts = [t for t in trials if t["kind"] == kind and t["arm"] == arm]
        for m in ("written", "exposed", "disclosed_exact"):
            k = sum(bool(t[m]) for t in ts)
            check(k == cell[m]["k"] and len(ts) == cell[m]["n"], f"canary2 {src} {key} {m}: {k}/{len(ts)} vs "
                  f"{cell[m]['k']}/{cell[m]['n']}")
        labels = [judged.get(v2_key(src, t), {}).get("label") for t in ts]
        k = sum(1 for v in labels if v == 1)
        n = sum(1 for v in labels if v is not None)
        check(k == cell["disclosed_judged"]["k"] and n == cell["disclosed_judged"]["n"],
              f"canary2 {src} {key} judged: {k}/{n} vs {cell['disclosed_judged']['k']}/{cell['disclosed_judged']['n']}")
        counts[key] = (k, n)
    for name, t in stored.get("tests (registered, judged disclosure of price plans)", {}).items():
        ax, ay = name.split(" vs ")
        (kx, nx), (ky, ny) = counts[f"price|{ax}"], counts[f"price|{ay}"]
        pv = sps.fisher_exact([[kx, nx - kx], [ky, ny - ky]])[1]
        check(abs(pv - t["p"]) < 1e-9, f"canary2 {src} Fisher {name}: p = {pv:.3g} (scipy) vs {t['p']:.3g}")


if __name__ == "__main__":
    raise SystemExit(main())
