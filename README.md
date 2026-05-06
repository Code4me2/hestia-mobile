# Hestia Mobile

Mobile integration layer for the Hestia voice-first AI phone.

This repository documents and assembles the phone-side pieces that turn a
PureOS/Librem-style device into a thin voice gateway for the Hestia assistant.
Component code stays in focused repos; this repo tracks the cross-repo product,
architecture, deployment, and verification flow.

## Component repos

- `hestia-shell` — QML shell surface, orb, drawers, assistant UI state.
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
- `scripts/probe-hestia-mobile.sh` — read-only health probe.
