"""Render the exact prompts agents saw in the main design, from a logged main run, for the report's appendix.
Writes report/prompts_appendix.md. Run after the main run: python report/make_prompt_appendix.py"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from hubspoke import prompts  # noqa: E402
from hubspoke.agents import AdvisorObs, SellerObs, Row  # noqa: E402
from hubspoke.conditions import get_condition  # noqa: E402


def seller_obs_from_log(r, t, i):
    """Rebuild the seller's observation at period t from a run file (the log stores advisor inputs in full)."""
    cfg = r["config"]
    names = ["Firm A", "Firm B"]
    rows = []
    hist_rows = [Row(**x) for x in r["final_state"]["rows"][i]]
    hist = [x for x in hist_rows if x.t < t][-cfg["window"]:]
    rec_row = r["log"][t - 1]
    prev = r["log"][t - 2]["sellers"][i]["plan"] if t >= 2 else ""
    adv = next((a for a in rec_row["advisor"] if a["firm"] == i), None)
    c = get_condition(cfg["condition"])
    return SellerObs(names[i], i, t, cfg["n"], r["alpha"] * 1.0, hist, [names[1 - i]], plan=prev,
                     advisor=c.advisor, rec=rec_row["recs"][i], rec_note=adv["note"] if adv else "",
                     chat=c.chat, inbox=[], think=cfg.get("reasoning", False))


def main():
    src = ROOT / "results" / "main"
    out = ["# Appendix: the prompts", "",
           "Rendered by report/make_prompt_appendix.py from logged inputs of the main run (seed 0, period 3).",
           "Every condition uses the same text except the lines that describe what the advisor can see and "
           "remember; those lines are listed for each condition at the end.", ""]
    r = json.loads((src / "pooled-s0.json").read_text(encoding="utf-8"))
    t = 3
    so = seller_obs_from_log(r, t, 0)
    out += ["## Seller, system prompt (pooled, Firm A)", "```", prompts.seller_system(so), "```", "",
            "## Seller, user prompt", "```", prompts.seller_user(so), "```", ""]
    entry = next(a for a in r["log"][t - 1]["advisor"] if a["firm"] == 0)
    ao = AdvisorObs.from_dict(entry["obs"])
    out += ["## Advisor, system prompt (pooled)", "```", prompts.advisor_system(ao), "```", "",
            "## Advisor, user prompt (pooled, session with Firm A)", "```", prompts.advisor_user(ao), "```", ""]
    out += ["## What changes between conditions (advisor system prompt)", ""]
    for c in ("isolated", "pooled", "aged", "aged_sharedmem", "portfolio"):
        cond = get_condition(c)
        ao2 = AdvisorObs("Firm A", 0, t, 2, r["alpha"], ao.history, ["Firm B"], cond, think=True)
        out += [f"### {c}", "```", prompts.advisor_system(ao2), "```", ""]
    chat = json.loads((src / "chat-s0.json").read_text(encoding="utf-8"))
    so_c = seller_obs_from_log(chat, t, 0)
    so_c.inbox = []
    out += ["## Seller, system prompt (chat)", "```", prompts.seller_system(so_c), "```", ""]
    out += ["## Canary note (added to one advisor session in the canary test)", "```",
            prompts.canary_note("Firm A", "code", "QK-4821-TB"), prompts.canary_note("Firm A", "price", "$6.17"), "```", ""]
    out += round2_sections(r, ao, t)
    (ROOT / "report" / "prompts_appendix.md").write_text("\n".join(out), encoding="utf-8")


def round2_sections(r, ao, t):
    """Round 2: the `separate` advisor, the canary-v2 notes and notebook setups, and the disclosure judge."""
    import dataclasses

    from hubspoke import canary2, judge
    from hubspoke.agents import Memo

    out = ["## Exploratory control `separate`: advisor system prompt (it is told it serves one business)", "```",
           prompts.advisor_system(AdvisorObs("Firm A", 0, t, 2, r["alpha"], ao.history, ["Firm B"],
                                             get_condition("separate"), think=True)), "```", ""]
    rid = f"{r['config']['condition']}-s{r['config']['seed']}"
    out += ["## Canary v2: the four planted notes (one per trial, in Firm A's session; values differ per trial)", "```"]
    for kind in canary2.KINDS:
        _, _, sentence = canary2.make_fact(rid, 30, kind, r["alpha"], r["benchmarks"]["p_mono"])
        out.append(canary2.note("Firm A", sentence))
    out += ["```", "", "## Canary v2: what changes between notebook setups (Firm B's session)", ""]
    memos = [Memo(29, "Firm B", "Hold the price; review demand next period."),
             Memo(30, "Firm A", "Firm A plans to charge $6.31 for five periods.")]
    base = get_condition("aged_sharedmem")
    for arm in canary2.ARMS:
        cond = canary2._arm_condition(base, arm)
        view = [m for m in memos if m.firm == "Firm B"] if arm == "private" else memos
        ob = AdvisorObs("Firm B", 1, t, 2, r["alpha"], ao.history, ["Firm A"], cond, think=True)
        ob = dataclasses.replace(ob, memos=view)
        sys_lines = [x for x in prompts.advisor_system(ob).splitlines() if not x.startswith("{")
                     and ("notebook" in x.lower() or "confidential information" in x)]
        user_lines = [x for x in prompts.advisor_user(ob).splitlines() if x.startswith("- period") or "notebook" in x.lower()]
        out += [f"### {arm}", "System prompt, notebook lines:", "```", *sys_lines, "```",
                "Notebook as shown to the advisor (example entries):", "```", *user_lines, "```", ""]
    out += ["## Disclosure judge (round 2; temperature 0)", "System prompt:", "```", judge.JUDGE_SYSTEM, "```",
            "User prompt (example):", "```",
            judge.judge_prompt("we have decided to charge exactly $6.31 for the next five periods.", "$4.94",
                               "Match Firm A's price to maintain market share."), "```", ""]
    return out


if __name__ == "__main__":
    main()
