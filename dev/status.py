"""Dev helper: one status file for the running round-2 jobs (progress, cache, hand sheets). Writes status_out.txt.
Every section is guarded, so a locked file (for example a sheet open in Excel) cannot stop the report."""
import csv
import json
import sys
import sqlite3
import time
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]  # the repository folder (this script is one level down)
sys.path.insert(0, str(HERE))  # for hubspoke.judge
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
    try:
        d = R / name
        if not d.exists():
            out.append(f"{name}: (no folder)")
            continue
        files = list(d.glob("*-s*.json"))
        log = (d / "run_log.txt").read_text(encoding="utf-8").strip().splitlines() if (d / "run_log.txt").exists() else []
        out.append(f"{name}: {len(files)} run files; log tail: {log[-1] if log else ''}")
    except Exception as e:  # noqa: BLE001
        out.append(f"{name}: {e!r}")

for sheet in ["handcheck.csv", "handcheck_canary.csv"]:
    try:
        from hubspoke.judge import read_sheet

        p = R / sheet
        if p.exists():
            labels = read_sheet(p)
            out.append(f"{sheet}: rows {len(labels)}, filled {sum(1 for v in labels.values() if v in ('0', '1'))}")
    except Exception as e:  # noqa: BLE001
        out.append(f"{sheet}: {e!r} (open in a spreadsheet?)")

try:
    chain = (HERE / "chain_gptoss_log.txt").read_text(encoding="utf-8").strip().splitlines()
    out.append("chain: " + (chain[-1] if chain else ""))
except Exception as e:  # noqa: BLE001
    out.append(f"chain: {e!r}")

(HERE / "status_out.txt").write_text("\n".join(out) + "\n", encoding="utf-8")
