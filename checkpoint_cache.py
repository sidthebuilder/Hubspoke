"""Merge the SQLite write-ahead log into results/cache.sqlite (run when no experiment is writing), so the single
file holds every reply before it is committed. Prints the reply count and the file size."""
import sqlite3
from pathlib import Path

HERE = Path(__file__).resolve().parent
path = HERE / "results" / "cache.sqlite"
db = sqlite3.connect(str(path), timeout=60)
db.execute("PRAGMA wal_checkpoint(TRUNCATE)")
n = db.execute("SELECT COUNT(*) FROM replies").fetchone()[0]
db.close()
(HERE / "checkpoint_out.txt").write_text(f"replies {n}; {path.stat().st_size / 1e6:.1f} MB\n", encoding="utf-8")
