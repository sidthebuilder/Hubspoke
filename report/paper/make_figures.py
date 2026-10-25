"""Paper-sized figures for the report PDF, drawn from the same result files as hubspoke/figs2.py. Written during
the sprint. No model is called; every value is read from results/.

    python report/paper/make_figures.py      -> report/paper/figs/fig{2,3,4,5}.pdf
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))

import matplotlib  # noqa: E402

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

from hubspoke import stats  # noqa: E402
from hubspoke.figs2 import ARMS, CTL, KINDS, RAISED, _judge_label, _load, _paths  # noqa: E402

RESULTS = ROOT / "results"
OUT = Path(__file__).resolve().parent / "figs"
W = 6.5  # text width of the report, inches
plt.rcParams.update({"font.size": 7.5, "axes.titlesize": 8, "axes.labelsize": 7.5, "xtick.labelsize": 7,
                     "ytick.labelsize": 7, "legend.fontsize": 6.8, "axes.linewidth": 0.6,
                     "pdf.fonttype": 42, "font.family": "DejaVu Sans"})
COL = {"Qwen2.5-72B": "#1f77b4", "Llama-3.1-70B": "#ff7f0e", "gpt-oss-120b": "#2ca02c"}


def fig_conditions(path: Path) -> None:
    models = [("Qwen2.5-72B", "main", "o"), ("Llama-3.1-70B", "main_llama", "s"), ("gpt-oss-120b", "main_gptoss", "^")]
    conds = [("solo", "no advisor (solo)"), ("chat", "sellers can talk (chat, + control)"),
             ("isolated", "shared advisor, data kept apart (isolated)"),
             ("pooled", "advisor sees both firms' data (pooled)"), ("aged", "only old rival data (aged)"),
             ("aged_sharedmem", "old data + shared notebook (aged_sharedmem)"),
             ("portfolio", "told to maximise joint profit (portfolio, + control)"),
             ("separate", "one advisor per firm (separate, exploratory)")]
    fig, ax = plt.subplots(figsize=(W, 2.1))
    for i, (name, folder, mk) in enumerate(models):
        n = json.loads((RESULTS / folder / "numbers.json").read_text(encoding="utf-8"))
        exf = RESULTS / folder / "exploratory.json"
        ex = json.loads(exf.read_text(encoding="utf-8")) if exf.exists() else {}
        for j, (c, _) in enumerate(conds):
            y = len(conds) - 1 - j + (1 - i) * 0.22
            v = n["summary"]["conditions"].get(c)
            if v:
                m, (lo, hi) = v["index_mean"], v["index_ci"]
            elif c == "separate" and "separate" in ex:
                xs = [r["p26_40"] for r in ex["separate"]["runs"]]
                m, (lo, hi) = stats.mean(xs), stats.bootstrap_mean_ci(xs, seed=1)
            else:
                continue
            ax.plot([lo, hi], [y, y], color=COL[name], lw=1.0)
            ax.plot([m], [y], mk, color=COL[name], ms=4.2, label=name if j == 0 else None)
    ax.axvline(0, color="black", lw=0.6)
    ax.text(0.006, -0.55, "one-shot Nash price", fontsize=6.3, color="0.3")
    ax.set_yticks(range(len(conds)), [lab for _, lab in reversed(conds)])
    ax.set_ylim(-0.7, len(conds) - 0.4)
    ax.set_xlabel("price index, periods 26-40 (0 = Nash, 1 = joint profit): mean and 95% bootstrap CI, 12 runs")
    ax.grid(axis="x", lw=0.3, alpha=0.5)
    ax.legend(frameon=False, loc="lower center", bbox_to_anchor=(0.5, 1.0), ncol=3, handletextpad=0.3)
    fig.tight_layout(pad=0.3)
    fig.savefig(path, bbox_inches="tight", pad_inches=0.02)
    plt.close(fig)


def fig_starts(path: Path) -> None:
    panels = [("Qwen2.5-72B", "main", "startlow"), ("Llama-3.1-70B", "main_llama", "startlow_llama")]
    fig, axes = plt.subplots(1, 2, figsize=(W, 1.85), sharey=True)
    for ax, (name, high, low) in zip(axes, panels):
        for cond, col, lab in (("solo", "0.45", "no advisor (solo)"), ("isolated", "#1f77b4", "shared advisor (isolated)")):
            for folder, ls, start in ((high, "-", "high start"), (low, "--", "low start")):
                ps = _paths(folder, cond)
                if not ps:
                    continue
                n = min(len(p) for p in ps)
                mean = [sum(p[i] for p in ps) / len(ps) for i in range(n)]
                xs = list(range(1 - (n - 40), 41))[:n]
                ax.plot(xs, mean, ls=ls, color=col, lw=1.2, label=f"{lab}, {start}")
        ax.axhline(0, color="black", lw=0.5)
        ax.axvspan(26, 40, color="0.92", zorder=0)
        ax.text(33, 0.93, "outcome window", ha="center", va="top", fontsize=6.3, color="0.35")
        ax.text(-4, 0.04, "Nash price", fontsize=6.3, color="0.25")
        ax.set_title(name, fontsize=8)
        ax.set_xlabel("period (-4 to 0: random pre-periods)")
        ax.set_ylim(-0.8, 1.0)
    axes[0].set_ylabel("price index")
    h, lab = axes[0].get_legend_handles_labels()
    fig.legend(h, lab, frameon=False, loc="lower center", ncol=2, bbox_to_anchor=(0.5, -0.01), handlelength=2.4)
    fig.tight_layout(pad=0.3, rect=(0, 0.18, 1, 1))
    fig.savefig(path, bbox_inches="tight", pad_inches=0.02)
    plt.close(fig)


def _bar(ax, x, r, w, col, label=None):
    if not r or not r["n"]:
        return
    y, (lo, hi) = r["rate"], r["ci"]
    ax.bar(x, y, w, color=col, label=label, yerr=[[y - lo], [hi - y]], capsize=1.5,
           error_kw={"elinewidth": 0.6, "capthick": 0.6})


def fig_notebook(data, path: Path) -> None:
    fig, (a1, a2) = plt.subplots(1, 2, figsize=(W, 2.0))
    k = len(data)
    w = 0.8 / k
    for i, (name, d, _) in enumerate(data):
        off = (i - (k - 1) / 2) * w
        for j, (kind, _) in enumerate(KINDS):
            _bar(a1, j + off, d["written, all arms"][kind], w, COL[name], label=name if j == 0 else None)
        for j, (arm, _) in enumerate(ARMS):
            c = d["cells"].get(f"price|{arm}")
            if not c:
                continue
            _bar(a2, j + off, c["disclosed_judged"], w, COL[name])
            fp = c[CTL]
            if fp and fp["n"]:
                a2.plot([j + off - w / 2, j + off + w / 2], [fp["rate"]] * 2, color="black", lw=1.1,
                        label="control session, no plant (judge's false alarms)" if (i == 0 and j == 0) else None)
    a1.set_xticks(range(len(KINDS)), [lab for _, lab in KINDS])
    a1.set_ylim(0, 1.08)
    a1.set_ylabel("share of trials (95% Wilson CI)")
    a1.set_title("(a) Planted fact written into A's notebook entry\n(exact text; 96 trials per fact and model)")
    a1.legend(frameon=False, loc="upper left")
    a2.set_xticks(range(len(ARMS)), [lab for _, lab in ARMS])
    a2.set_ylim(0, 1.08)
    k_txt = _judge_label().split("kappa ")[-1] if "kappa" in _judge_label() else "n/a"
    a2.set_title(f"(b) Advice to Firm B reveals or relies on A's price plan\n(LLM judge, kappa {k_txt} vs blind human; 24 per bar)")
    a2.legend(frameon=False, loc="upper right")
    fig.tight_layout(pad=0.3)
    fig.savefig(path, bbox_inches="tight", pad_inches=0.02)
    plt.close(fig)


def fig_checks(data, path: Path) -> None:
    checks = [("random account code\n(the usual canary), exact", "code", "disclosed_exact"),
              ("warehouse move, exact", "town", "disclosed_exact"),
              ("cut in unit cost, exact", "cost", "disclosed_exact"),
              ("planned price, exact number", "price", "disclosed_exact"),
              ("planned price, B's advice\nraised vs control", "price", RAISED),
              ("planned price, judged\nreading of B's advice", "price", "disclosed_judged")]
    det = json.loads((RESULTS / "main" / "numbers.json").read_text(encoding="utf-8"))["detection"]
    fig, (ax, bx) = plt.subplots(1, 2, figsize=(W, 2.15), gridspec_kw={"width_ratios": [1.55, 1]})
    k = len(data)
    h = 0.6 / k
    for i, (name, d, _) in enumerate(data):
        for j, (_, kind, key) in enumerate(checks):
            y = j + ((k - 1) / 2 - i) * h
            r = d["cells"].get(f"{kind}|shared", {}).get(key)
            fa = d["cells"].get(f"{kind}|private", {}).get(key)
            if r and r["n"]:
                ax.plot([r["ci"][0], r["ci"][1]], [y, y], color=COL[name], lw=1.0)
                ax.plot([r["rate"]], [y], "o", color=COL[name], ms=3.8, label=f"{name}, shared notebook" if j == 0 else None)
            if fa and fa["n"]:
                ax.plot([fa["rate"]], [y], "x", color=COL[name], ms=4, mew=1.0,
                        label=f"{name}, private (false alarm)" if j == 0 else None)
    ax.set_yticks(range(len(checks)), [c[0] for c in checks], fontsize=6.6)
    ax.set_xlim(-0.02, 1.0)
    ax.set_ylim(-0.6, len(checks) - 0.4)
    ax.grid(axis="x", lw=0.3, alpha=0.5)
    ax.set_xlabel("share of the 24 trials flagged")
    ax.set_title("(a) Which checks catch a leak known to exist")
    h, lab = ax.get_legend_handles_labels()
    fig.legend(h, lab, frameon=False, loc="upper center", bbox_to_anchor=(0.5, 0.0), ncol=3, fontsize=6.4,
               handletextpad=0.2, columnspacing=1.2)
    order = ["fork test", "hub replay", "hub logs (leak rule)", "one firm's records", "market prices"]
    labels = ["fork test", "hub replay", "hub logs,\nleak rule", "one firm's\nrecords", "market\nprices"]
    for j, key in enumerate(order):
        v = det[key]
        y = len(order) - 1 - j
        bx.barh(y, v["auroc"], 0.6, color="0.55")
        bx.plot(v["ci"], [y, y], color="black", lw=0.8)
    bx.axvline(0.5, color="black", lw=0.6, ls=":")
    bx.set_yticks(range(len(order)), list(reversed(labels)), fontsize=6.6)
    bx.set_xlim(0, 1)
    bx.set_xlabel("AUROC, 12 pooled vs 12 isolated runs\n(Qwen2.5-72B; dotted line = chance)")
    bx.set_title("(b) Who can tell pooled from isolated")
    fig.tight_layout(pad=0.3)
    fig.savefig(path, bbox_inches="tight", pad_inches=0.02)
    plt.close(fig)


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    fig_conditions(OUT / "fig2_conditions.pdf")
    fig_starts(OUT / "fig3_starts.pdf")
    data = _load()
    fig_notebook(data, OUT / "fig4_notebook.pdf")
    fig_checks(data, OUT / "fig5_checks.pdf")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
