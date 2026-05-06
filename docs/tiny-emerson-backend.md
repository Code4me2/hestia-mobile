# tiny-emerson Backend

`tiny-emerson` is the current Tailscale backend node for the phone gateway.

## Services

```text
agentic_flow orchestrator: http://tiny-emerson:8000
Unmute backend:           http://tiny-emerson:80
Unmute realtime:          ws://tiny-emerson:80/v1/realtime
STT:                      ws://tiny-emerson:8088
TTS:                      ws://tiny-emerson:8089
```

## Health checks

```bash
curl -fsS http://tiny-emerson:8000/health
curl -fsS http://tiny-emerson:8000/v1/models
curl -fsS http://tiny-emerson/v1/health
```

`http://tiny-emerson/health` may return 404; Unmute health is `/v1/health`.
