# Hestia Voice Gateway Release Checklist — 2026-05

Status: PRs opened, integration snapshot passing  
Created: 2026-05-06T23:46:54Z

This release coordinates the P0 Hestia voice-first mobile gateway stabilization across the shell, bridge, voice client, backend, and `hestia-mobile` integration repo.

## Component PRs

| Component | Branch | PR | Latest SHA | Status |
| --- | --- | --- | --- | --- |
| `hestia-shell` | `feat/hestia-voice-gateway` | [Code4me2/hestia-shell#1](https://github.com/Code4me2/hestia-shell/pull/1) | `44e52aa0` | Open |
| `hestia-ai-bridge` | `feat/hestia-voice-gateway` | [Code4me2/hestia-ai-bridge#1](https://github.com/Code4me2/hestia-ai-bridge/pull/1) | `986afda` | Open |
| `unmute-streaming-client` | `feat/hestia-voice-gateway` | [Code4me2/unmute-streaming-client#9](https://github.com/Code4me2/unmute-streaming-client/pull/9) | `9023ebf` | Open |
| `hestia-mobile` | `main` | N/A | `8364b3c` before this checklist | Landed |

## Known-good integration snapshot

Recorded in [`docs/compatibility-matrix.md`](../compatibility-matrix.md).

| Component | SHA / state |
| --- | --- |
| `hestia-mobile` | `8364b3c` |
| `hestia-shell` | `44e52aa0` |
| `hestia-ai-bridge` | `986afda` |
| `unmute-streaming-client` | `9023ebf` |
| Backend node | `tiny-emerson` |
| Probe result | `pass` |

Final structured probe command:

```bash
cd /home/purism/projects/ai-phone-review/hestia-mobile
python3 scripts/probe-hestia-mobile-json.py --config mobile-stack.json --pretty
```

Final checks were all passing:

```text
ai_socket: pass
assistant_socket: pass
bridge: pass
bridge_service: pass
orchestrator: pass
orchestrator_models: pass
unmute: pass
unmute_realtime: pass
voice_service: pass
overall: pass
```

## Acceptance gates

See [`docs/acceptance-gates.md`](../acceptance-gates.md) for canonical definitions.

- [x] Gate A — manifest validity
  - `mobile-stack.json` parsed as JSON.
  - `scripts/validate-mobile-stack.py --config mobile-stack.json` passed.
- [x] Gate B — local repo drift
  - component branches matched `mobile-stack.json` expectations.
  - worktrees were clean at final status check.
- [x] Gate C — live health
  - final structured probe passed all live checks.
  - backend `tiny-emerson` was healthy after restarting the orchestrator service.
- [x] Gate D — shell assistant event bus
  - assistant socket smoke test received normalized assistant events.
- [x] Gate E — release snapshot
  - passing snapshot recorded in `docs/compatibility-matrix.md`.
  - component PRs opened and linked here.

## Validation already completed

### `hestia-shell`

- Subagent spec review passed.
- Subagent quality review approved.
- Assistant event-bus Unix socket smoke test passed.
- Validated normalized event sequence included:
  - `assistant.connected`
  - `assistant.state=listening`
  - `assistant.transcript.user_delta`
  - `assistant.tool_call`
  - `assistant.state=speaking`
  - call availability false/true frames
  - `assistant.state=idle`

### `hestia-ai-bridge`

- Subagent spec review passed after review fixes.
- Subagent quality review approved after review fixes.
- Local service was restarted and verified active.
- `/health` returned backward-compatible fields plus sanitized nested orchestrator metadata.
- `orchestrator_online=true` after backend recovery.

### `unmute-streaming-client`

- `python3 -m pytest -q` passed: `12 passed`.
- Python compile checks passed.
- Subagent spec review passed after review fixes.
- Subagent quality review approved after review fixes.
- Installed user unit verified:

```text
Restart=on-failure
RestartPreventExitStatus=78
ActiveState=active
```

### `hestia-mobile`

- Manifest validation passed.
- Dry-run probe passed.
- Python compile passed for probe/validation scripts.
- Shell syntax check passed for scripts.
- Drift checker passed after cleanup.
- Final live structured probe passed all checks.

## Backend recovery note

The first final live probe found the backend orchestrator unavailable:

```text
agentic-flow-orchestrator.service: failed
Unmute llm_up=false
bridge orchestrator_online=false
```

Recovery performed on `tiny-emerson`:

```bash
systemctl --user reset-failed agentic-flow-orchestrator.service
systemctl --user start agentic-flow-orchestrator.service
```

After waiting for readiness:

```text
agentic-flow-orchestrator.service: active
Unmute /v1/health: llm_up=true, ok=true
```

The local bridge was then started/restarted so its health state reflected the recovered backend.

## Rollback / recovery

### If the shell PR causes UI/input-region issues

1. Revert or roll back `hestia-shell` to the previous known branch/commit.
2. Restart or reload the shell session as appropriate.
3. Re-run the assistant event-bus smoke test and live `hestia-mobile` probe.

### If bridge health regresses

Use the runbook:

```text
docs/runbooks/recover-bridge-orchestrator-offline.md
```

Quick checks:

```bash
systemctl --user status hestia-ai-bridge.service
curl -fsS http://127.0.0.1:8765/health
python3 scripts/probe-hestia-mobile-json.py --config mobile-stack.json --pretty
```

### If voice service reconnect behavior regresses

Use the runbook:

```text
docs/runbooks/recover-phone-voice-service.md
```

Quick checks:

```bash
systemctl --user show hestia-unmute-voice.service -p ActiveState -p Restart -p RestartPreventExitStatus
journalctl --user -u hestia-unmute-voice.service -n 100 --no-pager
```

### If backend LLM readiness regresses

Use the runbook:

```text
docs/runbooks/recover-unmute-llm-down.md
```

Quick checks on `tiny-emerson`:

```bash
systemctl --user status agentic-flow-orchestrator.service
curl -fsS http://127.0.0.1:8000/health
curl -fsS http://127.0.0.1/v1/health
```

## Manual validation still recommended before user-facing release

The P0 probe and protocol path are passing. Before a user-facing release, run a visual phone validation pass and record notes/screenshots if possible:

- [ ] Orb appears in expected centered position.
- [ ] Tap/click opens the chat drawer.
- [ ] Orb state visually changes for idle/listening/thinking/speaking/offline/error.
- [ ] Transcript preview does not obscure core UI.
- [ ] Input region matches visible orb bounds.
- [ ] Phone-call paused state is clear.
- [ ] Mic streaming and TTS pause during active calls.

Suggested destination for evidence:

```text
docs/validation/2026-05-hestia-voice-gateway/
```

## Merge checklist

- [ ] Confirm each component PR diff is expected.
- [ ] Confirm component CI, if present, is green.
- [ ] Merge `hestia-ai-bridge` PR.
- [ ] Merge `unmute-streaming-client` PR.
- [ ] Merge `hestia-shell` PR.
- [ ] Update `mobile-stack.json` expected branches/SHAs if component branches are merged to `main`.
- [ ] Re-run the final live structured probe.
- [ ] Add a post-merge row to `docs/compatibility-matrix.md`.
- [ ] Decide whether to tag a release in `hestia-mobile`.

## Follow-up P1 work

- Real visual/UI validation on device.
- End-to-end phone-call suppression hardening.
- Persistent local probe/history automation.
- Backend orchestrator durability investigation for previous `status=143` exit.
- Assistant UX polish: transcript preview, tool status, compact cards, constrained visual verbs.
- Packaging/image work only after install/runtime flow stabilizes.
