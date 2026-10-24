"""Dev helper: one status file for the running round-2 jobs (progress, cache, hand sheets). Writes status_out.txt."""
import csv
import json
import sqlite3
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
R = HERE / "results"
out = [time.strftime("%Y-%m-%d %H:%M:%S")]

try:
    db = sqlite3.connect(str(R / "cache.sqlite"), timeout=60)
    ts = [json.loads(v)["ts"] for (v,) in db.execute("SELECT value FROM replies")]
    now = time.time()
    out.append(f"cache replies {len(ts)}; last 60 s: {sum(1 for t in ts if t > now - 60)}; "
               f"last 10 min: {sum(1 for t in ts if t > now - 600)}; newest {now - max(ts):.0f} s ago")
except Exception as e:  # noqa: BLE001
    out.append(f"cache: {e!r}")

for name in ["startlow", "startlow_llama", "canary2", "canary2_llama", "main_gptoss", "canary2_gptoss"]:
    d = R / name
    if not d.exists():
        out.append(f"{name}: (no folder)")
        continue
    files = [p for p in d.glob("*.json")]
    log = (d / "run_log.txt").read_text(encoding="utf-8").strip().splitlines() if (d / "run_log.txt").exists() else []
    out.append(f"{name}: {len(files)} json; log tail: {log[-1] if log else ''}")

for sheet in ["handcheck.csv", "handcheck_canary.csv"]:
    p = R / sheet
    if p.exists():
        rows = list(csv.reader(p.open(encoding="utf-8")))[1:]
        out.append(f"{sheet}: rows {len(rows)}, filled {sum(1 for r in rows if r and r[-1].strip())}")

sl = R / "smoke_log.txt"
if sl.exists():
    out.append("smoke: " + sl.read_text(encoding="utf-8").strip().splitlines()[-1][:300])

(HERE / "status_out.txt").write_text("\n".join(out) + "\n", encoding="utf-8")
