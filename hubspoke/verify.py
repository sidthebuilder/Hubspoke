"""verify: rebuild every result from the cached model replies, then recompute the headline numbers independently.
Written during the sprint.

1. Replay. Every main run is played again with HUBSPOKE_OFFLINE=1: every model call must be answered from the
   cache (a cache miss is an error), and the replayed prices must equal the stored ones. The fork, replay and
   canary measures are recomputed the same way. This shows the stored run files follow from the raw replies.
2. Recompute. The outcome of every run is recomputed from raw posted prices with numpy and freshly computed
   benchmarks, and the H1-H4 p-values with scipy's exact permutation test. Both are compared with numbers.json.
Writes results/verify.txt; exits 1 if anything differs.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"
TOL = 1e-9


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
    conf = "modal_llama70b.json" if src.endswith("_llama") else "modal_qwen72b.json"  # the model the runs used
    cfg, spec = load_config(str(ROOT / "configs" / conf))
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
                     ("canary", lambda res: {"trials": canary.canary_trials(res, LLMAdvisor(client, res["config"]["temperature"]))}))
    for kind, fn in secondary:
        for p in sorted((RESULTS / kind).glob("*-s*.json")) if (RESULTS / kind).exists() else []:
            stored = json.loads(p.read_text(encoding="utf-8"))
            try:
                again = fn(runs[p.stem])
                keys = {"forks": ["excess_cut", "net_gain_pct", "placebo_gain_pct", "reaction"],
                        "replay": ["data_effect", "memo_effect", "abs_noise"]}.get(kind)
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
    else:
        lines.append(f"note: {nfile} not found; run `python -m hubspoke analyse --src {src}` first")

    lines.append(f"\n{bad} failure(s); client stats {client.stats}")
    (RESULTS / f"verify_{src}.txt").write_text("\n".join(lines), encoding="utf-8")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
