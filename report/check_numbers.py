"""Check that every number in the report text traces to results/main/numbers.json or to a listed design
constant. Prints numbers it cannot trace, for a human to look at. Usage: python report/check_numbers.py FILE"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CONSTANTS = {  # design values stated in the method, not results
    "0", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10", "11", "12", "13", "14", "15", "16", "20", "24", "25",
    "26", "27", "30", "35", "36", "40", "48", "60", "64", "84", "100", "150", "250", "0.25", "0.7", "1.473",
    "1.925", "3.2", "0.21.0", "2.5", "72", "2020", "2024", "2025", "2026", "0.5", "0.8", "0.15", "95", "-0.25",
    "1.25", "2.0", "1.0", "-1.00", "0.00", "-0.18", "-31.5", "0.02", "2.7",
}


def flatten(x, out):
    if isinstance(x, dict):
        for v in x.values():
            flatten(v, out)
    elif isinstance(x, (list, tuple)):
        for v in x:
            flatten(v, out)
    elif isinstance(x, bool) or x is None:
        return
    elif isinstance(x, (int, float)):
        out.add(float(x))


def forms(v: float) -> set[str]:
    s = set()
    for scale in (1, 100):
        y = v * scale
        for d in (0, 1, 2, 3):
            s.add(f"{y:.{d}f}")
            s.add(f"{abs(y):.{d}f}")
            s.add(f"{y:+.{d}f}")
    return s


def main():
    text = Path(sys.argv[1]).read_text(encoding="utf-8")
    numbers = json.loads((ROOT / "results" / "main" / "numbers.json").read_text(encoding="utf-8"))
    vals: set[float] = set()
    flatten(numbers, vals)
    known = set(CONSTANTS)
    for v in vals:
        known |= forms(v)
    found = re.findall(r"(?<![\w.])[-+]?\d+(?:\.\d+)?", text)
    missing = sorted({f for f in found if f not in known and f.lstrip("+") not in known})
    print(f"{len(found)} numbers in the text; {len(missing)} not traced:")
    for f in missing:
        print("  ", f)


if __name__ == "__main__":
    main()
