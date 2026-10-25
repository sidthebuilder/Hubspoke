"""Dev check: for every file whose staged or working copy differs from HEAD, say whether the difference is only line
endings (CRLF vs LF). Writes git_eol_out.txt."""
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent


def git(*a, binary=False):
    r = subprocess.run(["git", *a], cwd=HERE, capture_output=True)
    return r.stdout if binary else r.stdout.decode("utf-8", "replace")


status = [line for line in git("status", "--porcelain").splitlines() if line and not line.startswith("??")]
out = []
for line in status:
    rel = line[3:].strip().strip('"')
    head = git("show", f"HEAD:{rel}", binary=True)
    index = git("show", f":{rel}", binary=True)
    try:
        work = (HERE / rel).read_bytes()
    except OSError:
        work = b""
    norm = lambda b: b.replace(b"\r\n", b"\n")  # noqa: E731
    kind = []
    kind.append("head CRLF" if b"\r\n" in head else "head LF")
    kind.append("index CRLF" if b"\r\n" in index else "index LF")
    kind.append("work CRLF" if b"\r\n" in work else "work LF")
    same = norm(head) == norm(index) == norm(work)
    out.append(f"{line[:2]} {rel}: {'line endings only' if same else 'CONTENT DIFFERS'} ({', '.join(kind)})")
(HERE / "git_eol_out.txt").write_text("\n".join(out) + "\n", encoding="utf-8")
