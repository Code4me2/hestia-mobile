# Agent Phone Interface

The current Hestia Mobile agent-facing phone interface is a local-only contract spanning:

- `hestia-mobile-shell/docs/contracts/agent-phone-interface.md` — canonical visual/event contract.
- `hestia-ai-bridge` `GET /mobile_capabilities` — runtime discovery of supported states, visual verbs, protected modes, and socket paths.
- `hestia-ai-bridge` `GET /mobile_state` — current safe-action/protected-mode state for adapters.
- `mobile-stack.json` — integration manifest entry for capabilities/state endpoints and local sockets.
- `hestia-mobile-agent` — validated shell-side adapter CLI that fetches capabilities/state before sending allowed visual verbs.
- `hestia-mobile-fake-phone` — offline harness for local endpoint/socket integration testing.

## Local surfaces

```text
$XDG_RUNTIME_DIR/hestia-shell/assistant.sock
$XDG_RUNTIME_DIR/hestia-shell/ai.sock
http://127.0.0.1:8765/mobile_capabilities
http://127.0.0.1:8765/mobile_state
http://127.0.0.1:8765/health
```

Do not expose `assistant.sock` or `ai.sock` over Tailscale. Remote services may run on `tiny-emerson`, but UI IPC stays on the phone.

## Allowed visual verbs

```text
show_card
update_card
dismiss_card
show_confirmation
show_tool_status
open_chat
close_chat
open_app_interface
close_app_interface
```

## Agent adapter

The shell-side adapter is the preferred offline-testable send path for agents:

```bash
hestia-mobile-agent --capabilities-url http://127.0.0.1:8765/mobile_capabilities show-card --id agent-demo --title "Agent control works"
```

It validates the local-only capability document, requires and fetches `mobile_state`, refuses unadvertised verbs, refuses protected-mode-unsafe actions, and then writes one canonical event to `assistant.sock`. Use `--bridge-token` or `HESTIA_BRIDGE_TOKEN` when the local bridge is token-protected.

## Orchestrator integration rules

Remote orchestrators should not call the phone-local Unix sockets directly and should not treat Tailscale reachability as UI-control permission. The safe pattern is:

1. run a trusted adapter/tool on the phone;
2. discover `GET /mobile_capabilities` over loopback;
3. check `GET /mobile_state` before each optional visual action;
4. send only advertised visual verbs;
5. treat unknown contract versions as unsupported, not as an invitation to raw UI mutation.

## Versioning policy

`interface` identifies the contract family and `version` identifies breaking schema/semantic changes. Additive fields are non-breaking; consumers must ignore unknown fields and refuse unknown interface/version pairs.

## Protected modes

```text
phone_call_active
offline
error
```

Protected modes suppress optional material/actions while preserving state for restore.

## Verification

```bash
python3 -m json.tool mobile-stack.json
python3 scripts/validate-mobile-stack.py --config mobile-stack.json
curl -fsS http://127.0.0.1:8765/mobile_capabilities
curl -fsS http://127.0.0.1:8765/mobile_state
hestia-mobile-fake-phone --root /tmp/hestia-fake-phone --port 8766
```

Phone runtime validation should also verify `hestia-ai-bridge.service`, `hestia-unmute-voice.service`, `assistant.sock`, `ai.sock`, and the active PureOS/Phosh session.
