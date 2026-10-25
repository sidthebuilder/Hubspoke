"""Replay runs offline with the code of an earlier commit and this repository's reply cache.

Pilot 1 (results/pilot) used the first design (one period 0 at the Nash price). The final code no longer renders
those prompts, so `python -m hubspoke verify --src pilot` reports cache misses; the runs replay exactly with the
code of commit 5e15448, the commit they were run with. scripts/replay_pilot1.ps1 exports that commit with
`git archive` (no change to .git) and calls this script.

    python scripts/replay_at_commit.py <exported code folder> <results subfolder> <commit>

Every model call must be answered from results/cache.sqlite (HUBSPOKE_OFFLINE=1, and the endpoint is a dummy
address); the replayed prices must equal the stored ones. Writes results/verify_<subfolder>.txt.
"""
import json
import os
import sys
from pathlib import Path

os.environ["HUBSPOKE_OFFLINE"] = "1"
REPO = Path(__file__).resolve().parents[1]
CODE, SUB, COMMIT = Path(sys.argv[1]), sys.argv[2], sys.argv[3]
sys.path.insert(0, str(CODE))  # the old package shadows nothing else: REPO is not on sys.path
from hubspoke.cli import llm_agents  # noqa: E402
from hubspoke.game import Game, RunConfig  # noqa: E402
from hubspoke.llm import LLMClient, ModelSpec  # noqa: E402

cfg = json.loads((CODE / "configs" / "modal_qwen72b.json").read_text(encoding="utf-8"))
m = dict(cfg["model"])
m.pop("base_url_env", None)
m["base_url"] = "http://offline.invalid"  # never contacted: a cache miss is an error
client = LLMClient(ModelSpec.from_dict(m), REPO / "results" / "cache.sqlite")
out, bad = [f"replayed with the code of commit {COMMIT} (scripts/replay_at_commit.py)"], 0
for p in sorted((REPO / "results" / SUB).glob("*-s*.json")):
    r = json.loads(p.read_text(encoding="utf-8"))
    rc = RunConfig(**r["config"])
    sellers, advisor = llm_agents(rc, client)
    g = Game(rc, sellers, advisor)
    try:
        g.run()
        same = [row["prices"] for row in g.log] == [row["prices"] for row in r["log"]]
        out.append(("ok   " if same else "FAIL ") + f"replay {p.stem}: {len(g.log)} periods rebuilt from cache")
        bad += 0 if same else 1
    except Exception as e:  # noqa: BLE001  a cache miss: the run file does not follow from the stored replies
        out.append(f"FAIL replay {p.stem}: {type(e).__name__}: {str(e)[:160]}")
        bad += 1
out.append(f"\n{bad} failure(s); client stats {getattr(client, 'stats', '')}")
(REPO / "results" / f"verify_{SUB}.txt").write_text("\n".join(out) + "\n", encoding="utf-8")
raise SystemExit(1 if bad else 0)
