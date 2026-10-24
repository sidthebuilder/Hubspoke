"""Deploy modal_serve.py and record the server URL in hubspoke/.env as HUBSPOKE_BASE_URL (with /v1)."""
import os
import re
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ENV = HERE / ".env"
LOG = HERE / "modal_deploy_log.txt"
# Modal prints symbols such as a check mark; Windows' default console code page cannot encode them.
env = {**os.environ, "PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1"}
r = subprocess.run([sys.executable, "-m", "modal", "deploy", str(HERE / "modal_serve.py")],
                   capture_output=True, text=True, encoding="utf-8", errors="replace", cwd=str(HERE), env=env)
out = r.stdout + r.stderr
urls = re.findall(r"https://[\w.-]+\.modal\.(?:run|direct)[\w/.-]*", out)
url = urls[-1].rstrip("/") if urls else ""
if url:
    lines = [ln for ln in (ENV.read_text(encoding="utf-8").splitlines() if ENV.exists() else [])
             if not ln.startswith("HUBSPOKE_BASE_URL=")]
    lines.append(f"HUBSPOKE_BASE_URL={url}/v1")
    ENV.write_text("\n".join(lines) + "\n", encoding="utf-8")
LOG.write_text(f"exit={r.returncode}\nurl={url}\n\n{out[-6000:]}", encoding="utf-8")
