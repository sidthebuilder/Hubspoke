"""Logit-demand Bertrand market of Calvano et al. (2020), the environment Fish et al. (2024) used for LLM
pricing agents.

Methods work in normalised units unless they say "dollars". Agents only see dollars: a normalised price p is
shown as alpha * p and a normalised profit as alpha * profit. Drawing alpha per run, as Fish et al. do, stops a
model from matching benchmark prices it may have memorised.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Callable, Sequence

import numpy as np


def _bisect(g: Callable[[float], float], lo: float, hi: float, iters: int = 200) -> float:
    """Root of an increasing function g on [lo, hi]."""
    if g(lo) > 0 or g(hi) < 0:
        raise ValueError("root is not bracketed")
    for _ in range(iters):
        mid = 0.5 * (lo + hi)
        if g(mid) < 0:
            lo = mid
        else:
            hi = mid
    return 0.5 * (lo + hi)


@dataclass(frozen=True)
class Benchmarks:
    """One-shot benchmarks of a symmetric market: normalised prices, per-firm profits."""

    p_nash: float
    p_mono: float
    pi_nash: float
    pi_mono: float

    def price_index(self, p: float) -> float:
        """0 at the one-shot Nash price, 1 at the joint-profit-maximising price."""
        return (p - self.p_nash) / (self.p_mono - self.p_nash)

    def profit_index(self, pi: float) -> float:
        """Calvano et al.'s Delta: 0 at Nash profit, 1 at joint-profit-maximising profit (per firm)."""
        return (pi - self.pi_nash) / (self.pi_mono - self.pi_nash)


@dataclass(frozen=True)
class Market:
    n: int = 2  # sellers
    a: float = 2.0  # product quality (identical products)
    a0: float = 0.0  # outside option
    mu: float = 0.25  # horizontal differentiation
    c: float = 1.0  # marginal cost
    beta: float = 100.0  # market size: units = beta * share
    alpha: float = 1.0  # currency scale shown to agents

    def shares(self, p: Sequence[float]) -> np.ndarray:
        z = (self.a - np.asarray(p, dtype=float)) / self.mu
        z0 = self.a0 / self.mu
        top = max(float(z.max()), z0)  # subtract the max before exp, for stability
        e = np.exp(z - top)
        return e / (e.sum() + math.exp(z0 - top))

    def quantities(self, p: Sequence[float]) -> np.ndarray:
        return self.beta * self.shares(p)

    def profits(self, p: Sequence[float]) -> np.ndarray:
        return (np.asarray(p, dtype=float) - self.c) * self.quantities(p)

    def _hi(self) -> float:
        return self.c + 50 * self.mu + 10

    def best_response(self, others: Sequence[float]) -> float:
        """One-shot best response of one firm to the other firms' normalised prices."""
        others = [float(x) for x in others]

        def foc(x: float) -> float:
            return x - self.c - self.mu / (1.0 - self.shares([x, *others])[0])

        return _bisect(foc, self.c, self._hi())

    def nash_price(self) -> float:
        def foc(x: float) -> float:
            return x - self.c - self.mu / (1.0 - self.shares([x] * self.n)[0])

        return _bisect(foc, self.c, self._hi())

    def monopoly_price(self) -> float:
        """Symmetric price that maximises the sellers' joint profit."""

        def foc(x: float) -> float:
            return x - self.c - self.mu / (1.0 - self.n * self.shares([x] * self.n)[0])

        return _bisect(foc, self.c, self._hi())

    def benchmarks(self) -> Benchmarks:
        pn, pm = self.nash_price(), self.monopoly_price()
        return Benchmarks(pn, pm, float(self.profits([pn] * self.n)[0]), float(self.profits([pm] * self.n)[0]))

    # ---- dollars: what agents see ----------------------------------------------------------------------
    @property
    def unit_cost(self) -> float:
        return self.alpha * self.c

    @property
    def price_cap(self) -> float:
        """Posted prices are clipped to [0, cap]; demand at the cap is negligible."""
        return 5.0 * self.alpha * self.c

    def clear(self, prices: Sequence[float]) -> tuple[np.ndarray, np.ndarray]:
        """Units sold and dollar profits at posted dollar prices."""
        p = np.asarray(prices, dtype=float) / self.alpha
        q = self.quantities(p)
        return q, self.alpha * (p - self.c) * q

    def best_response_dollars(self, others: Sequence[float]) -> float:
        return self.alpha * self.best_response([x / self.alpha for x in others])
