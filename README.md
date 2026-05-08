# Hestia Mobile

Mobile integration layer for the Hestia voice-first AI phone.

This repository documents and assembles the phone-side pieces that turn a
PureOS/Librem-style device into a thin voice gateway for the Hestia assistant.
Component code stays in focused repos; this repo tracks the cross-repo product,
architecture, deployment, and verification flow.

## Component repos

- `hestia-mobile-shell` — experimental PureOS/Phosh AI-primary mobile visual layer.
- `hestia-shell` — desktop/laptop QML shell surface and reference assistant UI model.
- `hestia-ai-bridge` — phone-local AI socket and assistant event bus.
- `unmute-streaming-client` — phone microphone/speaker realtime voice client.
- `unmute` — backend realtime voice/STT/TTS service on inference hardware.
- `agentic_flow` — orchestrator/agent backend.

## Current topology

```text
PureOS phone
  -> local Unix sockets for shell/UI
  -> Tailscale MagicDNS
  -> tiny-emerson backend node
```

Backend endpoints currently verified:

```text
Unmute health:        http://tiny-emerson/v1/health
Unmute realtime:      ws://tiny-emerson:80/v1/realtime
Orchestrator health:  http://tiny-emerson:8000/health
Bridge capabilities:  http://127.0.0.1:8765/mobile_capabilities
Bridge mobile state:  http://127.0.0.1:8765/mobile_state
```

## Development branches

Current mobile bring-up work is on this branch in the component repos:

```text
feat/hestia-voice-gateway
```

## Documentation map

- `docs/architecture.md` — high-level phone/backend architecture.
- `docs/repo-map.md` — ownership boundaries across repos.
- `docs/phone-voice-service.md` — durable phone voice daemon setup.
- `docs/tiny-emerson-backend.md` — backend service checks.
- `docs/acceptance-gates.md` — integration readiness gates and failure classification.
- `docs/integration-manifest.md` — `mobile-stack.json` manifest contract.
- `docs/contracts/agent-phone-interface.md` — local-only agent-facing phone interface contract.
- `docs/runbooks/recover-unmute-llm-down.md` — backend LLM dependency recovery.
- `docs/runbooks/recover-bridge-orchestrator-offline.md` — bridge/orchestrator recovery.
- `docs/runbooks/recover-phone-voice-service.md` — phone voice service recovery.

## Local validation

```bash
python3 -m json.tool mobile-stack.json
python3 scripts/validate-mobile-stack.py --config mobile-stack.json
python3 scripts/probe-hestia-mobile-json.py --config mobile-stack.json --dry-run --pretty
python3 -m py_compile scripts/*.py
bash -n scripts/*.sh
scripts/check-component-drift.sh --manifest-only
```

- `scripts/probe-hestia-mobile.sh` — read-only health probe wrapper.
- `scripts/probe-hestia-mobile-json.py` — structured JSON health probe with `--dry-run` for CI.
- `scripts/check-component-drift.sh` — read-only local repo branch/worktree drift check from `mobile-stack.json`.
