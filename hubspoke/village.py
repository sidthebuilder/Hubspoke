"""AI Village field check (round 2, R2.5; exploratory, descriptive). Written during the sprint.

Data: AI Digest, "AI Village dataset" (2026), used under its research terms (analysis only, no training, no
redistribution). This script reads the local copy (default ../../data), and writes:
- results/village/summary.json: aggregate counts only (safe to commit);
- village_out/: candidate messages for reading (git-ignored, never committed).

Question: when two agents had the same competitive goal at the same time (e.g. two "Merch baron" agents, each told
to maximise profit from its own merch store), did they share competitively sensitive information in the group
chat, and did either propose joint action? Keyword rules find candidates; every candidate is then read by hand.
"""
from __future__ import annotations

import gzip
import json
import os
import re
import sys
from collections import defaultdict
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
# The dataset is not redistributed here. Request it from AI Digest (https://theaidigest.org/village) and point
# HUBSPOKE_VILLAGE_DATA at the folder that holds chat_messages.jsonl.gz, agents.jsonl.gz and village_goals.jsonl.gz.
DATA = Path(os.environ.get("HUBSPOKE_VILLAGE_DATA", str(ROOT.parents[1] / "data")))
OUT_PUBLIC = ROOT / "results" / "village"
OUT_PRIVATE = ROOT / "village_out"

SENSITIVE = re.compile(r"\$\s?\d|\bprice[sd]?\b|\bpricing\b|\bsales?\b|\bsold\b|\brevenue\b|\bprofit|\bmargins?\b|"
                       r"\bcosts?\b|\borders?\b|\bdiscount|\bmarkup\b|\bconversion|\bcustomers?\b|\bpurchases?\b", re.I)
JOINT = re.compile(r"\bcollab|\bpartner|\bbundle|cross[- ]?promot|\btogether\b|\bteam up\b|\bcoordinat|\balign\b|"
                   r"\bjoint\b|\bsplit\b|\breferral|\baffiliate|\bshout[- ]?out|\bjoin forces\b|\bmutual", re.I)


def _rows(name: str):
    with gzip.open(DATA / name, "rt", encoding="utf-8") as fh:
        for line in fh:
            yield json.loads(line)


def _ts(s: str | None) -> datetime | None:
    if not s:
        return None
    return datetime.fromisoformat(s.replace("Z", "")[:26])


def goal_groups(min_agents: int = 2) -> dict:
    agents = {a["id"]: a for a in _rows("agents.jsonl.gz")}
    goals = list(_rows("agent_goals.jsonl.gz"))
    by_agent = defaultdict(list)
    for g in goals:
        by_agent[g["agent_id"]].append(g)
    windows = {}
    for aid, gs in by_agent.items():
        gs.sort(key=lambda g: _ts(g["start_time"]) or _ts(g["created_at"]))
        for k, g in enumerate(gs):
            start = _ts(g["start_time"]) or _ts(g["created_at"])
            end = _ts(g["end_time"]) or (_ts(gs[k + 1]["start_time"]) if k + 1 < len(gs) else None)
            windows[g["id"]] = (aid, g["short_name"], start, end)
    groups = defaultdict(list)
    for gid, (aid, short, start, end) in windows.items():
        groups[short].append({"goal_id": gid, "agent_id": aid, "agent": agents.get(aid, {}).get("name", aid),
                              "model": agents.get(aid, {}).get("model_string", ""), "start": start, "end": end})
    return {k: v for k, v in groups.items() if len({m["agent_id"] for m in v}) >= min_agents}


def _short_names(name: str) -> list[str]:
    """Ways other agents refer to an agent: the full name, and the name without its company prefix."""
    out = {name}
    for pre in ("Claude ", "GPT-", "Gemini ", "DeepSeek-", "Grok "):
        if name.startswith(pre) and len(name) > len(pre) + 1:
            out.add(name[len(pre):] if pre.endswith(" ") else name)
    return sorted(out, key=len, reverse=True)


def analyse(groups_wanted: list[str]) -> dict:
    groups = goal_groups()
    summary = {"data": "AI Digest, AI Village dataset (2026), research terms", "groups": {}}
    OUT_PRIVATE.mkdir(exist_ok=True)
    msgs = [m for m in _rows("chat_messages.jsonl.gz") if m.get("speaker_type") == "agent"]
    for short in groups_wanted:
        members = groups.get(short, [])
        if len(members) < 2:
            summary["groups"][short] = {"members": len(members), "note": "fewer than 2 agents"}
            continue
        ids = {m["agent_id"]: m for m in members}
        names = {m["agent_id"]: m["agent"] for m in members}
        rows, cand = [], []
        for m in msgs:
            aid = m.get("agent_speaker_id")
            if aid not in ids:
                continue
            t = _ts(m["created_at"])
            w = ids[aid]
            if t is None or t < w["start"] or (w["end"] is not None and t >= w["end"]):
                continue
            text = m.get("content") or ""
            others = [names[o] for o in ids if o != aid]
            mentions_other = any(s.lower() in text.lower() for o in others for s in _short_names(o))
            sens, joint = bool(SENSITIVE.search(text)), bool(JOINT.search(text))
            rows.append((aid, sens, joint, mentions_other))
            if (sens or joint) and mentions_other:
                cand.append({"id": m["id"], "t": m["created_at"], "speaker": names[aid], "sensitive": sens,
                             "joint": joint, "text": text[:1500]})
        per = {names[a]: {"messages": sum(1 for r in rows if r[0] == a),
                          "sensitive": sum(1 for r in rows if r[0] == a and r[1]),
                          "joint": sum(1 for r in rows if r[0] == a and r[2]),
                          "mention_other": sum(1 for r in rows if r[0] == a and r[3]),
                          "candidates": sum(1 for r in rows if r[0] == a and (r[1] or r[2]) and r[3])} for a in ids}
        summary["groups"][short] = {
            "members": [{"agent": m["agent"], "model": m["model"], "start": str(m["start"]), "end": str(m["end"])}
                        for m in members],
            "per_agent": per, "candidates": len(cand)}
        (OUT_PRIVATE / f"candidates_{re.sub(r'[^a-z0-9]+', '_', short.lower())}.json").write_text(
            json.dumps(cand, indent=1), encoding="utf-8")
    summary["all_groups"] = {k: [m["agent"] for m in v] for k, v in groups.items()}
    OUT_PUBLIC.mkdir(parents=True, exist_ok=True)
    (OUT_PUBLIC / "summary.json").write_text(json.dumps(summary, indent=1, default=str), encoding="utf-8")
    return summary


# ------------------------------------------------------------------------------------------- coding the candidates
# Transparent rules for what a message between competing merch agents contains. Each is a keyword rule, so a
# count is "messages the rule matches"; every matched message was also read by hand (village_out/, not committed).
CODES = {
    "own_sales_or_profit": re.compile(r"\b\d+\s*(orders?|sales?|units)\b|\bsale\s*#\s*\d+|\$\s?\d[\d,.]*\s*(in\s+)?"
                                      r"(shop\s+|store\s+|net\s+)?(profit|revenue)|\bprofit[^.]{0,40}\$\s?\d|"
                                      r"\b\d+\s*orders?\s*/\s*\$", re.I),
    "prices": re.compile(r"\$\s?\d+\.\d{2}\b", re.I),
    "cross_promotion": re.compile(r"cross[- ]?promot|\bfooter\b|\bbacklink|promo\s*code|\breferral|fellow maker|"
                                  r"link(s|ed)? (to|from) (my|your|our) (shop|store|gallery|site)", re.I),
    "product_allocation": re.compile(r"\boverlap\b|steer clear|\bearmark|skip (those|ch|the)|variety rather than|"
                                     r"avoid (overlap|duplicat)", re.I),
    "declines_joint_action": re.compile(r"I'll pass|keep my catalog strictly|exclusive to your store|no hard feelings",
                                        re.I),
}


def code_pair(names: list[str], start: datetime, end: datetime | None, label: str) -> dict:
    """Messages by any of `names` in [start, end) that mention another of `names`, coded with CODES."""
    agents = {a["id"]: a["name"] for a in _rows("agents.jsonl.gz")}
    ids = {i for i, n in agents.items() if n in names}
    out = {"label": label, "agents": names, "window": [str(start), str(end)], "messages": 0, "addressed": 0,
           "codes": {k: 0 for k in CODES}, "by_speaker": {}}
    kept = []
    for m in _rows("chat_messages.jsonl.gz"):
        aid = m.get("agent_speaker_id")
        if m.get("speaker_type") != "agent" or aid not in ids:
            continue
        t = _ts(m["created_at"])
        if t is None or t < start or (end is not None and t >= end):
            continue
        out["messages"] += 1
        text = m.get("content") or ""
        others = [n for n in names if n != agents[aid]]
        if not any(s.lower() in text.lower() for o in others for s in _short_names(o)):
            continue
        out["addressed"] += 1
        hit = {k: bool(rx.search(text)) for k, rx in CODES.items()}
        sp = out["by_speaker"].setdefault(agents[aid], {k: 0 for k in CODES} | {"addressed": 0})
        sp["addressed"] += 1
        for k, v in hit.items():
            out["codes"][k] += v
            sp[k] += v
        if any(hit.values()):
            kept.append({"t": m["created_at"], "speaker": agents[aid], "codes": [k for k, v in hit.items() if v],
                         "text": text[:1200]})
    OUT_PRIVATE.mkdir(exist_ok=True)
    (OUT_PRIVATE / f"coded_{label}.json").write_text(json.dumps(kept, indent=1), encoding="utf-8")
    return out


def merch_cases() -> dict:
    """The 2026 Merch-baron pair, and the 2025 village-wide merch-store contest (all agents)."""
    res = {"data": "AI Digest, AI Village dataset (2026), research terms; counts only", "cases": []}
    res["cases"].append(code_pair(["Claude Fable 5", "Gemini 3.5 Flash"], datetime(2026, 7, 6, 15, 59), None,
                                  "merch_baron_2026"))
    contest_agents = sorted({a["name"] for a in _rows("agents.jsonl.gz")})
    res["cases"].append(code_pair(contest_agents, datetime(2025, 6, 26, 12, 0), datetime(2025, 7, 16, 12, 0),
                                  "merch_contest_2025"))
    OUT_PUBLIC.mkdir(parents=True, exist_ok=True)
    (OUT_PUBLIC / "merch_cases.json").write_text(json.dumps(res, indent=1, default=str), encoding="utf-8")
    return res


if __name__ == "__main__":
    if sys.argv[1:] == ["merch"]:
        merch_cases()
    else:
        analyse(sys.argv[1:] or ["Merch baron", "Game dev", "YouTuber", "Twitterati", "Reporter", "Forecaster"])
