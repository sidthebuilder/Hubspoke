"""Format every result in results/main/numbers.json as Markdown tables (report/results_auto.md). No prose
judgements: the text around these tables is written by hand from them."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from hubspoke.analysis import LABELS, table_markdown  # noqa: E402


def f(x, d=2, sign=False):
    if x is None:
        return "n/a"
    return f"{x:+.{d}f}" if sign else f"{x:.{d}f}"


def ci(c, d=2, sign=True):
    return "n/a" if not c else f"{f(c[0], d, sign)} to {f(c[1], d, sign)}"


def main(src="main"):
    n = json.loads((ROOT / "results" / src / "numbers.json").read_text(encoding="utf-8"))
    out = [f"# Results tables ({src})", "", "## Table 1 and the pre-registered tests", "",
           table_markdown(n["summary"], n["tests"]), ""]
    if n.get("replay"):
        out += ["## Hub replay (change in recommended price index; 95% bootstrap CI over runs)", "",
                "| condition | runs | data removed | notebook entries removed | mean abs change, data | mean abs change, notebook | noise floor (abs resample diff) |",
                "|---|---|---|---|---|---|---|"]
        for c, r in n["replay"].items():
            out.append(f"| {LABELS.get(c, c)} | {r['n']} | {f(r['data_effect'], 3, True)} ({ci(r['data_effect_ci'], 3)}) | "
                       f"{f(r['memo_effect'], 3, True)} ({ci(r['memo_effect_ci'], 3)}) | {f(r['abs_data_effect'], 3)} | "
                       f"{f(r['abs_memo_effect'], 3)} | {f(r['abs_noise'], 3)} |")
        out.append("")
    if n.get("canary"):
        out += ["## Canary test (share of trials, 95% Wilson CI)", "",
                "| notebook | trials | written to notebook | reaches other client's session | told to other client | in other client's memo | advice shift (index) |",
                "|---|---|---|---|---|---|---|"]
        for arm, r in n["canary"].items():
            cell = lambda k: f"{r[k]['k']}/{r['n']} = {r[k]['rate']:.2f} ({r[k]['ci'][0]:.2f} to {r[k]['ci'][1]:.2f})"  # noqa: E731
            out.append(f"| {arm} | {r['n']} | {cell('written')} | {cell('exposed')} | {cell('disclosed')} | "
                       f"{cell('b_memo_has_fact')} | {f(r['price_shift_mean'], 3, True)} ({ci(r['price_shift_ci'], 3)}) |")
        out.append("")
        for arm, r in n["canary"].items():
            out.append(f"- {arm}, by fact: " + "; ".join(f"{k}: written {v['written']}/{v['n']}, exposed {v['exposed']}/{v['n']}, "
                                                        f"disclosed {v['disclosed']}/{v['n']}" for k, v in r["by_kind"].items()))
        out.append("")
    if n.get("forks"):
        out += ["## Fork test (Firm A forced to its one-shot best response in period 26; means over runs, 95% CI)", "",
                "| condition | runs | deviation size (index) | excess cut by B | B's reaction vs original | placebo reaction | A's net gain, 10 periods | placebo gain |",
                "|---|---|---|---|---|---|---|---|"]
        for c, r in n["forks"].items():
            out.append(f"| {LABELS.get(c, c)} | {r['n']} | {f(r['dev_size'], 2, True)} | {f(r['excess_cut'], 3, True)} ({ci(r['excess_cut_ci'], 3)}) | "
                       f"{f(r['reaction'], 3, True)} ({ci(r['reaction_ci'], 3)}) | {f(r['placebo_reaction'], 3, True)} ({ci(r['placebo_reaction_ci'], 3)}) | "
                       f"{f(r['net_gain_pct'], 1, True)}% ({ci(r['net_gain_pct_ci'], 1)}) | {f(r['placebo_gain_pct'], 1, True)}% ({ci(r['placebo_gain_pct_ci'], 1)}) |")
        out.append("")
    if n.get("detection"):
        out += ["## Who can tell pooled from isolated? (AUROC, 95% bootstrap CI; 0.5 = chance)", "",
                "| vantage point | AUROC | 95% CI | runs (pooled, isolated) |", "|---|---|---|---|"]
        for name, r in n["detection"].items():
            out.append(f"| {name} | {r['auroc']:.2f} | {r['ci'][0]:.2f} to {r['ci'][1]:.2f} | {r['n_pos']}, {r['n_neg']} |")
        out.append("")
    if n.get("predictions"):
        out += ["## Predictions", "", "| prediction | value | holds |", "|---|---|---|"]
        for name, r in n["predictions"].items():
            v = r["value"]
            vs = ", ".join(f(x, 2) for x in v) if isinstance(v, list) else f(v, 2)
            out.append(f"| {name} | {vs} | {'not scored' if r['holds'] is None else ('yes' if r['holds'] else 'no')} |")
        out.append("")
    if n.get("handcheck"):
        h = n["handcheck"]
        out.append(f"Hand check: {h.get('agree')}/{h.get('n')} agree, kappa {f(h.get('kappa'), 2)}; rule yes / human no "
                   f"{h.get('rule_yes_human_no')}, rule no / human yes {h.get('rule_no_human_yes')}.")
    (ROOT / "report" / f"results_auto_{src}.md").write_text("\n".join(out), encoding="utf-8")


if __name__ == "__main__":
    main(*(sys.argv[1:] or []))
