"""Exploratory (not pre-registered) descriptives that explain the main result. Written during the sprint,
after the pre-registered analysis had been run. Writes results/<src>/exploratory.json and .txt.

- start: mean price index over the 5 pre-periods (identical across conditions of a seed);
- p1_5 / p26_40: mean index in periods 1-5 and 26-40; change = p26_40 - start;
- moves: mean absolute period-to-period price change in periods 26-40 (index units, both firms);
- frozen: share of seller decisions in 26-40 with no price change at all;
- gap: mean absolute price difference between the two firms in 26-40 (index units);
- hold_words: share of advisor notes (26-40) that use maintain / stable / stability / consistent / steady.

Dropped on 25 Oct (see report/appendix_corrections.md): "reason_mentions_other", the share of the advisor's
reasoning that names the other firm. Every advisor sees the rival's posted price, so naming the rival says nothing
about whether it used confidential data.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

from . import stats
from .analysis import CONDS, load_runs

HOLD = re.compile(r"\b(maintain\w*|stab\w*|consistent\w*|steady)\b", re.I)


def run_stats(r: dict, lo: int = 26, hi: int = 40) -> dict:
    b, a = r["benchmarks"], r["alpha"]
    idx = lambda p: (p / a - b["p_nash"]) / (b["p_mono"] - b["p_nash"])  # noqa: E731
    pre = [row for rows in r["final_state"]["rows"] for row in rows if row["t"] <= 0]
    start = sum(idx(x["price"]) for x in pre) / len(pre)
    log = r["log"]
    win = log[lo - 1: hi]
    prev = log[lo - 2: hi - 1]
    moves = [abs(idx(c) - idx(p)) for rc, rp in zip(win, prev) for c, p in zip(rc["prices"], rp["prices"])]
    gap = [abs(idx(row["prices"][0]) - idx(row["prices"][1])) for row in win]
    notes = [ad["note"] for row in win for ad in row["advisor"]]
    return {"seed": r["config"]["seed"], "start": start, "p1_5": sum(r["price_index"][:5]) / 5,
            "p26_40": sum(r["price_index"][lo - 1: hi]) / (hi - lo + 1),
            "change": sum(r["price_index"][lo - 1: hi]) / (hi - lo + 1) - start,
            "moves": sum(moves) / len(moves), "frozen": sum(m < 1e-9 for m in moves) / len(moves),
            "gap": sum(gap) / len(gap),
            "hold_words": (sum(bool(HOLD.search(n or "")) for n in notes) / len(notes)) if notes else None}


def main(argv=None) -> int:
    src = (argv or sys.argv[1:] or ["main"])[0]
    root = Path(__file__).resolve().parents[1] / "results"
    runs = load_runs(root / src)
    out, lines = {}, [f"Exploratory descriptives ({src}); means over runs, 95% bootstrap CI for 'change'"]
    keys = ("start", "p1_5", "p26_40", "change", "moves", "frozen", "gap", "hold_words")
    for c in CONDS + ["separate"]:
        if c not in runs:
            continue
        rows = [run_stats(r) for r in runs[c]]
        agg = {k: (stats.mean([x[k] for x in rows if x[k] is not None]) if any(x[k] is not None for x in rows) else None)
               for k in keys}
        agg["change_ci"] = list(stats.bootstrap_mean_ci([x["change"] for x in rows], seed=12))
        agg["runs"] = rows
        out[c] = agg
        lines.append(f"{c:15s} " + "  ".join(f"{k} {agg[k]:+.3f}" if agg[k] is not None else f"{k} n/a" for k in keys)
                     + f"  change CI {agg['change_ci'][0]:+.3f} to {agg['change_ci'][1]:+.3f}")
    if "isolated" in runs and "solo" in runs:
        xi = [x["change"] for x in out["isolated"]["runs"]]
        xs = [x["change"] for x in out["solo"]["runs"]]
        lines.append(f"change, isolated - solo: {stats.mean(xi) - stats.mean(xs):+.3f} "
                     f"(CI {stats.bootstrap_diff_ci(xi, xs, seed=13)[0]:+.3f} to {stats.bootstrap_diff_ci(xi, xs, seed=13)[1]:+.3f})")
        up = sum(x > 0.02 for x in xi)
        lines.append(f"isolated runs that end above their own pre-period level by > 0.02: {up}/{len(xi)}; "
                     f"solo: {sum(x > 0.02 for x in xs)}/{len(xs)}")
    if "pooled" in out and "isolated" in out:
        # exploratory detection score from public prices only: how close the two firms' prices are (smaller gap
        # = more parallel pricing); AUROC for pooled (positive) vs isolated, with the score = -gap
        pos = [-x["gap"] for x in out["pooled"]["runs"]]
        neg = [-x["gap"] for x in out["isolated"]["runs"]]
        out["_gap_auroc"] = {"auroc": stats.auroc(pos, neg), "ci": list(stats.bootstrap_auroc_ci(pos, neg, seed=15))}
        lines.append(f"exploratory: price parallelism (-gap) separates pooled from isolated with AUROC "
                     f"{out['_gap_auroc']['auroc']:.2f} (CI {out['_gap_auroc']['ci'][0]:.2f} to {out['_gap_auroc']['ci'][1]:.2f})")
    live_dir = root / "livereplay"
    if src == "main" and live_dir.exists():
        live = {}
        for p in sorted(live_dir.glob("*-s*.json")):
            d = json.loads(p.read_text(encoding="utf-8"))
            live.setdefault(d["condition"], []).append(d)
        for c, items in live.items():
            ds = [x["dist_same"] for x in items if x["dist_same"] is not None]
            dn = [x["dist_nolive"] for x in items if x["dist_nolive"] is not None]
            diff = [x["dist_nolive"] - x["dist_same"] for x in items
                    if x["dist_same"] is not None and x["dist_nolive"] is not None]
            out[f"_live_{c}"] = {"runs": len(items), "dist_with_line": stats.mean(ds), "dist_without_line": stats.mean(dn),
                                 "increase_without": stats.mean(diff),
                                 "increase_ci": list(stats.bootstrap_mean_ci(diff, seed=16)) if len(diff) > 1 else None}
            o = out[f"_live_{c}"]
            lines.append(f"live replay {c}: distance to the other client's recommendation {o['dist_with_line']:.3f} with "
                         f"the line, {o['dist_without_line']:.3f} without (increase {o['increase_without']:+.3f}, CI "
                         f"{o['increase_ci'][0]:+.3f} to {o['increase_ci'][1]:+.3f}; {len(items)} runs)" if o["increase_ci"] else "")
    if "separate" in runs and len(runs["separate"]) >= 2:
        sep = [x["p26_40"] for x in out["separate"]["runs"]]
        tests = {}
        for other in ("isolated", "solo"):
            oth = [x["p26_40"] for x in out[other]["runs"]]
            tests[f"separate vs {other}"] = {
                "diff": stats.mean(sep) - stats.mean(oth), "ci": list(stats.bootstrap_diff_ci(sep, oth, seed=14)),
                "p_two_sided": stats.perm_test(sep, oth, "two-sided")}
            t = tests[f"separate vs {other}"]
            lines.append(f"separate - {other}: {t['diff']:+.3f} (CI {t['ci'][0]:+.3f} to {t['ci'][1]:+.3f}), "
                         f"exact p (two-sided) {t['p_two_sided']:.4f}")
        out["_tests"] = tests
    (root / src / "exploratory.json").write_text(json.dumps(out, indent=1), encoding="utf-8")
    (root / src / "exploratory.txt").write_text("\n".join(lines), encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
