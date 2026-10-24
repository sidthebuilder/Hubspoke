"""What each agent observes and decides, and the LLM-backed policies."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Protocol

from . import prompts
from .conditions import Condition
from .parsing import clip_text, parse_reply, to_price


@dataclass
class Row:
    """One period of one firm's record. rival_prices are the other firms' posted (public) prices."""

    t: int
    price: float
    units: float
    profit: float
    rival_prices: list[float] = field(default_factory=list)


@dataclass
class Memo:
    """A note the advisor wrote to its notebook during a session with `firm`."""

    t: int
    firm: str
    text: str


@dataclass
class SellerObs:
    firm: str
    index: int
    t: int
    n: int
    cost: float
    history: list[Row]
    rival_names: list[str]
    plan: str = ""
    advisor: bool = False
    rec: float | None = None
    rec_note: str = ""
    chat: bool = False
    inbox: list[tuple[str, str]] = field(default_factory=list)
    think: bool = False  # the reply starts with a short "reasoning" field


@dataclass
class AdvisorObs:
    firm: str
    index: int
    t: int
    n: int
    cost: float
    history: list[Row]
    rival_names: list[str]
    condition: Condition
    portfolio: list[tuple[str, list[Row]]] | None = None  # other clients' confidential rows; None = no access
    live_recs: list[tuple[str, float]] | None = None  # prices already recommended to others this period
    memos: list[Memo] = field(default_factory=list)
    extra: str = ""  # only used by the canary test (a confidential note from this client)
    think: bool = False  # the reply starts with a short "reasoning" field

    def to_dict(self) -> dict:
        return asdict(self)

    @staticmethod
    def from_dict(d: dict) -> "AdvisorObs":
        def rows(xs):
            return [Row(**r) for r in xs]

        return AdvisorObs(
            firm=d["firm"], index=d["index"], t=d["t"], n=d["n"], cost=d["cost"], history=rows(d["history"]),
            rival_names=list(d["rival_names"]), condition=Condition(**d["condition"]),
            portfolio=None if d.get("portfolio") is None else [(name, rows(rs)) for name, rs in d["portfolio"]],
            live_recs=None if d.get("live_recs") is None else [(name, float(p)) for name, p in d["live_recs"]],
            memos=[Memo(**m) for m in d.get("memos", [])],
            extra=d.get("extra", ""),
            think=d.get("think", False),
        )


@dataclass
class SellerAction:
    price: float | None
    plan: str = ""
    message: str = ""
    ok: bool = True
    trace: list[dict] = field(default_factory=list)
    reasoning: str = ""


@dataclass
class AdvisorAction:
    price: float | None
    note: str = ""
    memo: str = ""
    ok: bool = True
    trace: list[dict] = field(default_factory=list)
    reasoning: str = ""  # private to the advisor: never shown to any client


@dataclass(frozen=True)
class CallCtx:
    """Identifies one model call. Forks keep run and period, so identical inputs reuse cached replies; a salt
    (placebo, replay) forces a fresh sample of the same input."""

    run: str
    t: int
    role: str
    firm: int
    salt: str = ""

    def sample_key(self, attempt: int = 0) -> str:
        return f"{self.run}|{self.role}|{self.firm}|{self.t}|{self.salt}|{attempt}"


class Policy(Protocol):
    def act(self, obs, ctx: CallCtx): ...


def _ask(client, system: str, user: str, ctx: CallCtx, temperature: float, max_tokens: int):
    """One call plus at most one repair retry. Returns (parsed dict or None, trace)."""
    msgs = [{"role": "system", "content": system}, {"role": "user", "content": user}]
    trace = []
    for attempt in (0, 1):
        c = client.complete(msgs, temperature=temperature, max_tokens=max_tokens, sample_key=ctx.sample_key(attempt))
        trace.append({"attempt": attempt, "cached": c.cached, "text": c.text})
        d = parse_reply(c.text)
        if d is not None and to_price(d.get("price")) is not None:
            return d, trace
        msgs = msgs + [{"role": "assistant", "content": c.text}, {"role": "user", "content": prompts.REPAIR}]
    return None, trace


class LLMSeller:
    def __init__(self, client, temperature: float = 0.7, max_tokens: int = 360):
        self.client, self.temperature, self.max_tokens = client, temperature, max_tokens

    def act(self, obs: SellerObs, ctx: CallCtx) -> SellerAction:
        d, trace = _ask(self.client, prompts.seller_system(obs), prompts.seller_user(obs), ctx,
                        self.temperature, self.max_tokens)
        if d is None:
            return SellerAction(None, ok=False, trace=trace)
        return SellerAction(to_price(d.get("price")), clip_text(d.get("plan")),
                            clip_text(d.get("message")) if obs.chat else "", True, trace,
                            clip_text(d.get("reasoning"), 600))


class LLMAdvisor:
    def __init__(self, client, temperature: float = 0.7, max_tokens: int = 420):
        self.client, self.temperature, self.max_tokens = client, temperature, max_tokens

    def act(self, obs: AdvisorObs, ctx: CallCtx) -> AdvisorAction:
        d, trace = _ask(self.client, prompts.advisor_system(obs), prompts.advisor_user(obs), ctx,
                        self.temperature, self.max_tokens)
        if d is None:
            return AdvisorAction(None, ok=False, trace=trace)
        return AdvisorAction(to_price(d.get("price")), clip_text(d.get("note")), clip_text(d.get("memo")), True, trace,
                             clip_text(d.get("reasoning"), 600))
