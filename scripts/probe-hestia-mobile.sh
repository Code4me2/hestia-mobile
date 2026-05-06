#!/usr/bin/env bash
set -u

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
PROBE="$ROOT/scripts/probe-hestia-mobile-json.py"
CONFIG="$ROOT/mobile-stack.json"

if command -v python3 >/dev/null 2>&1 && [ -x "$PROBE" ]; then
  python3 "$PROBE" --config "$CONFIG" --pretty || true
  exit 0
fi

echo '## backend: orchestrator'
curl -fsS http://tiny-emerson:8000/health && echo || echo 'orchestrator health failed'

echo '## backend: unmute'
curl -fsS http://tiny-emerson/v1/health && echo || echo 'unmute health failed'

echo '## phone: bridge'
curl -fsS http://127.0.0.1:8765/health && echo || echo 'hestia-ai-bridge health failed'

echo '## phone: sockets'
ls -l "${XDG_RUNTIME_DIR:-/run/user/$(id -u)}/hestia-shell/ai.sock" 2>/dev/null || echo 'ai.sock missing'
ls -l "${XDG_RUNTIME_DIR:-/run/user/$(id -u)}/hestia-shell/assistant.sock" 2>/dev/null || echo 'assistant.sock missing'

echo '## phone: voice service'
systemctl --user is-enabled hestia-unmute-voice.service 2>/dev/null || true
systemctl --user is-active hestia-unmute-voice.service 2>/dev/null || true
