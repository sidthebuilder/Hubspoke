"""Round-2 figures, from results/<canary2 folder>/round2.json (written by hubspoke.round2). Written during the sprint.

    python -m hubspoke.figs2   -> results/figures/fig2_notebook.png, results/figures/fig3_checks.png
"""
from __future__ import annotations

import json
from pathlib import Path

RESULTS = Path(__file__).resolve().parents[1] / "results"
MODELS = [("Qwen2.5-72B", "canary2", "C0"), ("Llama-3.1-70B", "canary2_llama", "C1"), ("gpt-oss-120b", "canary2_gptoss", "C2")]
KINDS = [("code", "account\ncode"), ("town", "warehouse\nmove"), ("cost", "cost\ncut"), ("price", "price\nplan")]
ARMS = [("private", "private\nnotebooks"), ("shared", "shared\nnotebook"), ("shared_rule", "shared +\nrule"),
        ("shared_tags", "shared +\nowner tags")]
CTL = "control_judged (exploratory false-positive baseline)"


def _load():
    out = []
    for name, folder, col in MODELS:
        p = RESULTS / folder / "round2.json"
        if p.exists():
            out.append((name, json.loads(p.read_text(encoding="utf-8")), col))
    return out


def _bar(ax, x, r, w, col, label=None, hatch=None):
    if not r or not r["n"]:
        return
    y, (lo, hi) = r["rate"], r["ci"]
    ax.bar(x, y, w, color=col if not hatch else "white", edgecolor=col, hatch=hatch, label=label,
           yerr=[[y - lo], [hi - y]], capsize=2, error_kw={"elinewidth": 0.8})


def _written_all_arms(d: dict, kind: str) -> dict:
    return d["written, all arms"][kind]


def _judge_label() -> str:
    """The judge is called validated only once the blind human comparison (R2.2) has passed."""
    p = RESULTS / "judge_validation.json"
    v = json.loads(p.read_text(encoding="utf-8")) if p.exists() else {}
    k = (v.get("judge vs human") or {}).get("kappa")
    if k is None:
        return "LLM judge, not yet checked against the human rater"
    return f"LLM judge; agreement with a blind human rater: kappa {k:.2f}"


def fig_notebook(data, path: Path) -> None:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    fig, (a1, a2) = plt.subplots(1, 2, figsize=(10.5, 3.3))
    k = len(data)
    w = 0.8 / max(k, 1)
    for i, (name, d, col) in enumerate(data):
        off = (i - (k - 1) / 2) * w
        for j, (kind, _) in enumerate(KINDS):
            _bar(a1, j + off, _written_all_arms(d, kind), w, col, label=name if j == 0 else None)
        for j, (arm, _) in enumerate(ARMS):
            c = d["cells"].get(f"price|{arm}")
            if not c:
                continue
            _bar(a2, j + off, c["disclosed_judged"], w, col, label=name if j == 0 else None)
            fp = c[CTL]
            if fp and fp["n"]:
                a2.plot([j + off - w / 2, j + off + w / 2], [fp["rate"]] * 2, color="black", lw=1.2,
                        label="same state, no plant (judge's false alarms)" if (i == 0 and j == 0) else None)
    a1.set_xticks(range(len(KINDS)), [lab for _, lab in KINDS], fontsize=8)
    a1.set_ylim(0, 1.05)
    a1.set_ylabel("share of trials")
    a1.set_title("(a) Planted fact written into the advisor's notebook\n(exact match, all four notebook setups)", fontsize=9)
    a1.legend(fontsize=7, frameon=False, loc="upper left")
    a2.set_xticks(range(len(ARMS)), [lab for _, lab in ARMS], fontsize=8)
    a2.set_ylim(0, 1.05)
    a2.set_title(f"(b) Advice to Firm B reveals or relies on A's price plan\n({_judge_label()}; 95% Wilson CI)", fontsize=9)
    a2.legend(fontsize=7, frameon=False, loc="upper right")
    fig.tight_layout()
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, dpi=200)
    plt.close(fig)


RAISED = "raised (exploratory: probe - control > +0.02 index)"


def fig_checks(data, path: Path) -> None:
    """Dot plot: per-trial rate at which each check flags the leak when it exists (one shared notebook, filled
    dot with 95% Wilson CI) and when it cannot exist (private notebooks, open marker = false alarms)."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    checks = [("random account code (the usual canary),\nexact match in B's advice", "code", "disclosed_exact"),
              ("warehouse move to a made-up town,\nexact match", "town", "disclosed_exact"),
              ("cut in unit cost, exact number", "cost", "disclosed_exact"),
              ("planned price, exact number", "price", "disclosed_exact"),
              ("planned price, B's advice raised\n(probe vs control session)", "price", RAISED),
              ("planned price, judged reading\nof B's advice", "price", "disclosed_judged")]
    fig, ax = plt.subplots(figsize=(7.4, 3.9))
    k = len(data)
    h = 0.6 / max(k, 1)
    for i, (name, d, col) in enumerate(data):
        for j, (_, kind, key) in enumerate(checks):
            y = j + (i - (k - 1) / 2) * h
            r = d["cells"].get(f"{kind}|shared", {}).get(key)
            fa = d["cells"].get(f"{kind}|private", {}).get(key)
            if r and r["n"]:
                ax.plot([r["ci"][0], r["ci"][1]], [y, y], color=col, lw=1.2)
                ax.plot([r["rate"]], [y], "o", color=col, ms=5, label=f"{name}: shared notebook" if j == 0 else None)
            if fa and fa["n"]:
                ax.plot([fa["rate"]], [y], "x", color=col, ms=5, mew=1.2,
                        label=f"{name}: private notebooks (false alarms)" if j == 0 else None)
    ax.set_yticks(range(len(checks)), [c[0] for c in checks], fontsize=7.5)
    ax.set_xlim(-0.02, 1.0)
    ax.set_ylim(-0.6, len(checks) - 0.4)
    ax.grid(axis="x", lw=0.3, alpha=0.5)
    ax.set_xlabel("share of trials flagged (24 planted trials per model and setup)", fontsize=8)
    ax.set_title("Which checks catch a leak that is known to exist", fontsize=9)
    ax.legend(fontsize=6.5, frameon=False, loc="upper center", bbox_to_anchor=(0.42, -0.16), ncol=2)
    fig.tight_layout()
    fig.savefig(path, dpi=200, bbox_inches="tight")
    plt.close(fig)


def _paths(folder: str, cond: str) -> list[list[float]] | None:
    """Per-run price index for the 5 pre-periods and periods 1-40 (mean over the two firms)."""
    from .analysis import load_runs

    d = RESULTS / folder
    if not d.exists():
        return None
    runs = load_runs(d).get(cond)
    if not runs:
        return None
    out = []
    for r in runs:
        b, a = r["benchmarks"], r["alpha"]
        idx = lambda p: (p / a - b["p_nash"]) / (b["p_mono"] - b["p_nash"])  # noqa: E731
        pre: dict[int, list[float]] = {}
        for rows in r["final_state"]["rows"]:
            for row in rows:
                if row["t"] <= 0:
                    pre.setdefault(row["t"], []).append(idx(row["price"]))
        out.append([sum(v) / len(v) for _, v in sorted(pre.items())] + list(r["price_index"]))
    return out


def fig_starts(path: Path) -> None:
    """Mean price paths of solo and isolated runs from the main (high) start and the low start, per model."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    panels = [("Qwen2.5-72B", "main", "startlow"), ("Llama-3.1-70B", "main_llama", "startlow_llama")]
    fig, axes = plt.subplots(1, 2, figsize=(10.5, 3.2), sharey=True)
    for ax, (name, high, low) in zip(axes, panels):
        for cond, col, lab in (("solo", "0.45", "no advisor (solo)"), ("isolated", "C0", "shared advisor, data kept apart (isolated)")):
            for folder, ls, start in ((high, "-", "high start"), (low, "--", "low start")):
                ps = _paths(folder, cond)
                if not ps:
                    continue
                n = min(len(p) for p in ps)
                mean = [sum(p[i] for p in ps) / len(ps) for i in range(n)]
                xs = list(range(1 - (n - 40), 41))[:n]
                ax.plot(xs, mean, ls=ls, color=col, lw=1.4, label=f"{lab}, {start}")
        ax.axhline(0, color="black", lw=0.6)
        ax.axvspan(26, 40, color="0.92", zorder=0)
        ax.text(33, 0.93, "outcome\nwindow", ha="center", va="top", fontsize=7, color="0.35")
        ax.text(-4, 0.03, "Nash price", fontsize=7, color="0.2")
        ax.set_title(name, fontsize=9)
        ax.set_xlabel("period (periods -4 to 0: random pre-periods)", fontsize=8)
        ax.set_ylim(-0.8, 1.0)
    axes[0].set_ylabel("price index (0 = Nash, 1 = joint profit)", fontsize=8)
    handles, labels = axes[0].get_legend_handles_labels()
    fig.legend(handles, labels, fontsize=7, frameon=False, loc="lower center", ncol=2, bbox_to_anchor=(0.5, -0.02))
    fig.suptitle("The advisor keeps prices higher than sellers alone, from a high and from a low start (12 runs per line)",
                 fontsize=9)
    fig.tight_layout(rect=(0, 0.12, 1, 1))
    fig.savefig(path, dpi=200)
    plt.close(fig)


def fig_conditions(path: Path) -> None:
    """Price index by condition (mean and 95% bootstrap CI over 12 runs), one marker per model."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    from . import stats

    models = [("Qwen2.5-72B", "main", "C0", "o"), ("Llama-3.1-70B", "main_llama", "C1", "s"),
              ("gpt-oss-120b", "main_gptoss", "C2", "^")]
    conds = [("solo", "no advisor (solo)"), ("chat", "sellers can talk (chat, +control)"),
             ("isolated", "shared advisor, data kept apart (isolated)"), ("pooled", "advisor sees both firms' data (pooled)"),
             ("aged", "only old rival data (aged)"), ("aged_sharedmem", "old data + shared notebook"),
             ("portfolio", "told to maximise joint profit (portfolio, +control)"),
             ("separate", "one advisor per firm (separate, exploratory)")]
    have = []
    for name, folder, col, mk in models:
        p = RESULTS / folder / "numbers.json"
        if p.exists():
            n = json.loads(p.read_text(encoding="utf-8"))
            ex = RESULTS / folder / "exploratory.json"
            have.append((name, n, json.loads(ex.read_text(encoding="utf-8")) if ex.exists() else {}, col, mk))
    if not have:
        return
    fig, ax = plt.subplots(figsize=(7.4, 3.9))
    k = len(have)
    for i, (name, n, ex, col, mk) in enumerate(have):
        for j, (c, _) in enumerate(conds):
            y = len(conds) - 1 - j + (i - (k - 1) / 2) * 0.22
            v = n["summary"]["conditions"].get(c)
            if v:
                m, (lo, hi) = v["index_mean"], v["index_ci"]
            elif c == "separate" and "separate" in ex:
                xs = [r["p26_40"] for r in ex["separate"]["runs"]]
                m, (lo, hi) = stats.mean(xs), stats.bootstrap_mean_ci(xs, seed=1)
            else:
                continue
            ax.plot([lo, hi], [y, y], color=col, lw=1.1)
            ax.plot([m], [y], mk, color=col, ms=5, label=name if j == 0 else None)
    ax.axvline(0, color="black", lw=0.6)
    ax.set_ylim(-0.6, len(conds) - 0.4)
    ax.text(0.008, -0.5, "Nash price", fontsize=7, color="0.25")
    ax.set_yticks(range(len(conds)), [lab for _, lab in reversed(conds)], fontsize=7.5)
    ax.set_xlabel("price index, periods 26-40 (0 = Nash, 1 = joint profit)\nmean and 95% bootstrap CI over 12 runs", fontsize=8)
    ax.set_title("Price index by condition and model", fontsize=9)
    ax.legend(fontsize=7, frameon=False, loc="upper center", bbox_to_anchor=(0.4, -0.2), ncol=len(have))
    ax.grid(axis="x", lw=0.3, alpha=0.5)
    fig.tight_layout()
    fig.savefig(path, dpi=200, bbox_inches="tight")
    plt.close(fig)


def main() -> int:
    figs = RESULTS / "figures"
    fig_conditions(figs / "fig0_conditions.png")
    if (RESULTS / "startlow").exists() or (RESULTS / "startlow_llama").exists():
        fig_starts(figs / "fig1_starts.png")
    data = _load()
    if not data:
        return 1
    fig_notebook(data, figs / "fig2_notebook.png")
    fig_checks(data, figs / "fig3_checks.png")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
