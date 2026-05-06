# Runbook: Recover Bridge or Orchestrator Offline

## Classification

- **Gate:** Gate C — Backend readiness, Gate D — Phone bridge readiness
- **Severity:** Blocking for shell assistant and voice gateway tests
- **Owner:** `bridge` when `127.0.0.1:8765/health` fails; `orchestrator` when `tiny-emerson:8000/health` fails
- **Scope:** Phone-local bridge plus backend orchestrator health; no secrets required

## Symptoms

One or more of these checks fail:

```bash
curl -fsS http://tiny-emerson:8000/health
curl -fsS http://127.0.0.1:8765/health
python3 scripts/probe-hestia-mobile-json.py --config mobile-stack.json --pretty
```

Expected orchestrator failure examples:

```text
curl: (6) Could not resolve host: tiny-emerson
curl: (7) Failed to connect to tiny-emerson port 8000
curl: (22) The requested URL returned error: 503
```

Expected bridge failure examples:

```text
curl: (7) Failed to connect to 127.0.0.1 port 8765
```

Expected probe classification shape:

```json
{
  "overall": "fail",
  "checks": {
    "orchestrator": {"status": "fail"},
    "bridge": {"status": "fail"}
  }
}
```

## Confirm backend reachability

```bash
getent hosts tiny-emerson
curl -fsS http://tiny-emerson:8000/health
curl -fsS http://tiny-emerson:8000/v1/models
```

Expected healthy output shape:

```text
100.x.y.z tiny-emerson...
{"status":"healthy"}
```

`/v1/models` should return JSON. If DNS fails, verify Tailnet connectivity outside this repo. If DNS passes but HTTP fails, treat as an orchestrator backend incident.

## Confirm bridge service on the phone

Run on the phone user session:

```bash
systemctl --user is-enabled hestia-ai-bridge.service
systemctl --user is-active hestia-ai-bridge.service
systemctl --user status hestia-ai-bridge.service --no-pager
journalctl --user -u hestia-ai-bridge.service -n 80 --no-pager
curl -fsS http://127.0.0.1:8765/health
```

Expected healthy outputs:

```text
enabled
active
```

Expected bridge health shape:

```json
{"status":"ok","orchestrator_online":true}
```

If `status=ok` but `orchestrator_online=false`, the bridge is running but the backend dependency is unavailable or failing health checks.

## Recovery steps

1. If `hestia-ai-bridge.service` is inactive or failed, restart it:

   ```bash
   systemctl --user restart hestia-ai-bridge.service
   systemctl --user is-active hestia-ai-bridge.service
   journalctl --user -u hestia-ai-bridge.service -n 40 --no-pager
   ```

   Expected output:

   ```text
   active
   ```

2. If the service is disabled and boot persistence is under test, enable it:

   ```bash
   systemctl --user enable --now hestia-ai-bridge.service
   systemctl --user is-enabled hestia-ai-bridge.service
   ```

   Expected output:

   ```text
   enabled
   ```

3. If orchestrator health fails, recover/redeploy the orchestrator in the `agentic_flow` repo or backend service environment. Do not record credentials in this repo.
4. Re-run the local probe:

   ```bash
   python3 scripts/probe-hestia-mobile-json.py --config mobile-stack.json --pretty
   ```

Expected recovered bridge/orchestrator sections:

```json
{
  "checks": {
    "orchestrator": {"status": "pass"},
    "orchestrator_models": {"status": "pass"},
    "bridge": {"status": "pass"},
    "bridge_service": {"active": "active"}
  }
}
```

## Escalation notes

Open `backend-readiness-incident.yml` for backend outages or `mobile-integration-bug.yml` for bridge-only regressions. Include exact command output, but do not include secrets, private environment variables, Tailnet auth keys, or private logs unrelated to the failure.
