"""vLLM OpenAI-compatible server for the experiments, on one Modal GPU (adapted from Modal's vllm_inference example).

Deploy:  modal deploy modal_serve.py      (prints the server URL; set HUBSPOKE_GPU to change the GPU type)
The endpoint needs the bearer key stored in the Modal secret "hubspoke-vllm" (env VLLM_API_KEY, read by vLLM);
the same key is in hubspoke/.env as HUBSPOKE_API_KEY. /health is open, so a client can wait for cold starts.
"""
import os

import modal

GPU = os.environ.get("HUBSPOKE_GPU", "H100:1")  # read at deploy time; every run uses the one GPU type
# Main model: ungated, 4-bit AWQ, about 42 GB of weights. A second model is deployed as a separate app by
# setting HUBSPOKE_MODEL / HUBSPOKE_REVISION / HUBSPOKE_SERVED / HUBSPOKE_APP before `modal deploy`; the values
# are passed into the container through `env`, so the container serves the same model the deploy named.
MODEL_NAME = os.environ.get("HUBSPOKE_MODEL", "Qwen/Qwen2.5-72B-Instruct-AWQ")
MODEL_REVISION = os.environ.get("HUBSPOKE_REVISION", "698703eae6604af048a3d2f509995dc302088217")  # pinned HF commit
SERVED_NAME = os.environ.get("HUBSPOKE_SERVED", "hubspoke-qwen72b")
APP_NAME = os.environ.get("HUBSPOKE_APP", "hubspoke-vllm")
VLLM_VERSION = "0.21.0"
MINUTES = 60
PORT = 8000

image = (
    modal.Image.from_registry("nvidia/cuda:12.9.0-devel-ubuntu22.04", add_python="3.12")
    .entrypoint([])
    .uv_pip_install(f"vllm=={VLLM_VERSION}")
    .env({"HF_XET_HIGH_PERFORMANCE": "1"})
)
hf_cache = modal.Volume.from_name("huggingface-cache", create_if_missing=True)
vllm_cache = modal.Volume.from_name("vllm-cache", create_if_missing=True)
app = modal.App(APP_NAME)


@app.server(
    image=image,
    gpu=GPU,
    scaledown_window=10 * MINUTES,  # shut down 10 minutes after the last request (stops billing)
    startup_timeout=25 * MINUTES,  # first boot downloads the weights into the volume
    volumes={"/root/.cache/huggingface": hf_cache, "/root/.cache/vllm": vllm_cache},
    secrets=[modal.Secret.from_name("hubspoke-vllm")],
    env={"HUBSPOKE_MODEL": MODEL_NAME, "HUBSPOKE_REVISION": MODEL_REVISION, "HUBSPOKE_SERVED": SERVED_NAME,
         "HUBSPOKE_APP": APP_NAME},
    port=PORT,
    target_concurrency=64,
    unauthenticated=True,  # Modal-level auth off; vLLM itself requires the bearer key on /v1
)
class Server:
    @modal.enter()
    def start(self):
        import subprocess

        cmd = ["vllm", "serve", MODEL_NAME, "--revision", MODEL_REVISION, "--served-model-name", SERVED_NAME,
               "--host", "0.0.0.0", "--port", str(PORT), "--max-model-len", "8192",
               "--gpu-memory-utilization", "0.92", "--max-num-seqs", "64", "--generation-config", "vllm",
               "--uvicorn-log-level=warning"]
        print("starting:", " ".join(cmd))  # the API key comes from the VLLM_API_KEY env var and is never printed
        self.process = subprocess.Popen(cmd)

    @modal.exit()
    def stop(self):
        self.process.terminate()
