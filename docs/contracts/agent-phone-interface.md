# Agent Phone Interface

The current Hestia Mobile agent-facing phone interface is a local-only contract spanning:

- `hestia-mobile-shell/docs/contracts/agent-phone-interface.md` — canonical visual/event contract.
- `hestia-ai-bridge` `GET /mobile_capabilities` — runtime discovery of supported states, visual verbs, protected modes, and socket paths.
- `mobile-stack.json` — integration manifest entry for the capabilities endpoint and local sockets.
- `hestia-mobile-agent` — validated shell-side adapter CLI that fetches capabilities before sending allowed visual verbs.

## Local surfaces

```text
$XDG_RUNTIME_DIR/hestia-shell/assistant.sock
$XDG_RUNTIME_DIR/hestia-shell/ai.sock
http://127.0.0.1:8765/mobile_capabilities
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

It validates the local-only capability document and refuses unadvertised verbs before writing to `assistant.sock`.

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
```

Phone runtime validation should also verify `hestia-ai-bridge.service`, `hestia-unmute-voice.service`, `assistant.sock`, `ai.sock`, and the active PureOS/Phosh session.
