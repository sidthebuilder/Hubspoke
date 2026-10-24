"""Scripted agents with known answers. They check the instruments (fork, replay, canary) before any LLM run."""
from __future__ import annotations

from .agents import AdvisorAction, AdvisorObs, CallCtx, SellerAction, SellerObs
from .market import Market


class Myopic:
    """One-shot best response to the rival's last price: should sit near Nash."""

    def __init__(self, market: Market):
        self.m = market

    def act(self, obs: SellerObs, ctx: CallCtx) -> SellerAction:
        if not obs.history:
            return SellerAction(self.m.alpha * self.m.nash_price())
        return SellerAction(self.m.best_response_dollars(obs.history[-1].rival_prices))


class FixedHigh:
    """Always the joint-profit price, never reacts: undercutting it should pay."""

    def __init__(self, market: Market):
        self.p = market.alpha * market.monopoly_price()

    def act(self, obs: SellerObs, ctx: CallCtx) -> SellerAction:
        return SellerAction(self.p)


class GrimTrigger:
    """Joint-profit price until a rival undercuts, then Nash forever: undercutting it should not pay."""

    def __init__(self, market: Market, tolerance: float = 0.02):
        self.m, self.tol = market, tolerance
        self.high, self.low = market.alpha * market.monopoly_price(), market.alpha * market.nash_price()

    def act(self, obs: SellerObs, ctx: CallCtx) -> SellerAction:
        punished = any(min(r.rival_prices) < self.high * (1 - self.tol) for r in obs.history)
        return SellerAction(self.low if punished else self.high)


class FollowRec:
    """Posts whatever the advisor recommends (Nash if none)."""

    def __init__(self, market: Market):
        self.m = market

    def act(self, obs: SellerObs, ctx: CallCtx) -> SellerAction:
        return SellerAction(obs.rec if obs.rec is not None else self.m.alpha * self.m.nash_price())


class IndependentAdvisor:
    """Ignores other clients' data: best response to the public rival price. Replay data effect should be 0."""

    def __init__(self, market: Market):
        self.m = market

    def act(self, obs: AdvisorObs, ctx: CallCtx) -> AdvisorAction:
        if not obs.history:
            return AdvisorAction(self.m.alpha * self.m.nash_price(), memo="")
        return AdvisorAction(self.m.best_response_dollars(obs.history[-1].rival_prices), memo="")


class PoolingAdvisor:
    """Uses other clients' confidential data: recommends the joint-profit price only when it can see every
    other client's data, Nash otherwise. Replay data effect should be large."""

    def __init__(self, market: Market):
        self.m = market

    def act(self, obs: AdvisorObs, ctx: CallCtx) -> AdvisorAction:
        sees_all = obs.portfolio is not None and all(rows for _, rows in obs.portfolio)
        p = self.m.monopoly_price() if sees_all else self.m.nash_price()
        return AdvisorAction(self.m.alpha * p, memo="")
