# Phone Voice Service

Durable phone-side service:

```text
hestia-unmute-voice.service
```

Expected command:

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

Useful operations:

```bash
systemctl --user status hestia-unmute-voice.service
journalctl --user -u hestia-unmute-voice.service -f
systemctl --user stop hestia-unmute-voice.service
systemctl --user start hestia-unmute-voice.service
systemctl --user enable --now hestia-unmute-voice.service
```

The component source of truth is:

```text
unmute-streaming-client/docs/hestia-phone-voice-service.md
unmute-streaming-client/systemd/hestia-unmute-voice.service
```
