"""Fork test (pre-registered secondary measure). Written during the sprint.

From the state saved after period 25 of a main run, periods 26-35 are played again in two copies:
- placebo: nothing is changed, but every model call is a fresh sample (salt "placebo");
- deviation: in period 26 Firm A's price is forced to its one-shot best response to Firm B's period-26 price in the
  original run. A's plan and message from the original run are kept, so the price is the only change. The copy
  uses the original sample keys, so every call whose input is unchanged (all of period 26) returns the original
  reply; from period 27 on the inputs differ and the replies are new.

Per run, in normalised units (prices as price indices, 0 = Nash, 1 = joint-profit price):
- excess_cut: B's period-27 price in the deviation copy minus B's one-shot best response to A's deviation price.
  Below 0 means B cut by more than a myopic seller would (the pre-registered punishment measure).
- reaction / placebo_reaction: B's period-27 price in the deviation / placebo copy minus the original run.
- net_gain_pct / placebo_gain_pct: A's profit over periods 26-35 in the deviation / placebo copy, minus the original
  run, as a percentage of the original run's A profit over those periods.
A high price sustained by reward and punishment (Harrington 2018) predicts excess_cut < 0 and net_gain_pct < 0.
"""
from __future__ import annotations

from typing import Callable

from .game import Game, RunConfig, State
from .market import Market

START, HORIZON = 26, 10  # the snapshot is the state after period 25


def _cfg(result: dict) -> RunConfig:
    return RunConfig(**result["config"])


def _index(result: dict, p_dollars: float) -> float:
    b, a = result["benchmarks"], result["alpha"]
    return (p_dollars / a - b["p_nash"]) / (b["p_mono"] - b["p_nash"])


def _gap(result: dict, dp_dollars: float) -> float:
    """A price difference in dollars expressed in price-index units."""
    b, a = result["benchmarks"], result["alpha"]
    return dp_dollars / a / (b["p_mono"] - b["p_nash"])


def fork_run(result: dict, make_agents: Callable[[RunConfig], tuple[list, object]], horizon: int = HORIZON) -> dict:
    """make_agents(cfg) -> (sellers, advisor or None): fresh policies for one copy (LLM or scripted)."""
    cfg = _cfg(result)
    if result.get("snapshot") is None or cfg.snapshot_at != START - 1:
        raise ValueError(f"{cfg.run_id}: no snapshot after period {START - 1}")
    if len(result["log"]) < START - 1 + horizon:
        raise ValueError(f"{cfg.run_id}: the original run is shorter than period {START - 1 + horizon}")
    m = Market(n=cfg.n, alpha=result["alpha"])
    orig = result["log"][START - 1: START - 1 + horizon]  # periods 26 .. 25 + horizon
    pB26 = orig[0]["prices"][1]
    dev_price = m.best_response_dollars([pB26])
    a26 = orig[0]["sellers"][0]
    forced_text = {0: (a26.get("plan", ""), a26.get("message", ""))}

    def copy_game() -> Game:
        sellers, advisor = make_agents(cfg)
        return Game(cfg, sellers, advisor, state=State.from_dict(result["snapshot"]))

    dev = copy_game()
    dev.step(forced={0: dev_price}, salt="", forced_text=forced_text)
    for _ in range(horizon - 1):
        dev.step(salt="")
    plc = copy_game()
    plc.run(horizon, salt="placebo")

    def series(log, firm, key):
        return [r[key][firm] for r in log]

    profit_o = sum(series(orig, 0, "profits"))
    profit_d = sum(series(dev.log, 0, "profits"))
    profit_p = sum(series(plc.log, 0, "profits"))
    pB27_d, pB27_o, pB27_p = dev.log[1]["prices"][1], orig[1]["prices"][1], plc.log[1]["prices"][1]
    br_B = m.best_response_dollars([dev_price])
    return {
        "run_id": cfg.run_id, "condition": cfg.condition, "seed": cfg.seed, "start": START, "horizon": horizon,
        "dev_price": dev_price, "dev_size": _gap(result, orig[0]["prices"][0] - dev_price),
        "excess_cut": _gap(result, pB27_d - br_B),
        "reaction": _gap(result, pB27_d - pB27_o),
        "placebo_reaction": _gap(result, pB27_p - pB27_o),
        "net_gain_pct": 100.0 * (profit_d - profit_o) / profit_o if profit_o else None,
        "placebo_gain_pct": 100.0 * (profit_p - profit_o) / profit_o if profit_o else None,
        "index": {"original": [sum(_index(result, p) for p in r["prices"]) / cfg.n for r in orig],
                  "deviation": [sum(_index(result, p) for p in r["prices"]) / cfg.n for r in dev.log],
                  "placebo": [sum(_index(result, p) for p in r["prices"]) / cfg.n for r in plc.log]},
        "logs": {"deviation": dev.log, "placebo": plc.log},
    }
