"""Command line: smoke | validate | run. Every command writes its output under results/."""
from __future__ import annotations

import argparse
import concurrent.futures as cf
import json
import os
import time
from pathlib import Path

from . import scripted
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


def llm_game(rc: RunConfig, client) -> Game:
    sellers = [LLMSeller(client, rc.temperature) for _ in range(rc.n)]
    advisor = LLMAdvisor(client, rc.temperature) if get_condition(rc.condition).advisor else None
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
    g = llm_game(RunConfig("pooled", seed=99, T=args.T, temperature=cfg["temperature"]), client)
    g.run()
    res = g.result()
    calls, bad = parse_stats(res)
    write_json(RESULTS / "smoke.json", res)
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
               "period 2, aged from period 13")
    (RESULTS / "validate.txt").parent.mkdir(parents=True, exist_ok=True)
    (RESULTS / "validate.txt").write_text("\n".join(out), encoding="utf-8")
    return 0


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
        g = llm_game(RunConfig(cond, seed=seed, T=args.T, temperature=cfg["temperature"]), client)
        g.run()
        res = g.result()
        res["model_note"] = cfg.get("model_note", "")
        write_json(path, res)
        calls, bad = parse_stats(res)
        tail = res["price_index"][-15:]
        return (f"{cond}-s{seed} done in {time.time() - t0:.0f}s; index(last 15) {sum(tail) / len(tail):+.3f}; "
                f"unreadable {bad}/{calls}")

    with cf.ThreadPoolExecutor(max_workers=cfg.get("workers", 8)) as ex:
        for fut in cf.as_completed([ex.submit(one, j) for j in jobs]):
            try:
                log(lp, fut.result())
            except Exception as e:  # keep the sweep going; the failed run is retried on the next call
                log(lp, f"FAILED: {type(e).__name__}: {e}")
    log(lp, f"finished; client stats {client.stats}")
    return 0


ALL = ["solo", "chat", "isolated", "pooled", "aged", "aged_sharedmem", "portfolio"]


def main(argv=None) -> int:
    p = argparse.ArgumentParser(prog="hubspoke")
    sub = p.add_subparsers(dest="cmd", required=True)
    s = sub.add_parser("smoke", help="a 3-period pooled game against the live endpoint")
    s.add_argument("--config", default=str(ROOT / "configs" / "modal_qwen72b.json"))
    s.add_argument("--T", type=int, default=3)
    s.add_argument("--wait", type=float, default=1800)
    sub.add_parser("validate", help="scripted agents with known answers (no model calls)")
    r = sub.add_parser("run", help="run conditions x seeds (resumes: finished runs are skipped)")
    r.add_argument("--config", default=str(ROOT / "configs" / "modal_qwen72b.json"))
    r.add_argument("--conditions", nargs="+", default=ALL)
    r.add_argument("--seeds", nargs="+", type=int, default=list(range(6)))
    r.add_argument("--T", type=int, default=40)
    r.add_argument("--out", default="main")
    r.add_argument("--wait", type=float, default=1800)
    a = p.parse_args(argv)
    return {"smoke": cmd_smoke, "validate": cmd_validate, "run": cmd_run}[a.cmd](a)
