"""Dev helper: cached replies per model, and the gpt-oss reply rate over the last 10 minutes. Writes
cache_by_model_out.txt."""
import collections
import json
import sqlite3
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
db = sqlite3.connect(str(HERE / "results" / "cache.sqlite"), timeout=60)
by, recent, ct = collections.Counter(), collections.Counter(), collections.Counter()
now = time.time()
for (v,) in db.execute("SELECT value FROM replies"):
    d = json.loads(v)
    m = d.get("model", "?")
    by[m] += 1
    ct[m] += d.get("ct", 0)
    if d.get("ts", 0) > now - 600:
        recent[m] += 1
lines = [time.strftime("%H:%M:%S")] + [f"{m}: {n} replies, {ct[m] / max(n, 1):.0f} completion tokens per reply, "
                                       f"last 10 min {recent[m]}" for m, n in by.most_common()]
(HERE / "cache_by_model_out.txt").write_text("\n".join(lines) + "\n", encoding="utf-8")
