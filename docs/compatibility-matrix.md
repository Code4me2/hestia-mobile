# Compatibility Matrix

Known-good Hestia Mobile integration snapshots.

| Date/Time UTC | hestia-mobile | hestia-shell | hestia-ai-bridge | unmute-streaming-client | Backend node | Probe result | Notes |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 2026-05-06 | `30f6056` | `fd16ad50` | `7b70e2f` | `adfe270` | `tiny-emerson` | partial/pass with transient backend observations | Initial voice gateway bring-up; service active, sockets present. Need structured probe history for transient `llm_up=false` / `orchestrator_online=false` cases. |
| 2026-05-06 22:28Z | `8313f05` | `44e52aa0` | `986afda` | `9023ebf` | `tiny-emerson` | pass | Structured probe passed after restarting `agentic-flow-orchestrator.service` on `tiny-emerson` and restarting `hestia-ai-bridge.service` locally. Includes bridge health hysteresis, shell orb input-region fix, Unmute client reconnect hardening, runbooks, issue templates, and CI. |
| 2026-05-07 offline | `a22dc09` | N/A (`hestia-mobile-shell` `cafad63`) | `50d883f` | unchanged | phone unavailable | offline tests pass | Agent-facing phone surface expansion: `/mobile_state`, fail-closed `hestia-mobile-agent` protected-mode gating, bearer-token support, fake phone harness, and loopback manifest validation. Live PureOS/Phosh validation still pending. |
| 2026-05-08 offline | `19cb650` | N/A (`hestia-mobile-shell` `cafad63`) | `85cef4a` | `9023ebf` | phone unavailable | offline tests pass | Follow-up agent-surface hardening: `/mobile_state` now reports live `PhoneCallGuard` call-active protected mode to keep adapter gating aligned with the assistant event bus. Live PureOS/Phosh validation still pending. |

Update this table after each successful structured probe and component branch push.
