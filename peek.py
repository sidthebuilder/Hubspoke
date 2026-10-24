"""Print a compact view of finished runs (prices, recommendations, notes) to peek_out.txt. Dev helper only."""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
folder = HERE / "results" / (sys.argv[1] if len(sys.argv) > 1 else "pilot")
show = sys.argv[2:]  # optional run ids to print in full
out = []
for p in sorted(folder.glob("*-s*.json")):
    r = json.loads(p.read_text(encoding="utf-8"))
    a = r["alpha"]
    idx = r["price_index"]
    out.append(f"{p.stem:22s} alpha {a:4.1f}  index by period: " + " ".join(f"{x:+.2f}" for x in idx))
    if p.stem in show:
        for row in r["log"]:
            recs = "" if not any(x is not None for x in row["recs"]) else " recs " + str([None if x is None else round(x / a, 3) for x in row["recs"]])
            out.append(f"   t{row['t']:>2} prices/alpha {[round(x / a, 3) for x in row['prices']]}{recs}")
            for s in row["sellers"]:
                out.append(f"       seller {'AB'[s['firm']]} plan: {s['plan'][:150]}" + (f" | msg: {s['message'][:150]}" if s['message'] else ""))
            for ad in row["advisor"]:
                out.append(f"       advisor->{'AB'[ad['firm']]} note: {ad['note'][:150]} | memo: {ad['memo'][:150]}")
(HERE / "peek_out.txt").write_text("\n".join(out), encoding="utf-8")
