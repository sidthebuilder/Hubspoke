"""Gate G1 for a pilot folder, as pre-registered: readable >= 95%, portfolio >= 0.2, solo <= 0.7, using the mean
price index over periods 11-15 averaged over seeds (the 1-15 mean is shown too). Writes results/<folder>/gate.txt."""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]  # the repository folder (this script is one level down)
folder = HERE / "results" / sys.argv[1]
rows, ok = {}, [0, 0]
for p in sorted(folder.glob("*-s*.json")):
    r = json.loads(p.read_text(encoding="utf-8"))
    c = r["config"]["condition"]
    idx = r["price_index"]
    rows.setdefault(c, []).append((r["config"]["seed"], sum(idx[10:15]) / 5, sum(idx) / len(idx)))
    for row in r["log"]:
        for a in row["advisor"] + [s for s in row["sellers"] if not s["forced"]]:
            ok[1] += 1
            ok[0] += 1 if a["ok"] else 0
out = [f"{folder.name}: readable {ok[0]}/{ok[1]} = {ok[0] / ok[1]:.3f}"]
level = {}
for c in ["solo", "chat", "isolated", "pooled", "aged", "aged_sharedmem", "portfolio"]:
    if c in rows:
        xs = rows[c]
        level[c] = sum(x[1] for x in xs) / len(xs)
        out.append(f"  {c:15s} 11-15 mean {level[c]:+.3f}   1-15 mean {sum(x[2] for x in xs) / len(xs):+.3f}   per seed "
                   + "  ".join(f"s{s}: {a:+.3f}/{b:+.3f}" for s, a, b in xs))
g = {"readable": ok[0] / ok[1] >= 0.95, "portfolio": level.get("portfolio", -9) >= 0.2, "solo": level.get("solo", 9) <= 0.7}
out.append("G1 " + ("PASS" if all(g.values()) else "FAIL") + " " + str(g))
(folder / "gate.txt").write_text("\n".join(out), encoding="utf-8")
