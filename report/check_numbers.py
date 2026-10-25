"""Check that every number in the report text traces to a result file or to a listed design constant. Prints the
numbers it cannot trace, for a human to look at (a derived number, such as a difference computed in the text, is
listed too and must be checked by hand).

    python report/check_numbers.py FILE            untraced numbers
    python report/check_numbers.py FILE --where    also: which result file each traced number comes from

Result files read: results/<folder>/{numbers,exploratory,round2,hub_check}.json, results/robust.json,
results/judge_validation.json, results/village/*.json."""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
R = ROOT / "results"
CONSTANTS = {  # design values stated in the method, not results
    "0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12", "13", "14", "15", "16", "20", "24", "25",
    "26", "27", "30", "35", "36", "40", "48", "60", "64", "84", "96", "100", "150", "250", "384", "0.25", "0.7",
    "1.473", "1.925", "3.2", "0.21.0", "2.5", "72", "70", "120", "2020", "2024", "2025", "2026", "0.5", "0.8",
    "0.15", "95", "-0.25", "1.25", "-0.75", "2.0", "1.0", "-1.00", "0.00", "-0.18", "-31.5", "0.02", "2.7", "0.6",
    "0.65", "0.75", "11,520", "11520", "1,152", "1152", "8,640", "8640", "4096",
}


def flatten(x, out, where, src):
    if isinstance(x, dict):
        for v in x.values():
            flatten(v, out, where, src)
    elif isinstance(x, (list, tuple)):
        for v in x:
            flatten(v, out, where, src)
    elif isinstance(x, bool) or x is None:
        return
    elif isinstance(x, (int, float)):
        out.add(float(x))
        where.setdefault(float(x), set()).add(src)


def forms(v: float) -> set[str]:
    s = set()
    for scale in (1, 100):
        y = v * scale
        for d in (0, 1, 2, 3, 4):
            for f in (f"{y:.{d}f}", f"{abs(y):.{d}f}", f"{y:+.{d}f}"):
                s.add(f)
    if v != 0:
        for f in (f"{v:.1e}", f"{v:.2e}", f"{v:.2g}", f"{v:.3g}"):
            s.add(f.replace("e-0", "e-"))
            s.add(f)
    return s


def result_files() -> list[Path]:
    files = []
    for name in ("numbers.json", "exploratory.json", "round2.json", "hub_check.json"):
        files += sorted(R.glob(f"*/{name}"))
    files += [p for p in (R / "robust.json", R / "judge_validation.json") if p.exists()]
    files += sorted((R / "village").glob("*.json"))
    return files


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    show_where = "--where" in sys.argv
    text = Path(args[0]).read_text(encoding="utf-8")
    text = re.sub(r"(?<=\d),(?=\d{3}\b)", "", text)  # 11,520 -> 11520
    vals: set[float] = set()
    where: dict[float, set[str]] = {}
    for p in result_files():
        flatten(json.loads(p.read_text(encoding="utf-8")), vals, where, str(p.relative_to(ROOT)))
    known: dict[str, set[str]] = {c: {"design constant"} for c in CONSTANTS}
    for v in vals:
        for f in forms(v):
            known.setdefault(f, set()).update(where[v])
    found = re.findall(r"(?<![\w.])[-+\u2212]?\d+(?:\.\d+)?(?:e-?\d+)?", text)
    found = [f.replace("\u2212", "-") for f in found]
    missing = sorted({f for f in found if f not in known and f.lstrip("+") not in known})
    print(f"{len(found)} numbers in the text; {len(set(found)) - len(missing)} distinct traced; {len(missing)} not traced:")
    for f in missing:
        print("  ", f)
    if show_where:
        print("\ntraced:")
        for f in sorted(set(found) - set(missing)):
            src = known.get(f) or known.get(f.lstrip("+")) or set()
            print(f"   {f}: {', '.join(sorted(src))[:160]}")


if __name__ == "__main__":
    main()
