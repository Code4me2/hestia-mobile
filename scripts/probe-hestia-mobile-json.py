#!/usr/bin/env python3
"""Structured Hestia Mobile health probe.

The probe is dependency-free and safe to run on the phone. It emits JSON for
issue templates, CI artifacts, and compatibility matrix updates.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import socket
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat().replace("+00:00", "Z")


def load_config(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text())


def http_json(url: str, timeout: float) -> dict[str, Any]:
    with urllib.request.urlopen(url, timeout=timeout) as resp:
        body = resp.read().decode("utf-8", errors="replace")
        return {"ok": 200 <= resp.status < 300, "status_code": resp.status, "json": json.loads(body)}


def check_http_json(url: str, timeout: float) -> dict[str, Any]:
    try:
        result = http_json(url, timeout)
        return {"status": "pass" if result["ok"] else "fail", **result}
    except (urllib.error.URLError, TimeoutError, OSError, json.JSONDecodeError) as e:
        return {"status": "fail", "error": f"{type(e).__name__}: {e}"}


def run_cmd(args: list[str], timeout: float = 5.0) -> dict[str, Any]:
    try:
        proc = subprocess.run(args, text=True, capture_output=True, timeout=timeout)
        return {
            "status": "pass" if proc.returncode == 0 else "fail",
            "returncode": proc.returncode,
            "stdout": proc.stdout.strip(),
            "stderr": proc.stderr.strip(),
        }
    except (OSError, subprocess.TimeoutExpired) as e:
        return {"status": "fail", "error": f"{type(e).__name__}: {e}"}


def expand_phone_path(value: str) -> str:
    runtime = os.environ.get("XDG_RUNTIME_DIR") or f"/run/user/{os.getuid()}"
    return value.replace("$XDG_RUNTIME_DIR", runtime)


def check_socket(path: str) -> dict[str, Any]:
    p = Path(expand_phone_path(path))
    exists = p.exists()
    is_socket = exists and p.is_socket()
    mode = oct(p.stat().st_mode & 0o777) if exists else None
    status = "pass" if is_socket else "fail"
    return {"status": status, "path": str(p), "exists": exists, "is_socket": is_socket, "mode": mode}


def check_service(name: str) -> dict[str, Any]:
    enabled = run_cmd(["systemctl", "--user", "is-enabled", name], timeout=3)
    active = run_cmd(["systemctl", "--user", "is-active", name], timeout=3)
    return {
        "status": "pass" if enabled.get("stdout") == "enabled" and active.get("stdout") == "active" else "fail",
        "enabled": enabled.get("stdout"),
        "active": active.get("stdout"),
        "enabled_check": enabled,
        "active_check": active,
    }


def check_realtime_ws(url: str, timeout: float) -> dict[str, Any]:
    """Minimal WebSocket upgrade probe without external dependencies."""
    from base64 import b64encode
    from os import urandom
    from urllib.parse import urlparse

    parsed = urlparse(url)
    if parsed.scheme not in {"ws", "wss"}:
        return {"status": "fail", "error": f"unsupported websocket scheme: {parsed.scheme}"}
    if parsed.scheme == "wss":
        return {"status": "skip", "reason": "wss probe not implemented without ssl wrapper"}

    host = parsed.hostname
    port = parsed.port or 80
    path = parsed.path or "/"
    if parsed.query:
        path += "?" + parsed.query
    if host is None:
        return {"status": "fail", "error": f"missing host in {url}"}

    key = b64encode(urandom(16)).decode("ascii")
    request = (
        f"GET {path} HTTP/1.1\r\n"
        f"Host: {host}:{port}\r\n"
        "Upgrade: websocket\r\n"
        "Connection: Upgrade\r\n"
        f"Sec-WebSocket-Key: {key}\r\n"
        "Sec-WebSocket-Version: 13\r\n"
        "Sec-WebSocket-Protocol: realtime\r\n"
        "\r\n"
    ).encode("ascii")

    try:
        with socket.create_connection((host, port), timeout=timeout) as sock:
            sock.settimeout(timeout)
            sock.sendall(request)
            response = sock.recv(1024).decode("iso-8859-1", errors="replace")
        first_line = response.splitlines()[0] if response else ""
        ok = " 101 " in first_line or first_line.endswith(" 101 Switching Protocols")
        return {"status": "pass" if ok else "fail", "first_line": first_line}
    except OSError as e:
        return {"status": "fail", "error": f"{type(e).__name__}: {e}"}


def compute_overall(checks: dict[str, Any]) -> str:
    hard = ["orchestrator", "unmute", "bridge", "ai_socket", "assistant_socket", "voice_service"]
    for key in hard:
        if checks.get(key, {}).get("status") != "pass":
            return "fail"
    return "pass"


def probe(config: dict[str, Any], *, dry_run: bool, timeout: float) -> dict[str, Any]:
    endpoints = config["endpoints"]
    phone = config["phone"]
    policy = config.get("health_policy", {})

    if dry_run:
        return {
            "ts": now(),
            "dry_run": True,
            "overall": "pass",
            "checks": {
                "manifest": {"status": "pass"},
                "configured_endpoints": {"status": "pass", "endpoints": endpoints},
                "configured_phone": {"status": "pass", "phone": phone},
            },
        }

    checks: dict[str, Any] = {}

    orch = check_http_json(endpoints["orchestrator_health"], timeout)
    if orch.get("status") == "pass":
        body = orch.get("json", {})
        expected = policy.get("orchestrator_required_status")
        if expected and body.get("status") != expected:
            orch["status"] = "fail"
            orch["policy_error"] = f"status {body.get('status')!r} != {expected!r}"
    checks["orchestrator"] = orch

    models = check_http_json(endpoints["orchestrator_models"], timeout)
    checks["orchestrator_models"] = models

    unmute = check_http_json(endpoints["unmute_health"], timeout)
    if unmute.get("status") == "pass":
        body = unmute.get("json", {})
        missing = [key for key in policy.get("unmute_required_true", []) if body.get(key) is not True]
        if missing:
            unmute["status"] = "fail"
            unmute["policy_error"] = f"required true fields failed: {missing}"
    checks["unmute"] = unmute

    bridge = check_http_json(endpoints["bridge_health"], timeout)
    if bridge.get("status") == "pass":
        body = bridge.get("json", {})
        missing = [key for key in policy.get("bridge_required_true", []) if body.get(key) is not True]
        if missing:
            bridge["status"] = "fail"
            bridge["policy_error"] = f"required true fields failed: {missing}"
    checks["bridge"] = bridge

    checks["ai_socket"] = check_socket(phone["ai_socket"])
    checks["assistant_socket"] = check_socket(phone["assistant_socket"])
    checks["voice_service"] = check_service(phone["voice_service"])
    checks["bridge_service"] = check_service(phone["bridge_service"])
    checks["unmute_realtime"] = check_realtime_ws(endpoints["unmute_realtime"], timeout)

    return {"ts": now(), "dry_run": False, "overall": compute_overall(checks), "checks": checks}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="mobile-stack.json")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--timeout", type=float, default=5.0)
    parser.add_argument("--pretty", action="store_true")
    args = parser.parse_args()

    config = load_config(Path(args.config))
    result = probe(config, dry_run=args.dry_run, timeout=args.timeout)
    print(json.dumps(result, indent=2 if args.pretty else None, sort_keys=True))
    return 0 if result["overall"] == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())
