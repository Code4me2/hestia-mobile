# Runbook: Recover Unmute `llm_up=false`

## Classification

- **Gate:** Gate C — Backend readiness
- **Severity:** Blocking for voice assistant end-to-end tests
- **Owner:** `backend-voice`, with `orchestrator` support if model routing is the root cause
- **Scope:** Backend node `tiny-emerson`; no phone secrets or credentials are required

## Symptoms

The Unmute health endpoint is reachable, but its JSON reports the LLM dependency down.

```bash
curl -fsS http://tiny-emerson/v1/health
```

Expected failing output shape:

```json
{"stt_up":true,"tts_up":true,"llm_up":false,"ok":false,"voice_cloning_up":false}
```

`voice_cloning_up=false` is currently non-blocking; `llm_up=false` and `ok=false` are blocking.

## Confirm and capture evidence

Run from the phone or another host on the same Tailnet:

```bash
python3 scripts/probe-hestia-mobile-json.py --config mobile-stack.json --pretty
```

Expected failing fields:

```json
{
  "overall": "fail",
  "checks": {
    "unmute": {
      "status": "fail",
      "policy_error": "required true fields failed: ['llm_up', 'ok']"
    }
  }
}
```

Check orchestrator health to determine whether the LLM failure is isolated to Unmute or upstream:

```bash
curl -fsS http://tiny-emerson:8000/health
curl -fsS http://tiny-emerson:8000/v1/models
```

Expected healthy orchestrator output shape:

```json
{"status":"healthy"}
```

`/v1/models` should return a JSON object or list of model metadata. A connection error, timeout, or non-JSON body indicates an orchestrator/model-serving incident, not only Unmute.

## Recovery steps

1. If orchestrator health or models fail, follow `docs/runbooks/recover-bridge-orchestrator-offline.md` for the backend portion first.
2. Recheck Unmute after orchestrator/model serving is healthy:

   ```bash
   curl -fsS http://tiny-emerson/v1/health
   ```

3. If `llm_up=false` persists while orchestrator is healthy, restart or redeploy the Unmute backend using that repo's service/deployment procedure. Do not place secrets in this repo or in the incident issue.
4. Verify the realtime WebSocket upgrade from this repo:

   ```bash
   python3 scripts/probe-hestia-mobile-json.py --config mobile-stack.json --pretty
   ```

Expected recovered output fields:

```json
{
  "overall": "pass",
  "checks": {
    "unmute": {"status": "pass"},
    "unmute_realtime": {"status": "pass", "first_line": "HTTP/1.1 101 Switching Protocols"}
  }
}
```

The probe may still fail on phone-local sockets/services if it is run somewhere other than the phone. In that case, only use the `unmute` and `unmute_realtime` sections for this backend incident.

## Escalation notes

Open `backend-readiness-incident.yml` with:

- exact command output above;
- timestamp and host where the probe ran;
- whether orchestrator health and `/v1/models` passed;
- no tokens, private keys, environment dumps, or credential-bearing URLs.
