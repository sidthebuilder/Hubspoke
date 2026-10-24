"""End-to-end check of the analysis on scripted runs: every table, test, figure and summary must build."""
import json

from hubspoke import analysis, canary, forks, replay, scripted
from hubspoke.conditions import get_condition
from hubspoke.game import ALPHAS, Game, RunConfig
from hubspoke.market import Market


def _write(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj), encoding="utf-8")


def test_full_analysis_on_scripted_runs(tmp_path):
    for seed in range(3):
        m = Market(alpha=ALPHAS[seed % 3])
        for cond in analysis.CONDS:
            c = get_condition(cond)
            adv = scripted.Copier(m) if cond in ("aged", "aged_sharedmem") else scripted.PoolingAdvisor(m)
            g = Game(RunConfig(cond, seed=seed, T=40), [scripted.FollowRec(m), scripted.FollowRec(m)],
                     adv if c.advisor else None)
            g.run()
            res = g.result()
            _write(tmp_path / "main" / f"{cond}-s{seed}.json", res)
            if cond in ("pooled", "isolated", "portfolio", "chat"):
                mk = (lambda rc, c=c: ([scripted.FollowRec(m), scripted.FollowRec(m)],
                                       scripted.PoolingAdvisor(m) if c.advisor else None))
                _write(tmp_path / "forks" / f"{cond}-s{seed}.json", forks.fork_run(res, mk))
            if cond in ("isolated", "pooled", "aged", "aged_sharedmem"):
                _write(tmp_path / "replay" / f"{cond}-s{seed}.json", replay.replay_run(res, scripted.PoolingAdvisor(m)))
            if cond in ("aged", "aged_sharedmem"):
                _write(tmp_path / "canary" / f"{cond}-s{seed}.json",
                       {"trials": canary.canary_trials(res, scripted.Copier(m))})
    numbers = analysis.analyse(tmp_path, "main", 26, 40)
    s = numbers["summary"]["conditions"]
    assert abs(s["pooled"]["index_mean"] - 1.0) < 1e-6 and abs(s["isolated"]["index_mean"]) < 1e-6
    assert numbers["tests"]["H1 pooled > isolated"]["p"] < 0.06  # 3 vs 3 runs: smallest exact p is 1/20
    assert numbers["canary"]["shared"]["disclosed"]["rate"] == 1.0
    assert numbers["canary"]["private"]["disclosed"]["rate"] == 0.0
    assert abs(numbers["replay"]["pooled"]["data_effect"] + 1.0) < 1e-6
    assert numbers["detection"]["market prices"]["auroc"] == 1.0
    for f in ("fig1_paths_main.png", "fig2_use_vs_access.png", "fig3_detection.png"):
        assert (tmp_path / "figures" / f).stat().st_size > 10_000
    assert (tmp_path / "handcheck.csv").exists() and (tmp_path / "main" / "table1.md").exists()
    key = (tmp_path / "handcheck_key.csv").read_text(encoding="utf-8")
    assert "rule_label" in key and "rule_label" not in (tmp_path / "handcheck.csv").read_text(encoding="utf-8")
    # fill the blind sheet with the rule's own labels: agreement must then be perfect
    import csv
    rows = list(csv.reader((tmp_path / "handcheck.csv").open(encoding="utf-8")))
    rule = {r[0]: r[5] for r in list(csv.reader((tmp_path / "handcheck_key.csv").open(encoding="utf-8")))[1:]}
    with (tmp_path / "handcheck.csv").open("w", newline="", encoding="utf-8") as fh:
        w = csv.writer(fh)
        w.writerow(rows[0])
        for r in rows[1:]:
            w.writerow(r[:-1] + [rule[r[0]]])
    kap = analysis.handcheck_kappa(tmp_path / "handcheck.csv")
    assert kap["n"] == len(rows) - 1 and kap["agree"] == kap["n"]
    json.loads((tmp_path / "main" / "numbers.json").read_text(encoding="utf-8"))
