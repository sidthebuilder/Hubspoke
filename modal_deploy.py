"""Deploy modal_serve.py and record the server URL in hubspoke/.env as HUBSPOKE_BASE_URL (with /v1)."""
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ENV = HERE / ".env"
LOG = HERE / "modal_deploy_log.txt"
r = subprocess.run([sys.executable, "-m", "modal", "deploy", str(HERE / "modal_serve.py")],
                   capture_output=True, text=True, cwd=str(HERE))
out = r.stdout + r.stderr
urls = re.findall(r"https://[\w.-]+\.modal\.(?:run|direct)[\w/.-]*", out)
url = urls[-1].rstrip("/") if urls else ""
if url:
    lines = [ln for ln in (ENV.read_text(encoding="utf-8").splitlines() if ENV.exists() else [])
             if not ln.startswith("HUBSPOKE_BASE_URL=")]
    lines.append(f"HUBSPOKE_BASE_URL={url}/v1")
    ENV.write_text("\n".join(lines) + "\n", encoding="utf-8")
LOG.write_text(f"exit={r.returncode}\nurl={url}\n\n{out[-6000:]}", encoding="utf-8")
