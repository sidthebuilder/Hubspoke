"""One repeated pricing market: sellers, an optional shared advisor, and a full call log."""
from __future__ import annotations

import copy
import random
from dataclasses import asdict, dataclass, field

from .agents import AdvisorObs, CallCtx, Memo, Row, SellerObs
from .conditions import Condition, get_condition
from .market import Market
from .prompts import firm_name

ALPHAS = (1.0, 3.2, 10.0)  # currency scale per seed, so benchmark prices cannot be recalled from memory


@dataclass
class RunConfig:
    condition: str
    seed: int
    T: int = 40
    window: int = 20  # periods of history each agent sees
    memo_window: int = 10  # notebook entries the advisor sees
    temperature: float = 0.7
    n: int = 2
    aged_lag: int = 12
    snapshot_at: int = 25  # state saved here for the fork test

    @property
    def run_id(self) -> str:
        return f"{self.condition}-s{self.seed}"


@dataclass
class State:
    t: int = 0
    rows: list[list[Row]] = field(default_factory=list)
    plans: list[str] = field(default_factory=list)
    memos: list[Memo] = field(default_factory=list)
    inbox: list[list[tuple[str, str]]] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)

    @staticmethod
    def from_dict(d: dict) -> "State":
        return State(t=d["t"], rows=[[Row(**r) for r in rs] for rs in d["rows"]], plans=list(d["plans"]),
                     memos=[Memo(**m) for m in d["memos"]], inbox=[[tuple(x) for x in ib] for ib in d["inbox"]])


class Game:
    def __init__(self, cfg: RunConfig, sellers: list, advisor=None, state: State | None = None):
        self.cfg = cfg
        self.cond: Condition = get_condition(cfg.condition, cfg.aged_lag)
        self.market = Market(n=cfg.n, alpha=ALPHAS[cfg.seed % len(ALPHAS)])
        self.sellers, self.advisor = sellers, advisor
        if self.cond.advisor and advisor is None:
            raise ValueError(f"condition {cfg.condition} needs an advisor")
        n = cfg.n
        self.names = [firm_name(i) for i in range(n)]
        self.state = state or State(rows=[[] for _ in range(n)], plans=[""] * n, inbox=[[] for _ in range(n)])
        self.log: list[dict] = []
        self.snapshot: dict | None = None

    # ---------------------------------------------------------------- one period
    def _advisor_obs(self, i: int, t: int, live: list[tuple[str, float]]) -> AdvisorObs:
        s, c, W = self.state, self.cond, self.cfg.window
        portfolio = None
        if c.data_lag is not None:
            portfolio = [(self.names[j], [r for r in s.rows[j] if r.t <= t - c.data_lag][-W:])
                         for j in range(self.cfg.n) if j != i]
        memos = s.memos if c.memory == "shared" else [m for m in s.memos if m.firm == self.names[i]]
        return AdvisorObs(firm=self.names[i], index=i, t=t, n=self.cfg.n, cost=self.market.unit_cost,
                          history=s.rows[i][-W:], rival_names=[x for j, x in enumerate(self.names) if j != i],
                          condition=c, portfolio=portfolio, live_recs=list(live) if c.live_recs else None,
                          memos=list(memos[-self.cfg.memo_window:]))

    def step(self, forced: dict[int, float] | None = None, salt: str = "") -> dict:
        s, m, n, cap = self.state, self.market, self.cfg.n, self.market.price_cap
        t = s.t + 1
        rid = self.cfg.run_id
        recs: list[float | None] = [None] * n
        notes = [""] * n
        adv_log = []
        if self.cond.advisor:
            order = list(range(n))
            random.Random(f"{rid}|{t}").shuffle(order)  # depends only on run and period, so forks match
            live: list[tuple[str, float]] = []
            for i in order:
                obs = self._advisor_obs(i, t, live)
                a = self.advisor.act(obs, CallCtx(rid, t, "advisor", i, salt))
                p = None if a.price is None else min(max(a.price, 0.0), cap)
                recs[i], notes[i] = p, a.note
                if a.memo:
                    s.memos.append(Memo(t, self.names[i], a.memo))
                if p is not None:
                    live.append((self.names[i], p))
                adv_log.append({"firm": i, "obs": obs.to_dict(), "price": a.price, "note": a.note, "memo": a.memo,
                                "ok": a.ok, "trace": a.trace})

        prices, plans, msgs, sel_log = [0.0] * n, list(s.plans), [""] * n, []
        for i in range(n):
            if forced and i in forced:
                p, ok, a = forced[i], True, None
            else:
                obs = SellerObs(firm=self.names[i], index=i, t=t, n=n, cost=m.unit_cost,
                                history=s.rows[i][-self.cfg.window:],
                                rival_names=[x for j, x in enumerate(self.names) if j != i], plan=s.plans[i],
                                advisor=self.cond.advisor, rec=recs[i], rec_note=notes[i], chat=self.cond.chat,
                                inbox=list(s.inbox[i]))
                a = self.sellers[i].act(obs, CallCtx(rid, t, "seller", i, salt))
                p, ok = a.price, a.ok
                plans[i], msgs[i] = a.plan or s.plans[i], a.message
            if p is None:  # unreadable reply: keep the last price (or Nash in period 1)
                p = s.rows[i][-1].price if s.rows[i] else m.alpha * m.nash_price()
            prices[i] = min(max(float(p), 0.0), cap)
            sel_log.append({"firm": i, "price": None if a is None else a.price, "ok": ok, "forced": a is None,
                            "plan": plans[i], "message": msgs[i], "trace": [] if a is None else a.trace})
        q, pi = m.clear(prices)
        for i in range(n):
            s.rows[i].append(Row(t, round(prices[i], 4), round(float(q[i]), 3), round(float(pi[i]), 4),
                                 [round(prices[j], 4) for j in range(n) if j != i]))
        s.plans = plans
        s.inbox = [[(self.names[j], msgs[j]) for j in range(n) if j != i and msgs[j]] for i in range(n)]
        s.t = t
        rec = {"t": t, "prices": prices, "units": [float(x) for x in q], "profits": [float(x) for x in pi],
               "recs": recs, "advisor": adv_log, "sellers": sel_log, "forced": forced or {}, "salt": salt}
        self.log.append(rec)
        if t == self.cfg.snapshot_at:
            self.snapshot = copy.deepcopy(s.to_dict())
        return rec

    def run(self, T: int | None = None, salt: str = "") -> None:
        for _ in range(T or self.cfg.T):
            self.step(salt=salt)

    # ---------------------------------------------------------------- outcomes
    def price_index(self) -> list[float]:
        b = self.market.benchmarks()
        return [sum(b.price_index(p / self.market.alpha) for p in r["prices"]) / self.cfg.n for r in self.log]

    def result(self) -> dict:
        b = self.market.benchmarks()
        return {"config": asdict(self.cfg), "alpha": self.market.alpha,
                "benchmarks": {"p_nash": b.p_nash, "p_mono": b.p_mono, "pi_nash": b.pi_nash, "pi_mono": b.pi_mono},
                "price_index": self.price_index(), "snapshot": self.snapshot, "final_state": self.state.to_dict(),
                "log": self.log}
