# Hestia Mobile Architecture

Hestia Mobile is voice-first. The phone screen is a shell actuator and compact
state surface, not the primary assistant UI.

## Runtime flow

```text
hardware mic/audio switch
  -> hestia-unmute-voice.service
  -> unmute-streaming-client/headless_client_microphone.py --no-tui
  -> ws://tiny-emerson:80/v1/realtime
  -> Unmute backend on tiny-emerson
  -> agentic_flow orchestrator on tiny-emerson:8000
  -> response audio/text back to phone
  -> hestia-ai-bridge assistant event bus
  -> /run/user/1000/hestia-shell/assistant.sock
  -> hestia-shell AssistantService + orb/chat drawer
```

## Boundaries

Phone-local only:

```text
/run/user/1000/hestia-shell/ai.sock
/run/user/1000/hestia-shell/assistant.sock
```

Tailscale-reachable backend services:

```text
http://tiny-emerson:8000
http://tiny-emerson:80
ws://tiny-emerson:80/v1/realtime
ws://tiny-emerson:8088
ws://tiny-emerson:8089
```

Do not expose shell Unix sockets over Tailscale.

## Product rule

The hardware audio switch is the main mic privacy boundary. Software should not
be overly cautious about allowing the assistant to listen when the switch is on,
but it should still suppress assistant audio/listening during active phone calls.
