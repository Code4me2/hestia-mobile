# Repository Map

## Integration repo

### `hestia-mobile`

Owns cross-repo architecture, deployment docs, health probes, packaging notes,
release checklists, and device bring-up plans.

## Component repos

### `hestia-shell`

Owns shell UI, orb/chat surfaces, QML services, drawer integration, and user-visible assistant state.

### `hestia-ai-bridge`

Owns local shell IPC, `ai.sock`, `assistant.sock`, normalized assistant events,
call-state parsing, and orchestrator HTTP/SSE bridging.

### `unmute-streaming-client`

Owns phone-side microphone/speaker realtime client, headless daemon mode, audio
device handling, and publication of realtime events to `assistant.sock`.

### `unmute`

Owns backend realtime voice service, STT/TTS, and websocket `/v1/realtime`.

### `agentic_flow`

Owns orchestration, agent routing, LLM/tool calls, and OpenAI-compatible chat/SSE endpoints.
