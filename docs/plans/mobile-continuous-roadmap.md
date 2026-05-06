# Hestia Mobile Continuous Cross-Repo Roadmap

> **For Hermes:** Use subagent-driven-development for implementation slices. Dispatch fresh subagents for shell, bridge, voice-client, and integration tasks where they touch separate repos.

**Goal:** Make `hestia-mobile` the continuous coordination repo for the Hestia voice-first AI phone stack.

**Architecture:** Component code stays in focused repos; this repo owns integration state, compatibility manifests, probes, runbooks, acceptance gates, and cross-repo contract docs. The phone is a thin voice/UI gateway; remote STT/TTS/LLM/orchestration runs on `tiny-emerson` over Tailscale.

**Tech Stack:** PureOS/Librem phone, Quickshell/QML, Python 3.11 bridge/client code, systemd user services, Tailscale MagicDNS, GitHub repos/CI.

---

## Current component branches

```text
hestia-mobile:            main
hestia-shell:             feat/hestia-voice-gateway
hestia-ai-bridge:         feat/hestia-voice-gateway
unmute-streaming-client:  feat/hestia-voice-gateway
```

## Current backend endpoints

```text
Orchestrator health:  http://tiny-emerson:8000/health
Orchestrator models:  http://tiny-emerson:8000/v1/models
Unmute health:        http://tiny-emerson/v1/health
Unmute realtime:      ws://tiny-emerson:80/v1/realtime
Bridge health:        http://127.0.0.1:8765/health
Shell sockets:        $XDG_RUNTIME_DIR/hestia-shell/{ai.sock,assistant.sock}
Voice service:        hestia-unmute-voice.service
```

## Recent assessment summary

Subagents reviewed the active repos and identified these priority areas:

1. **hestia-shell P0:** verify/fix assistant orb sizing and live event-bus subscription; possible zero-size `Assistant.Wrapper` because implicit size may not produce actual `width`/`height` in the anchored drawer context.
2. **hestia-ai-bridge P0:** add health metadata, failure logging, and hysteresis; `/health` currently reports a cached `orchestrator_online` boolean with no last error or retry context.
3. **unmute-streaming-client P0:** implement in-process websocket reconnect and text-stream dedupe; current `Restart=always` masks websocket 1011/keepalive failures by restarting the whole process.
4. **hestia-mobile P0:** add machine-readable stack manifest, structured probe, docs/CI/runbooks, and compatibility tracking.

## Phase 1 — Integration state and probes

### Task 1: Add machine-readable stack manifest

**Objective:** Track component repos, expected branches, service names, sockets, endpoints, and blocking/non-blocking health fields in one file.

**Files:**
- Create: `mobile-stack.json`
- Create: `docs/integration-manifest.md`

**Verification:**

```bash
python3 -m json.tool mobile-stack.json >/tmp/mobile-stack.pretty.json
```

### Task 2: Add manifest validator

**Objective:** Validate the manifest structure in CI and locally without external dependencies.

**Files:**
- Create: `scripts/validate-mobile-stack.py`

**Verification:**

```bash
python3 scripts/validate-mobile-stack.py --config mobile-stack.json
```

### Task 3: Add structured live/dry-run probe

**Objective:** Produce JSON probe output suitable for logs, CI artifacts, and issue templates.

**Files:**
- Create: `scripts/probe-hestia-mobile-json.py`
- Modify: `scripts/probe-hestia-mobile.sh`
- Create: `docs/acceptance-gates.md`

**Verification:**

```bash
python3 scripts/probe-hestia-mobile-json.py --dry-run --config mobile-stack.json
python3 scripts/probe-hestia-mobile-json.py --config mobile-stack.json
scripts/probe-hestia-mobile.sh
```

### Task 4: Add compatibility matrix

**Objective:** Track known-good component SHA combinations and probe state.

**Files:**
- Create: `docs/compatibility-matrix.md`

**Verification:** manual doc review.

## Phase 2 — Runbooks and incident capture

### Task 5: Add recovery runbooks

**Objective:** Capture exact steps for transient failures already observed.

**Files:**
- Create: `docs/runbooks/recover-unmute-llm-down.md`
- Create: `docs/runbooks/recover-bridge-orchestrator-offline.md`
- Create: `docs/runbooks/recover-phone-voice-service.md`

**Verification:** runbook commands are copy-pasteable and redact secrets.

### Task 6: Add issue templates

**Objective:** Standardize cross-repo bugs, backend incidents, and contract changes.

**Files:**
- Create: `.github/ISSUE_TEMPLATE/mobile-integration-bug.yml`
- Create: `.github/ISSUE_TEMPLATE/backend-readiness-incident.yml`
- Create: `.github/ISSUE_TEMPLATE/cross-repo-contract-change.yml`
- Create: `.github/ISSUE_TEMPLATE/mobile-bringup-task.yml`

**Verification:** YAML parses and templates render on GitHub.

## Phase 3 — Cross-repo contract docs

### Task 7: Add contracts directory

**Objective:** Keep event, health, service, networking, and audio contracts stable across repos.

**Files:**
- Create: `docs/contracts/assistant-event-bus.md`
- Create: `docs/contracts/health-endpoints.md`
- Create: `docs/contracts/systemd-services.md`
- Create: `docs/contracts/tailscale-networking.md`
- Create: `docs/contracts/audio-device-selection.md`

**Verification:** docs reference actual manifest endpoints/service names.

## Phase 4 — Component repo implementation slices

### Task 8: Bridge health observability

**Repo:** `hestia-ai-bridge`

**Objective:** Add structured health state metadata, last error, consecutive failures, and hysteresis.

**Files likely touched:**
- `hestia_ai_bridge/main.py`
- `hestia_ai_bridge/http_server.py`
- `hestia_ai_bridge/orchestrator_client.py`
- tests under `tests/`

**Verification:**

```bash
cd /home/purism/projects/ai-phone-review/hestia-ai-bridge
.venv/bin/python -m pytest -q
curl -sS http://127.0.0.1:8765/health | python3 -m json.tool
```

### Task 9: Voice client in-process reconnect and dedupe

**Repo:** `unmute-streaming-client`

**Objective:** Keep one long-running process across websocket failures, dedupe repeated text event families, and reduce one-letter ambient triggers without overblocking mic listening.

**Files likely touched:**
- `headless_client_microphone.py`
- `unmute/assistant_event_sink.py`
- tests under `tests/`
- `systemd/hestia-unmute-voice.service`

**Verification:**

```bash
cd /home/purism/projects/ai-phone-review/unmute-streaming-client
.venv/bin/python -m pytest -q
systemctl --user restart hestia-unmute-voice.service
journalctl --user -u hestia-unmute-voice.service -n 80 --no-pager
```

### Task 10: Shell orb runtime fix and event smoke tests

**Repo:** `hestia-shell`

**Objective:** Ensure orb has real size/input region and live event-bus frames update state/transcripts/tool status.

**Files likely touched:**
- `modules/assistant/Wrapper.qml`
- `modules/assistant/Orb.qml`
- `services/AssistantService.qml`
- `services/AIConfig.qml`
- docs under `docs/`

**Verification:**

```bash
qs ipc call assistant state listening
qs ipc call assistant state thinking
qs ipc call assistant state speaking
qs ipc call assistant state idle
qs ipc call assistant status
```

## Phase 5 — CI and continuous coordination

### Task 11: Add local/dry-run CI for hestia-mobile

**Objective:** Validate docs, manifest, and scripts on every PR without requiring live Tailscale access.

**Files:**
- Create: `.github/workflows/docs-and-probes.yml`

**Verification:** GitHub Actions passes on PR.

### Task 12: Add optional self-hosted live probe workflow

**Objective:** Run live probes from a phone/Tailscale runner when available.

**Files:**
- Create: `.github/workflows/mobile-live-probe.yml`

**Verification:** manual `workflow_dispatch` uploads probe JSON artifact.

## Continuous work cadence

1. Run structured probe.
2. Check component drift against manifest.
3. Update compatibility matrix with known-good SHAs.
4. Open/triage cross-repo issues from failures.
5. Dispatch subagents per independent repo task.
6. Require tests/probes and commits per repo.
7. Push branches and create PRs with `gh`.
8. Repeat.
