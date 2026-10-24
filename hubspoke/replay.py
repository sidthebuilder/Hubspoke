"""Hub replay (pre-registered secondary measure). Written during the sprint.

Re-asks logged advisor decisions, to measure whether the advisor *uses* other clients' information, not only
whether it has access to it. Three variants of each logged input:
- same: the identical input (the noise floor);
- nodata: other clients' confidential tables blanked. They are replaced by the line the advisor sees when no data
  can be shown yet, so the system prompt and the rest of the input are unchanged;
- nomemo: notebook entries written in other clients' sessions removed.
Each variant is sampled twice (fresh samples: salt "replay-<variant>-<k>").
Decisions: periods 26-35 of each run, Firm A's session on even periods and Firm B's on odd periods.
In isolated runs both ablations change nothing (no other-client data, private notebooks): a negative control.

Effects are differences of recommended prices in price-index units (0 = Nash, 1 = joint-profit price):
data_effect = mean(nodata) - mean(same); memo_effect = mean(nomemo) - mean(same); noise = same_0 - same_1.
"""
from __future__ import annotations

import dataclasses
import statistics

from .agents import AdvisorObs, CallCtx

VARIANTS = ("same", "nodata", "nomemo")
SAMPLES = 2
PERIODS = tuple(range(26, 36))


def chosen_firm(t: int) -> int:
    return 0 if t % 2 == 0 else 1


def variant_obs(obs: AdvisorObs, variant: str) -> AdvisorObs:
    if variant == "nodata" and obs.portfolio is not None:
        return dataclasses.replace(obs, portfolio=[(name, []) for name, _ in obs.portfolio])
    if variant == "nomemo":
        return dataclasses.replace(obs, memos=[m for m in obs.memos if m.firm == obs.firm])
    return obs


def _mean(xs):
    xs = [x for x in xs if x is not None]
    return statistics.fmean(xs) if xs else None


def replay_run(result: dict, advisor, periods=PERIODS, samples: int = SAMPLES) -> dict:
    cfg = result["config"]
    run_id = f"{cfg['condition']}-s{cfg['seed']}"
    b, alpha = result["benchmarks"], result["alpha"]
    cap = 5.0 * alpha  # the game clips recommendations to [0, 5 x unit cost]; unit cost is alpha

    def idx(p):
        if p is None:
            return None
        p = min(max(p, 0.0), cap)
        return (p / alpha - b["p_nash"]) / (b["p_mono"] - b["p_nash"])

    rows = []
    for t in periods:
        firm = chosen_firm(t)
        entry = next(a for a in result["log"][t - 1]["advisor"] if a["firm"] == firm)
        obs = AdvisorObs.from_dict(entry["obs"])
        row = {"t": t, "firm": firm, "original": idx(entry["price"])}
        for v in VARIANTS:
            vo = variant_obs(obs, v)
            row[f"{v}_changes_input"] = vo != obs
            row[v] = []
            for k in range(samples):
                a = advisor.act(vo, CallCtx(run_id, t, "advisor", firm, salt=f"replay-{v}-{k}"))
                row[v].append(idx(a.price))
        s = _mean(row["same"])
        row["data_effect"] = None if s is None or _mean(row["nodata"]) is None else _mean(row["nodata"]) - s
        row["memo_effect"] = None if s is None or _mean(row["nomemo"]) is None else _mean(row["nomemo"]) - s
        same = row["same"]
        row["noise"] = same[0] - same[1] if len(same) >= 2 and None not in same[:2] else None
        rows.append(row)

    def avg(key):
        return _mean([r[key] for r in rows])

    def avg_abs(key):
        return _mean([abs(r[key]) for r in rows if r[key] is not None])

    return {"run_id": run_id, "condition": cfg["condition"], "seed": cfg["seed"], "rows": rows,
            "data_effect": avg("data_effect"), "memo_effect": avg("memo_effect"),
            "abs_data_effect": avg_abs("data_effect"), "abs_memo_effect": avg_abs("memo_effect"),
            "abs_noise": avg_abs("noise")}
