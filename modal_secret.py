"""Create the API key for the vLLM server: store it in hubspoke/.env and in the Modal secret "hubspoke-vllm".
The key is generated locally and never printed. Run after `python -m modal setup`."""
import secrets
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ENV = HERE / ".env"
LOG = HERE / "modal_secret_log.txt"

lines = ENV.read_text(encoding="utf-8").splitlines() if ENV.exists() else []
existing = {ln.split("=", 1)[0]: ln.split("=", 1)[1] for ln in lines if "=" in ln}
key = existing.get("HUBSPOKE_API_KEY") or "hs-" + secrets.token_urlsafe(32)
if "HUBSPOKE_API_KEY" not in existing:
    lines.append(f"HUBSPOKE_API_KEY={key}")
    ENV.write_text("\n".join(lines) + "\n", encoding="utf-8")
r = subprocess.run([sys.executable, "-m", "modal", "secret", "create", "--force", "hubspoke-vllm", f"VLLM_API_KEY={key}"],
                   capture_output=True, text=True)
out = (r.stdout + r.stderr).replace(key, "<redacted>")
LOG.write_text(f"exit={r.returncode}\n{out}", encoding="utf-8")
