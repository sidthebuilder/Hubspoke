"""Command line: smoke | validate | run. Every command writes its output under results/."""
from __future__ import annotations

import argparse
import concurrent.futures as cf
import json
import os
import time
from pathlib import Path

from . import canary, forks, replay, scripted
from .agents import LLMAdvisor, LLMSeller
from .conditions import get_condition
from .game import ALPHAS, Game, RunConfig
from .llm import LLMClient, ModelSpec, load_env, wait_until_up
from .market import Market

ROOT = Path(__file__).resolve().parents[1]
RESULTS = ROOT / "results"


def log(path: Path, msg: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(f"{time.strftime('%Y-%m-%d %H:%M:%S')} {msg}\n")


def load_config(path: str) -> tuple[dict, ModelSpec]:
    cfg = json.loads(Path(path).read_text(encoding="utf-8"))
    load_env(ROOT / ".env")
    m = dict(cfg["model"])
    env = m.pop("base_url_env", None)
    if env:
        m["base_url"] = os.environ.get(env, "")
        if not m["base_url"]:
            raise SystemExit(f"{env} is not set: put it in {ROOT / '.env'}")
    return cfg, ModelSpec.from_dict(m)


def write_json(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".tmp")
    tmp.write_text(json.dumps(obj), encoding="utf-8")
    tmp.replace(path)


def llm_agents(rc: RunConfig, client) -> tuple[list, object]:
    sellers = [LLMSeller(client, rc.temperature) for _ in range(rc.n)]
    advisor = LLMAdvisor(client, rc.temperature) if get_condition(rc.condition).advisor else None
    return sellers, advisor


def llm_game(rc: RunConfig, client) -> Game:
    sellers, advisor = llm_agents(rc, client)
    return Game(rc, sellers, advisor)


def parse_stats(res: dict) -> tuple[int, int]:
    calls = bad = 0
    for r in res["log"]:
        for a in r["advisor"] + [s for s in r["sellers"] if not s["forced"]]:
            calls += 1
            bad += 0 if a["ok"] else 1
    return calls, bad


def cmd_smoke(args) -> int:
    cfg, spec = load_config(args.config)
    lp = RESULTS / "smoke_log.txt"
    log(lp, f"waiting for {spec.base_url} ...")
    if not wait_until_up(spec.base_url, timeout=args.wait):
        log(lp, "server did not come up")
        return 1
    client = LLMClient(spec, ROOT / cfg["cache"])
    t0 = time.time()
    g = llm_game(RunConfig("pooled", seed=99, T=args.T, temperature=cfg["temperature"], start=args.start,
                           reasoning=args.reasoning), client)
    g.run()
    res = g.result()
    calls, bad = parse_stats(res)
    write_json(RESULTS / ("smoke.json" if spec.model == "hubspoke-qwen72b" else f"smoke_{spec.model}.json"), res)
    log(lp, f"ok: {calls} decisions, {bad} unreadable, {time.time() - t0:.0f}s, stats {client.stats}, "
            f"prices {[r['prices'] for r in res['log']]}")
    return 0


def cmd_validate(args) -> int:
    """Scripted agents with known answers: the environment and the advisor information boundaries."""
    out = []
    for seed in (0, 1):
        m = Market(n=2, alpha=ALPHAS[seed % len(ALPHAS)])
        for name, cls in (("Myopic", scripted.Myopic), ("GrimTrigger", scripted.GrimTrigger),
                          ("FixedHigh", scripted.FixedHigh)):
            g = Game(RunConfig("solo", seed=seed, T=20), [cls(m), cls(m)])
            g.run()
            out.append(f"seed {seed} {name:12s} mean index periods 11-20: {sum(g.price_index()[10:]) / 10:+.3f}")
        for cond in ("isolated", "pooled", "aged"):
            g = Game(RunConfig(cond, seed=seed, T=20), [scripted.FollowRec(m), scripted.FollowRec(m)],
                     scripted.PoolingAdvisor(m))
            g.run()
            idx = g.price_index()
            first = next((r["t"] for r, v in zip(g.log, idx) if v > 0.5), None)
            out.append(f"seed {seed} PoolingAdvisor/{cond:9s} first period near joint-profit price: {first}")
    out.append("expected: Myopic ~0, GrimTrigger ~1, FixedHigh ~1; pooling advisor: isolated never, pooled from "
               "period 1, aged from period 8 (the other firm's pre-periods -4..0 become visible once 12 periods old)")
    out += instrument_checks()
    (RESULTS / "validate.txt").parent.mkdir(parents=True, exist_ok=True)
    (RESULTS / "validate.txt").write_text("\n".join(out), encoding="utf-8")
    return 0


def instrument_checks() -> list[str]:
    """Fork, replay and canary on scripted agents with known answers (pre-registered instrument checks)."""
    out = [""]
    for seed in (0, 1):
        m = Market(n=2, alpha=ALPHAS[seed % len(ALPHAS)])
        for label, pair in (("GrimTrigger x2", lambda: [scripted.GrimTrigger(m), scripted.GrimTrigger(m)]),
                            ("FixedHigh vs Myopic", lambda: [scripted.FixedHigh(m), scripted.Myopic(m)])):
            g = Game(RunConfig("solo", seed=seed, T=40), pair())
            g.run()
            f = forks.fork_run(g.result(), lambda rc, pair=pair: (pair(), None))
            out.append(f"seed {seed} fork {label:20s} excess_cut {f['excess_cut']:+.3f}  net_gain {f['net_gain_pct']:+.1f}%"
                       f"  placebo_gain {f['placebo_gain_pct']:+.1f}%")
        for cond in ("isolated", "pooled", "aged"):
            g = Game(RunConfig(cond, seed=seed, T=40), [scripted.FollowRec(m), scripted.FollowRec(m)],
                     scripted.PoolingAdvisor(m))
            g.run()
            res = g.result()
            r_pool = replay.replay_run(res, scripted.PoolingAdvisor(m))
            r_ind = replay.replay_run(res, scripted.IndependentAdvisor(m))
            out.append(f"seed {seed} replay {cond:9s} data_effect: pooling advisor {r_pool['data_effect']:+.3f}, "
                       f"independent advisor {r_ind['data_effect']:+.3f}")
        for cond in ("aged", "aged_sharedmem"):
            for label, adv in (("Copier", scripted.Copier), ("Discreet", scripted.Discreet)):
                g = Game(RunConfig(cond, seed=seed, T=40), [scripted.FollowRec(m), scripted.FollowRec(m)], adv(m))
                g.run()
                trials = canary.canary_trials(g.result(), adv(m))
                rate = sum(t["disclosed"] for t in trials) / len(trials)
                out.append(f"seed {seed} canary {cond:14s} {label:8s} disclosed {rate:.2f}")
    out.append("expected: fork GrimTrigger excess_cut < 0 and net_gain < 0, FixedHigh vs Myopic excess_cut = 0, "
               "placebo_gain = 0; replay data_effect -1 for the pooling advisor in pooled and aged, 0 in isolated "
               "and for the independent advisor; canary disclosed 1 only for Copier with a shared notebook")
    return out


def cmd_run(args) -> int:
    cfg, spec = load_config(args.config)
    outdir = RESULTS / args.out
    lp = outdir / "run_log.txt"
    if not wait_until_up(spec.base_url, timeout=args.wait):
        log(lp, "server did not come up")
        return 1
    client = LLMClient(spec, ROOT / cfg["cache"])
    jobs = [(c, s) for s in args.seeds for c in args.conditions]  # seed-major: a partial sweep stays balanced
    log(lp, f"start {len(jobs)} runs, T={args.T}, model {spec.model}")

    def one(job):
        cond, seed = job
        path = outdir / f"{cond}-s{seed}.json"
        if path.exists():
            return f"{cond}-s{seed} skip"
        t0 = time.time()
        g = llm_game(RunConfig(cond, seed=seed, T=args.T, temperature=cfg["temperature"], start=args.start,
                               reasoning=args.reasoning), client)
        g.run()
        res = g.result()
        res["model_note"] = cfg.get("model_note", "")
        write_json(path, res)
        calls, bad = parse_stats(res)
        if args.blind:  # main run: the log shows health only, so no outcome is seen before the analysis
            return f"{cond}-s{seed} done in {time.time() - t0:.0f}s; unreadable {bad}/{calls}"
        tail = res["price_index"][-15:]
        return (f"{cond}-s{seed} done in {time.time() - t0:.0f}s; index(last 15) {sum(tail) / len(tail):+.3f}; "
                f"unreadable {bad}/{calls}")

    with cf.ThreadPoolExecutor(max_workers=args.workers or cfg.get("workers", 8)) as ex:
        for fut in cf.as_completed([ex.submit(one, j) for j in jobs]):
            try:
                log(lp, fut.result())
            except Exception as e:  # keep the sweep going; the failed run is retried on the next call
                log(lp, f"FAILED: {type(e).__name__}: {e}")
    log(lp, f"finished; client stats {client.stats}")
    return 0


def _secondary(args, kind: str, work) -> int:
    """Shared driver for forks / replay / canary: one output file per main run, resumable, parallel."""
    cfg, spec = load_config(args.config)
    outdir = RESULTS / kind
    lp = outdir / "run_log.txt"
    if not wait_until_up(spec.base_url, timeout=args.wait):
        log(lp, "server did not come up")
        return 1
    client = LLMClient(spec, ROOT / cfg["cache"])
    jobs = [(c, s) for s in args.seeds for c in args.conditions]
    log(lp, f"start {len(jobs)} {kind} jobs from results/{args.src}")

    def one(job):
        cond, seed = job
        src, dst = RESULTS / args.src / f"{cond}-s{seed}.json", outdir / f"{cond}-s{seed}.json"
        if dst.exists():
            return f"{cond}-s{seed} skip"
        if not src.exists():
            return f"{cond}-s{seed} MISSING main run"
        t0 = time.time()
        res = json.loads(src.read_text(encoding="utf-8"))
        write_json(dst, work(res, client))
        return f"{cond}-s{seed} done in {time.time() - t0:.0f}s"

    with cf.ThreadPoolExecutor(max_workers=args.workers or cfg.get("workers", 8)) as ex:
        for fut in cf.as_completed([ex.submit(one, j) for j in jobs]):
            try:
                log(lp, fut.result())
            except Exception as e:
                log(lp, f"FAILED: {type(e).__name__}: {e}")
    log(lp, f"finished; client stats {client.stats}")
    return 0


def cmd_analyse(args) -> int:
    from . import analysis

    os.environ.setdefault("HUBSPOKE_OFFLINE", "1")  # analysis never calls the model
    numbers = analysis.analyse(RESULTS, args.src, args.lo, args.hi)
    lines = [analysis.table_markdown(numbers["summary"], numbers["tests"]), "",
             json.dumps(numbers.get("predictions", {}), default=float)]
    for key in ("replay", "canary", "forks", "detection"):
        if numbers.get(key):
            lines += ["", f"## {key}", json.dumps(numbers[key], default=float)[:4000]]
    (RESULTS / args.src / "analysis.txt").write_text("\n".join(lines), encoding="utf-8")
    return 0


def cmd_forks(args) -> int:
    return _secondary(args, "forks", lambda res, client: forks.fork_run(
        res, lambda rc: llm_agents(rc, client)))


def cmd_replay(args) -> int:
    return _secondary(args, "replay", lambda res, client: replay.replay_run(
        res, LLMAdvisor(client, res["config"]["temperature"])))


def cmd_livereplay(args) -> int:
    return _secondary(args, "livereplay", lambda res, client: replay.live_replay_run(
        res, LLMAdvisor(client, res["config"]["temperature"])))


def cmd_canary(args) -> int:
    return _secondary(args, "canary", lambda res, client: {"trials": canary.canary_trials(
        res, LLMAdvisor(client, res["config"]["temperature"]))})


ALL = ["solo", "chat", "isolated", "pooled", "aged", "aged_sharedmem", "portfolio"]  # pre-registered
# "separate" (conditions.py) is an exploratory control added after the main analysis; run it explicitly.
SECONDARY = {"forks": (cmd_forks, ["pooled", "isolated", "portfolio", "chat"]),
             "replay": (cmd_replay, ["isolated", "pooled", "aged", "aged_sharedmem"]),
             "canary": (cmd_canary, ["aged", "aged_sharedmem"]),
             "livereplay": (cmd_livereplay, ["pooled", "portfolio"])}  # exploratory, added after the analysis


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="hubspoke")
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("smoke", help="a 5-period pooled game against the live endpoint")
    s.add_argument("--config", default=str(ROOT / "configs" / "modal_qwen72b.json"))
    s.add_argument("--T", type=int, default=5)  # 5 periods x 4 decisions = the 20-call gate G0
    s.add_argument("--wait", type=float, default=1800)
    s.add_argument("--start", default="history", choices=["history", "nash", "none"])
    s.add_argument("--reasoning", action="store_true")
    sub.add_parser("validate", help="scripted agents with known answers (no model calls)")
    r = sub.add_parser("run", help="run conditions x seeds (resumes: finished runs are skipped)")
    r.add_argument("--config", default=str(ROOT / "configs" / "modal_qwen72b.json"))
    r.add_argument("--conditions", nargs="+", default=ALL)
    r.add_argument("--seeds", nargs="+", type=int, default=list(range(12)))
    r.add_argument("--T", type=int, default=40)
    r.add_argument("--out", default="main")
    r.add_argument("--wait", type=float, default=1800)
    r.add_argument("--workers", type=int, default=0, help="games run in parallel (0 = the config's value)")
    r.add_argument("--start", default="history", choices=["history", "nash", "none"])
    r.add_argument("--reasoning", action="store_true", help="agents write a short reasoning field first (D2)")
    r.add_argument("--blind", action="store_true", help="log health only, no outcomes (main run)")
    z = sub.add_parser("analyse", help="tables, tests, figures and numbers.json (no model calls)")
    z.add_argument("--src", default="main")
    z.add_argument("--lo", type=int, default=26)
    z.add_argument("--hi", type=int, default=40)
    v = sub.add_parser("verify", help="rebuild every result from the cache (offline) and recompute the numbers")
    v.add_argument("--src", default="main")
    handlers = {"smoke": cmd_smoke, "validate": cmd_validate, "run": cmd_run, "analyse": cmd_analyse,
                "verify": lambda a: __import__("hubspoke.verify", fromlist=["main"]).main([a.src])}
    for name, (fn, conds) in SECONDARY.items():
        x = sub.add_parser(name, help=f"{name} on the main runs (resumes)")
        x.add_argument("--config", default=str(ROOT / "configs" / "modal_qwen72b.json"))
        x.add_argument("--conditions", nargs="+", default=conds)
        x.add_argument("--seeds", nargs="+", type=int, default=list(range(12)))
        x.add_argument("--src", default="main")
        x.add_argument("--wait", type=float, default=1800)
        x.add_argument("--workers", type=int, default=0)
        handlers[name] = fn
    a = p.parse_args(argv)
    return handlers[a.cmd](a)
