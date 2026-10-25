"""Dev helper: write the village-wide goals with their dates to village_out/village_goals.txt (not committed)."""
import gzip
import json
from pathlib import Path

HERE = Path(__file__).resolve().parent
DATA = HERE.parents[1] / "data"
rows = [json.loads(x) for x in gzip.open(DATA / "village_goals.jsonl.gz", "rt", encoding="utf-8")]
rows.sort(key=lambda r: r.get("start_time") or "")
out = [f"{r.get('start_time')} -> {r.get('end_time')}: {r.get('goal')}" for r in rows]
(HERE / "village_out").mkdir(exist_ok=True)
(HERE / "village_out" / "village_goals.txt").write_text("\n".join(out), encoding="utf-8")
