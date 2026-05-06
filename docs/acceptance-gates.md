# Acceptance Gates

Hestia Mobile uses explicit gates so transient backend failures and local phone issues are classified consistently.

## Gate A — Manifest validity

Passes when:

```bash
python3 scripts/validate-mobile-stack.py --config mobile-stack.json
```

exits with `0`.

Blocks work when:

- required repos/endpoints/services are missing from the manifest;
- endpoint schemes are invalid;
- expected branches are blank.

## Gate B — Local repo alignment

Passes when each local component repo exists and is on the manifest branch.

Temporary deviations are allowed for active feature work, but they must be documented in the PR or compatibility matrix.

## Gate C — Backend readiness

Blocking failures:

- orchestrator `/health` unavailable or not healthy;
- Unmute `/v1/health` has any of:
  - `stt_up=false`,
  - `tts_up=false`,
  - `llm_up=false`,
  - `ok=false`.

Currently non-blocking:

- `voice_cloning_up=false`.

## Gate D — Phone bridge readiness

Blocking failures:

- `hestia-ai-bridge` `/health` unavailable;
- `status != ok`;
- `orchestrator_online=false` after retry window.

A single false reading can be transient until bridge health metadata/hysteresis is implemented.

## Gate E — Shell socket readiness

Blocking failures:

- `ai.sock` missing;
- `assistant.sock` missing;
- sockets are not Unix sockets;
- socket permissions expose local shell IPC beyond the phone user.

## Gate F — Voice service readiness

Blocking failures:

- `hestia-unmute-voice.service` inactive;
- service disabled when testing boot persistence;
- repeated crash/restart loop in recent journal.

The phone hardware mic switch is the primary privacy boundary; software should keep the voice service available unless explicitly stopped or suppressing during calls.
