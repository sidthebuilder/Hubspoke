"""Dev check: no secret from .env appears in any file git tracks or would add. Prints file names only, never values.
Writes secret_scan_out.txt."""
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]  # the repository folder (this script is one level down)
secrets = {}
for line in (HERE / ".env").read_text(encoding="utf-8").splitlines():
    if "=" in line and not line.lstrip().startswith("#"):
        k, v = line.split("=", 1)
        v = v.strip().strip('"').strip("'")
        if "KEY" in k.upper() or "TOKEN" in k.upper() or "SECRET" in k.upper():
            if len(v) >= 8:
                secrets[k.strip()] = v
tracked = subprocess.run(["git", "ls-files"], cwd=HERE, capture_output=True, text=True).stdout.splitlines()
untracked = subprocess.run(["git", "ls-files", "--others", "--exclude-standard"], cwd=HERE, capture_output=True,
                           text=True).stdout.splitlines()
hits = []
for rel in tracked + untracked:
    p = HERE / rel
    try:
        data = p.read_bytes()
    except OSError:
        continue
    if rel.endswith(".gz"):
        import gzip

        try:
            data = gzip.decompress(data)
        except OSError:
            pass
    for name, v in secrets.items():
        if v.encode() in data:
            hits.append(f"{rel}: contains {name}")
out = [f"secrets checked: {sorted(secrets)}", f"files scanned: {len(tracked)} tracked, {len(untracked)} untracked "
       f"(not ignored)", f"hits: {len(hits)}"] + hits
(HERE / "secret_scan_out.txt").write_text("\n".join(out) + "\n", encoding="utf-8")
