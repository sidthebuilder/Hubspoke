"""Chat-completion backends (Ollama, or any OpenAI-compatible API) behind one persistent cache.

Every reply is stored under a hash of the model, the messages, the sampling settings and a sample key. Re-running
an experiment replays identical replies without network calls, and anyone with the cache file can rebuild every
result without an API key. Keys are read from environment variables named in the config, never stored or logged.
"""
from __future__ import annotations

import dataclasses
import hashlib
import http.client
import json
import os
import random
import sqlite3
import sys
import threading
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from pathlib import Path

_RETRYABLE = {408, 409, 425, 429, 500, 502, 503, 504}


class LLMError(RuntimeError):
    """A failure that retrying will not fix: unknown model, missing key, rejected request."""


class _Retry(Exception):
    def __init__(self, msg: str, retry_after: float | None = None):
        super().__init__(msg)
        self.retry_after = retry_after


class _HTTPFail(Exception):
    def __init__(self, code: int, detail: str):
        super().__init__(f"HTTP {code}: {detail}")
        self.code, self.detail = code, detail


@dataclass(frozen=True)
class ModelSpec:
    backend: str  # "ollama", or "openai" for any OpenAI-compatible /chat/completions endpoint
    model: str
    base_url: str = ""
    api_key_env: str = ""  # NAME of the environment variable that holds the key
    json_mode: bool = True
    num_ctx: int = 8192  # Ollama context window; its default is too small for the advisor prompts
    timeout: float = 180.0
    max_retries: int = 6

    @staticmethod
    def from_dict(d: dict) -> "ModelSpec":
        return ModelSpec(**{k: v for k, v in d.items() if k in ModelSpec.__dataclass_fields__})

    @property
    def label(self) -> str:
        return f"{self.backend}:{self.model}"


@dataclass
class Completion:
    text: str
    prompt_tokens: int = 0
    completion_tokens: int = 0
    cached: bool = False
    seconds: float = 0.0


class Cache:
    """Thread-safe SQLite store of replies."""

    def __init__(self, path: str | Path):
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        self._lock = threading.Lock()
        # timeout: several processes (e.g. two pilots) may write to the same cache file
        self._db = sqlite3.connect(str(path), check_same_thread=False, timeout=60)
        with self._lock:
            self._db.execute("PRAGMA journal_mode=WAL")
            self._db.execute("CREATE TABLE IF NOT EXISTS replies (key TEXT PRIMARY KEY, value TEXT NOT NULL)")
            self._db.commit()

    def get(self, key: str) -> dict | None:
        with self._lock:
            row = self._db.execute("SELECT value FROM replies WHERE key = ?", (key,)).fetchone()
        return None if row is None else json.loads(row[0])

    def put(self, key: str, value: dict) -> None:
        with self._lock:
            self._db.execute("INSERT OR REPLACE INTO replies (key, value) VALUES (?, ?)", (key, json.dumps(value)))
            self._db.commit()

    def close(self) -> None:
        with self._lock:
            self._db.close()


def _seed(sample_key: str) -> int:
    return int(hashlib.sha256(sample_key.encode("utf-8")).hexdigest()[:8], 16) % (2**31 - 1)


def load_env(path: str | Path) -> None:
    """Read KEY=VALUE lines from a .env file into os.environ (values are never printed)."""
    p = Path(path)
    if not p.exists():
        return
    for line in p.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if line and not line.startswith("#") and "=" in line:
            k, v = line.split("=", 1)
            os.environ.setdefault(k.strip(), v.strip().strip('"').strip("'"))


class LLMClient:
    """OpenAI-compatible /chat/completions client with a persistent reply cache.

    Set HUBSPOKE_OFFLINE=1 to forbid network calls (rebuild results from the cache only)."""

    def __init__(self, spec: ModelSpec, cache_path: str | Path):
        if spec.backend != "openai":
            raise LLMError(f"unsupported backend {spec.backend!r}; use an OpenAI-compatible endpoint")
        self.spec = spec
        self.cache = Cache(cache_path)
        self._json_ok = spec.json_mode
        self._lock = threading.Lock()
        self.stats = {"calls": 0, "cached": 0, "prompt_tokens": 0, "completion_tokens": 0, "retries": 0}

    def _key(self, messages, temperature, max_tokens, sample_key) -> str:
        blob = json.dumps({"model": self.spec.model, "messages": messages, "temperature": temperature,
                           "max_tokens": max_tokens, "sample_key": sample_key}, sort_keys=True)
        return hashlib.sha256(blob.encode("utf-8")).hexdigest()

    def complete(self, messages, temperature: float = 0.7, max_tokens: int = 250, sample_key: str = "") -> Completion:
        key = self._key(messages, temperature, max_tokens, sample_key)
        hit = self.cache.get(key)
        if hit is not None:
            with self._lock:
                self.stats["cached"] += 1
            return Completion(hit["text"], hit.get("pt", 0), hit.get("ct", 0), cached=True)
        if os.environ.get("HUBSPOKE_OFFLINE") == "1":
            raise LLMError("cache miss while HUBSPOKE_OFFLINE=1")
        t0 = time.time()
        text, pt, ct = self._post(messages, temperature, max_tokens, _seed(sample_key))
        self.cache.put(key, {"text": text, "pt": pt, "ct": ct, "model": self.spec.model, "ts": round(time.time())})
        with self._lock:
            self.stats["calls"] += 1
            self.stats["prompt_tokens"] += pt
            self.stats["completion_tokens"] += ct
        return Completion(text, pt, ct, cached=False, seconds=time.time() - t0)

    def _post(self, messages, temperature, max_tokens, seed):
        url = self.spec.base_url.rstrip("/") + "/chat/completions"
        headers = {"Content-Type": "application/json"}
        key = os.environ.get(self.spec.api_key_env, "") if self.spec.api_key_env else ""
        if self.spec.api_key_env and not key:
            raise LLMError(f"environment variable {self.spec.api_key_env} is not set (put it in hubspoke/.env)")
        if key:
            headers["Authorization"] = f"Bearer {key}"
        for attempt in range(self.spec.max_retries + 1):
            body = {"model": self.spec.model, "messages": messages, "temperature": temperature,
                    "max_tokens": max_tokens, "seed": seed}
            if self._json_ok:
                body["response_format"] = {"type": "json_object"}
            req = urllib.request.Request(url, data=json.dumps(body).encode("utf-8"), headers=headers, method="POST")
            try:
                with urllib.request.urlopen(req, timeout=self.spec.timeout) as r:
                    d = json.load(r)
                text = (d["choices"][0]["message"].get("content") or "").strip()
                u = d.get("usage") or {}
                return text, int(u.get("prompt_tokens") or 0), int(u.get("completion_tokens") or 0)
            except urllib.error.HTTPError as e:
                detail = e.read()[:400].decode("utf-8", "replace")
                if e.code == 400 and self._json_ok and ("response_format" in detail or "json" in detail.lower()):
                    self._json_ok = False  # endpoint rejects JSON mode: fall back to plain text
                    continue
                if e.code not in _RETRYABLE:
                    raise LLMError(f"HTTP {e.code}: {detail}") from None
                wait = float(e.headers.get("Retry-After") or 0) or min(60.0, 2.0 ** attempt)
            except (urllib.error.URLError, TimeoutError, http.client.HTTPException, ConnectionError, OSError):
                wait = min(60.0, 2.0 ** attempt)
            with self._lock:
                self.stats["retries"] += 1
            time.sleep(wait + random.random())
        raise LLMError(f"gave up after {self.spec.max_retries + 1} attempts: {url}")


def wait_until_up(base_url: str, timeout: float = 900.0) -> bool:
    """Poll {server}/health until a cold-started server answers (vLLM on Modal can take minutes)."""
    root = base_url.rstrip("/")
    root = root[:-3] if root.endswith("/v1") else root
    end = time.time() + timeout
    while time.time() < end:
        try:
            with urllib.request.urlopen(root + "/health", timeout=60) as r:
                if r.status == 200:
                    return True
        except Exception:  # 503 while booting, or not reachable yet
            pass
        time.sleep(5)
    return False
