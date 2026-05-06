#!/usr/bin/env bash
set -u

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
