# Runbook: Recover Phone Voice Service

## Classification

- **Gate:** Gate F — Voice service readiness, with Gate E socket dependencies
- **Severity:** Blocking for hands-free voice tests on the phone
- **Owner:** `voice-client`, with `shell-ui` support when assistant socket readiness is the root cause
- **Scope:** Phone user service `hestia-unmute-voice.service`; no secrets required

## Symptoms

The phone does not capture or play assistant audio, or the structured probe reports `voice_service.status=fail`.

```bash
python3 scripts/probe-hestia-mobile-json.py --config mobile-stack.json --pretty
```

Expected failing output shape:

```json
{
  "overall": "fail",
  "checks": {
    "voice_service": {
      "status": "fail",
      "enabled": "enabled",
      "active": "inactive"
    }
  }
}
```

The service also depends on the shell assistant socket:

```bash
ls -l "${XDG_RUNTIME_DIR:-/run/user/$(id -u)}/hestia-shell/assistant.sock"
```

Expected healthy output shape:

```text
srw------- ... /run/user/1000/hestia-shell/assistant.sock
```

## Confirm service state

Run on the phone as the user that owns the graphical/session services:

```bash
systemctl --user is-enabled hestia-unmute-voice.service
systemctl --user is-active hestia-unmute-voice.service
systemctl --user status hestia-unmute-voice.service --no-pager
journalctl --user -u hestia-unmute-voice.service -n 120 --no-pager
```

Expected healthy outputs:

```text
enabled
active
```

Common failing outputs:

```text
disabled
inactive
failed
```

## Confirm configured command and sockets

The expected command is documented in `docs/phone-voice-service.md` and should use:

```bash
/home/purism/projects/ai-phone-review/unmute-streaming-client/.venv/bin/python \
  headless_client_microphone.py \
  --no-tui \
  --server-url ws://tiny-emerson:80 \
  --assistant-socket /run/user/%U/hestia-shell/assistant.sock \
  --input-device 11 \
  --output-device 11 \
  --verbose
```

Check shell IPC sockets:

```bash
ls -l "${XDG_RUNTIME_DIR:-/run/user/$(id -u)}/hestia-shell/ai.sock"
ls -l "${XDG_RUNTIME_DIR:-/run/user/$(id -u)}/hestia-shell/assistant.sock"
```

Expected healthy output shape:

```text
srw------- ... ai.sock
srw------- ... assistant.sock
```

If sockets are missing, recover the shell/bridge path before restarting voice capture.

## Recovery steps

1. Restart the voice service:

   ```bash
   systemctl --user restart hestia-unmute-voice.service
   systemctl --user is-active hestia-unmute-voice.service
   journalctl --user -u hestia-unmute-voice.service -n 60 --no-pager
   ```

   Expected output:

   ```text
   active
   ```

2. If boot persistence is being tested and the unit is disabled, enable it:

   ```bash
   systemctl --user enable --now hestia-unmute-voice.service
   systemctl --user is-enabled hestia-unmute-voice.service
   ```

   Expected output:

   ```text
   enabled
   ```

3. If the journal shows repeated audio-device failures, confirm the manifest device IDs still match the phone:

   ```bash
   python3 - <<'PY'
   import json
   cfg = json.load(open('mobile-stack.json'))
   print('input', cfg['phone'].get('voice_input_device'))
   print('output', cfg['phone'].get('voice_output_device'))
   PY
   ```

   Expected output:

   ```text
   input 11
   output 11
   ```

4. Re-run the structured probe:

   ```bash
   python3 scripts/probe-hestia-mobile-json.py --config mobile-stack.json --pretty
   ```

Expected recovered sections:

```json
{
  "checks": {
    "assistant_socket": {"status": "pass", "is_socket": true},
    "voice_service": {"status": "pass", "enabled": "enabled", "active": "active"}
  }
}
```

## Escalation notes

Open `mobile-integration-bug.yml` when the local service or sockets regress. Include service status and journal excerpts relevant to the failure. Do not include secrets, full environment dumps, private keys, or unrelated personal audio/log data.
