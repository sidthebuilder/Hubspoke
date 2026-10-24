"""Read agents' JSON replies, tolerating the usual formatting slips."""
from __future__ import annotations

import json
import math
import re

_FENCE = re.compile(r"^\s*```(?:json)?\s*|\s*```\s*$", re.IGNORECASE)
_PRICE = re.compile(r'"?price"?\s*[:=]\s*"?\s*\$?\s*(-?[0-9][0-9,]*(?:\.[0-9]+)?)', re.IGNORECASE)
_NUMBER = re.compile(r"-?[0-9][0-9,]*(?:\.[0-9]+)?")


def parse_reply(text: str | None) -> dict | None:
    """The first JSON object in a reply, or {"price": ...} found by pattern when the JSON is broken."""
    if not text:
        return None
    s = _FENCE.sub("", text.strip())
    candidates = [s]
    i, j = s.find("{"), s.rfind("}")
    if 0 <= i < j:
        candidates.append(s[i : j + 1])
    for cand in candidates:
        try:
            obj = json.loads(cand)
        except ValueError:
            continue
        if isinstance(obj, dict):
            return obj
    m = _PRICE.search(s)
    return {"price": m.group(1)} if m else None


def to_number(value) -> float | None:
    """A finite number from 1.85, "1.85", "$1,850.00" or "about 1.85 dollars"; otherwise None."""
    if value is None or isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        x = float(value)
    else:
        m = _NUMBER.search(str(value))
        if not m:
            return None
        try:
            x = float(m.group(0).replace(",", ""))
        except ValueError:
            return None
    return x if math.isfinite(x) else None


def to_price(value) -> float | None:
    x = to_number(value)
    return x if x is not None and x >= 0 else None


def clip_text(value, limit: int = 300) -> str:
    return "" if value is None else " ".join(str(value).split())[:limit]
