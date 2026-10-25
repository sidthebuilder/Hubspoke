"""Check which packages import in this venv (Windows Application Control can block new DLLs)."""
import importlib
from importlib import metadata
from pathlib import Path

out = []
for name in ("numpy", "scipy", "scipy.stats", "matplotlib", "matplotlib.pyplot", "PIL.Image", "pandas", "pytest", "modal"):
    try:
        importlib.import_module(name)
        out.append(f"OK   {name}")
    except Exception as e:  # report and continue
        out.append(f"FAIL {name}: {type(e).__name__}: {str(e)[:160]}")
for dist in ("numpy", "scipy", "matplotlib", "pillow", "pandas", "pytest", "modal", "fonttools", "contourpy", "kiwisolver"):
    try:
        out.append(f"{dist}=={metadata.version(dist)}")
    except Exception:
        out.append(f"{dist} not installed")
(Path(__file__).resolve().parents[1] / "imports_log.txt").write_text("\n".join(out), encoding="utf-8")
