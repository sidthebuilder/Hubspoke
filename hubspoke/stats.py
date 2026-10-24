"""Statistics for small samples of run-level outcomes. Written during the sprint.

Everything is exact or resampling-based with a fixed seed, so every number can be recomputed by verify.py.
"""
from __future__ import annotations

import itertools
import math
import random
import statistics
from typing import Sequence


def mean(xs: Sequence[float]) -> float:
    return statistics.fmean(xs)


def perm_test(x: Sequence[float], y: Sequence[float], alternative: str = "greater") -> float:
    """Exact permutation test of mean(x) - mean(y) over every split of the pooled runs.

    alternative: "greater" (H: x > y), "less" (H: x < y) or "two-sided"."""
    x, y = list(x), list(y)
    pooled, n = x + y, len(x)
    obs = mean(x) - mean(y)
    hits = total = 0
    eps = 1e-12
    total_sum = sum(pooled)
    for idx in itertools.combinations(range(len(pooled)), n):
        sx = sum(pooled[i] for i in idx)
        d = sx / n - (total_sum - sx) / len(y)
        total += 1
        if alternative == "greater":
            hits += d >= obs - eps
        elif alternative == "less":
            hits += d <= obs + eps
        else:
            hits += abs(d) >= abs(obs) - eps
    return hits / total


def holm(pvals: dict[str, float]) -> dict[str, float]:
    """Holm-Bonferroni adjusted p-values (monotone, capped at 1)."""
    order = sorted(pvals, key=pvals.get)
    m, out, running = len(order), {}, 0.0
    for k, name in enumerate(order):
        running = max(running, min(1.0, (m - k) * pvals[name]))
        out[name] = running
    return out


def bootstrap_mean_ci(x: Sequence[float], n: int = 10_000, level: float = 0.95, seed: int = 0) -> tuple[float, float]:
    rng = random.Random(seed)
    x = list(x)
    reps = sorted(mean(rng.choices(x, k=len(x))) for _ in range(n))
    return _pct(reps, level)


def bootstrap_diff_ci(x: Sequence[float], y: Sequence[float], n: int = 10_000, level: float = 0.95,
                      seed: int = 0) -> tuple[float, float]:
    """Percentile interval for mean(x) - mean(y), resampling runs within each group."""
    rng = random.Random(seed)
    x, y = list(x), list(y)
    reps = sorted(mean(rng.choices(x, k=len(x))) - mean(rng.choices(y, k=len(y))) for _ in range(n))
    return _pct(reps, level)


def _pct(sorted_reps: list[float], level: float) -> tuple[float, float]:
    lo = sorted_reps[int(math.floor((1 - level) / 2 * (len(sorted_reps) - 1)))]
    hi = sorted_reps[int(math.ceil((1 + level) / 2 * (len(sorted_reps) - 1)))]
    return lo, hi


def auroc(pos: Sequence[float], neg: Sequence[float]) -> float:
    """Probability that a random positive run scores above a random negative run (ties count one half)."""
    wins = sum((p > q) + 0.5 * (p == q) for p in pos for q in neg)
    return wins / (len(pos) * len(neg))


def bootstrap_auroc_ci(pos, neg, n: int = 10_000, level: float = 0.95, seed: int = 0) -> tuple[float, float]:
    rng = random.Random(seed)
    pos, neg = list(pos), list(neg)
    reps = sorted(auroc(rng.choices(pos, k=len(pos)), rng.choices(neg, k=len(neg))) for _ in range(n))
    return _pct(reps, level)


def wilson_ci(k: int, n: int, z: float = 1.959964) -> tuple[float, float]:
    """Wilson score interval for a proportion k/n."""
    if n == 0:
        return (float("nan"), float("nan"))
    p = k / n
    den = 1 + z * z / n
    centre = (p + z * z / (2 * n)) / den
    half = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / den
    return max(0.0, centre - half), min(1.0, centre + half)
