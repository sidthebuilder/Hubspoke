"""Move the reply cache in and out of git as a compressed text file.

    python cache_io.py export   results/cache.sqlite  -> results/cache.jsonl.gz  (one line per reply)
    python cache_io.py import   results/cache.jsonl.gz -> results/cache.sqlite   (after cloning the repo)

The SQLite file itself is not committed (binary, about 50 MB); the export is the committed source of truth."""
import gzip
import json
import sqlite3
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
DB, GZ = HERE / "results" / "cache.sqlite", HERE / "results" / "cache.jsonl.gz"


def export() -> int:
    db = sqlite3.connect(str(DB), timeout=60)
    db.execute("PRAGMA wal_checkpoint(TRUNCATE)")
    rows = db.execute("SELECT key, value FROM replies ORDER BY key").fetchall()
    db.close()
    with gzip.open(GZ, "wt", encoding="utf-8") as fh:
        for k, v in rows:
            fh.write(json.dumps({"key": k, "value": json.loads(v)}, sort_keys=True) + "\n")
    print(f"exported {len(rows)} replies to {GZ} ({GZ.stat().st_size / 1e6:.1f} MB)")
    return 0


def import_() -> int:
    db = sqlite3.connect(str(DB), timeout=60)
    db.execute("CREATE TABLE IF NOT EXISTS replies (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
    n = 0
    with gzip.open(GZ, "rt", encoding="utf-8") as fh:
        for line in fh:
            d = json.loads(line)
            db.execute("INSERT OR REPLACE INTO replies (key, value) VALUES (?, ?)", (d["key"], json.dumps(d["value"])))
            n += 1
    db.commit()
    db.close()
    print(f"imported {n} replies into {DB}")
    return 0


if __name__ == "__main__":
    raise SystemExit({"export": export, "import": import_}[sys.argv[1]]())
