# Compatibility Matrix

Known-good Hestia Mobile integration snapshots.

| Date/Time UTC | hestia-mobile | hestia-shell | hestia-ai-bridge | unmute-streaming-client | Backend node | Probe result | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2026-05-06 | `30f6056` | `fd16ad50` | `7b70e2f` | `adfe270` | `tiny-emerson` | partial/pass with transient backend observations | Initial voice gateway bring-up; service active, sockets present. Need structured probe history for transient `llm_up=false` / `orchestrator_online=false` cases. |

Update this table after each successful structured probe and component branch push.
