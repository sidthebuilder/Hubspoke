"""Dev helper: number of cached replies and the newest timestamps (progress of a running sweep)."""
import json
import sqlite3
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
db = sqlite3.connect(str(HERE / "results" / "cache.sqlite"), timeout=60)
rows = db.execute("SELECT value FROM replies").fetchall()
ts = sorted(json.loads(v)["ts"] for (v,) in rows)
now = time.time()
recent = sum(1 for t in ts if t > now - 60)
(HERE / "cache_count_out.txt").write_text(
    f"{time.strftime('%H:%M:%S')} replies {len(ts)}; in the last 60 s: {recent}; newest {now - ts[-1]:.0f} s ago\n",
    encoding="utf-8")
