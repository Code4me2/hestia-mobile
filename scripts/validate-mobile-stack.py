#!/usr/bin/env python3
"""Validate the Hestia Mobile stack manifest."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from urllib.parse import urlparse

REQUIRED_TOP_LEVEL = ["stack_name", "repos", "endpoints", "phone", "health_policy"]
REQUIRED_REPO_FIELDS = ["path", "remote", "branch", "owner"]
REQUIRED_ENDPOINTS = [
    "orchestrator_health",
    "orchestrator_models",
    "unmute_health",
    "unmute_realtime",
    "bridge_health",
]
REQUIRED_PHONE = ["ai_socket", "assistant_socket", "voice_service", "bridge_service"]


def load_config(path: Path) -> dict:
    try:
        return json.loads(path.read_text())
    except json.JSONDecodeError as e:
        raise SystemExit(f"invalid JSON in {path}: {e}")


def require(condition: bool, message: str, errors: list[str]) -> None:
    if not condition:
        errors.append(message)


def validate(config: dict) -> list[str]:
    errors: list[str] = []

    for key in REQUIRED_TOP_LEVEL:
        require(key in config, f"missing top-level key: {key}", errors)

    repos = config.get("repos", {})
    require(isinstance(repos, dict) and repos, "repos must be a non-empty object", errors)
    for name, repo in repos.items():
        require(isinstance(repo, dict), f"repo {name} must be an object", errors)
        if not isinstance(repo, dict):
            continue
        for field in REQUIRED_REPO_FIELDS:
            require(bool(repo.get(field)), f"repo {name} missing field: {field}", errors)
        remote = str(repo.get("remote", ""))
        require(remote.startswith("git@github.com:") or remote.startswith("https://github.com/"), f"repo {name} remote is not a GitHub URL: {remote}", errors)

    endpoints = config.get("endpoints", {})
    require(isinstance(endpoints, dict), "endpoints must be an object", errors)
    for key in REQUIRED_ENDPOINTS:
        value = str(endpoints.get(key, ""))
        require(bool(value), f"missing endpoint: {key}", errors)
        if value:
            parsed = urlparse(value)
            allowed = {"http", "https", "ws", "wss"}
            require(parsed.scheme in allowed and bool(parsed.netloc), f"invalid endpoint URL for {key}: {value}", errors)

    phone = config.get("phone", {})
    require(isinstance(phone, dict), "phone must be an object", errors)
    for key in REQUIRED_PHONE:
        require(bool(phone.get(key)), f"missing phone field: {key}", errors)

    policy = config.get("health_policy", {})
    require(isinstance(policy, dict), "health_policy must be an object", errors)
    require(isinstance(policy.get("unmute_required_true", []), list), "health_policy.unmute_required_true must be a list", errors)
    require(isinstance(policy.get("bridge_required_true", []), list), "health_policy.bridge_required_true must be a list", errors)

    return errors


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--config", default="mobile-stack.json", help="Path to mobile-stack.json")
    args = parser.parse_args()

    config_path = Path(args.config)
    config = load_config(config_path)
    errors = validate(config)
    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return 1

    print(f"ok: {config_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
