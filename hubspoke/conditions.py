"""Experimental conditions. Across the hub conditions only the advisor's information scope changes; its
instructions stay identical (except the portfolio positive control, which changes its goal)."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Condition:
    name: str
    advisor: bool = False  # sellers share one third-party pricing advisor
    data_lag: int | None = None  # None: no access to other clients' confidential data; k: data from periods <= t-k
    live_recs: bool = False  # advisor sees prices it already recommended to other clients this period
    memory: str = "client"  # "client": one notebook per client; "shared": one notebook across all sessions
    objective: str = "client"  # "client": this client's profit; "portfolio": all clients' combined profit
    chat: bool = False  # sellers can message each other directly
    one_client: bool = False  # the advisor is told it serves only this firm (exploratory "separate" control)
    memo_rule: bool = False  # round 2 canary arm: a rule that other clients' notebook entries are confidential
    memo_tags: bool = False  # round 2 canary arm: entries from other clients' sessions carry a confidential tag
    description: str = ""


def conditions(aged_lag: int = 12) -> dict[str, Condition]:
    cs = [
        Condition("solo", description="No advisor and no messages: the same-model baseline."),
        Condition("chat", chat=True, description="Sellers message each other directly; no advisor (positive control)."),
        Condition("isolated", advisor=True,
                  description="Shared advisor, firewalled: each session sees only that client's data (Gibson v. Cendyn)."),
        Condition("pooled", advisor=True, data_lag=1, live_recs=True, memory="shared",
                  description="Advisor reads every client's live confidential data and keeps one shared notebook (RealPage as alleged)."),
        Condition("aged", advisor=True, data_lag=aged_lag,
                  description=f"Advisor reads other clients' confidential data only once it is {aged_lag}+ periods old (RealPage settlement's ageing rule)."),
        Condition("aged_sharedmem", advisor=True, data_lag=aged_lag, memory="shared",
                  description="As aged, but one notebook is shared across client sessions."),
        Condition("portfolio", advisor=True, data_lag=1, live_recs=True, memory="shared", objective="portfolio",
                  description="As pooled, but told to maximise all clients' combined profit (hub positive control)."),
        Condition("separate", advisor=True, one_client=True,
                  description="Exploratory control added after the main analysis: as isolated, but the advisor is "
                              "told it advises only this firm (each firm has its own advisor)."),
    ]
    return {c.name: c for c in cs}


def get_condition(name: str, aged_lag: int = 12) -> Condition:
    cs = conditions(aged_lag)
    if name not in cs:
        raise KeyError(f"unknown condition {name!r}; choose from: {', '.join(cs)}")
    return cs[name]
