"""Dev helper: which registered runs of a folder are not on disk yet (names only, no outcomes). Writes
missing_runs_out.txt. Usage: python missing_runs.py main_gptoss"""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]  # the repository folder (this script is one level down)
folder = sys.argv[1] if len(sys.argv) > 1 else "main_gptoss"
conds = ["solo", "chat", "isolated", "pooled", "aged", "aged_sharedmem", "portfolio"]
have = {p.stem for p in (HERE / "results" / folder).glob("*-s*.json")}
missing = [f"{c}-s{s}" for c in conds for s in range(12) if f"{c}-s{s}" not in have]
(HERE / "missing_runs_out.txt").write_text(f"{folder}: {len(have)} on disk; missing {missing}\n", encoding="utf-8")
