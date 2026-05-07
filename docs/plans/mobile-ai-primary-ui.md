# Hestia Mobile AI-Primary UI Plan

> **For Hermes:** Use subagent-driven-development skill to implement this plan task-by-task.

**Goal:** Define and prototype the Hestia Mobile UI as an AI-primary PureOS/Phosh phone experience where the normal app launcher is secondary.

**Architecture:** Keep the working voice/backend/bridge services, but do not assume desktop/laptop `hestia-shell` is the production mobile shell. Build a mobile-native visual layer for PureOS/Phosh/Wayland that subscribes to the existing local assistant socket and renders a mostly blank AI canvas, transient cards/material, and a bottom-right affordance for the traditional app interface.

**Tech Stack:** PureOS Byzantium, Phosh/phoc Wayland session, local Unix sockets from `hestia-ai-bridge`, `unmute-streaming-client`, GTK/libadwaita or another Phosh-compatible Wayland surface toolkit, optional future compositor/session integration.

**Integration owner repo:** `hestia-mobile`

**Component repos:**
- `hestia-mobile` — integration, plans, probes, release gates, product direction.
- `hestia-ai-bridge` — local HTTP/socket health and assistant event bus.
- `unmute-streaming-client` — always-available voice client.
- `hestia-shell` — desktop/laptop Quickshell reference UI, not currently the production mobile UI.
- Proposed: `hestia-mobile-shell` or `hestia-mobile-ui` — PureOS/Phosh-native AI-primary visual layer.

**Runtime topology:**
- Phone local session: `Phosh:GNOME`, `phoc`, Wayland.
- Voice service: `hestia-unmute-voice.service`.
- Bridge service: `hestia-ai-bridge.service`.
- Local sockets: `$XDG_RUNTIME_DIR/hestia-shell/ai.sock`, `$XDG_RUNTIME_DIR/hestia-shell/assistant.sock`.
- Backend: `tiny-emerson` over Tailscale.

**Acceptance gates:**
- Blocking: phone remains reachable; voice service continues speaking; bridge health remains `status=ok`; local assistant socket is consumed by the new UI; normal app access remains available.
- Non-blocking initially: replacing Phosh completely, lockscreen integration, notification-center integration, packaging/image builds.

---

## Verified environment

Checks run on the phone showed:

```text
XDG_CURRENT_DESKTOP=Phosh:GNOME
XDG_SESSION_DESKTOP=phosh
XDG_SESSION_TYPE=wayland
OS=PureOS 10 (Byzantium)
Kernel=6.6.0-1-librem5 aarch64
```

Active graphical shell processes include:

```text
/usr/bin/phoc
/usr/libexec/gnome-session-binary --session=phosh
/usr/libexec/phosh
/usr/bin/squeekboard
xdg-desktop-portal / xdg-desktop-portal-gtk
```

No running `qs`, `quickshell`, Hyprland, or desktop `hestia-shell` process was found. The local `hestia-shell` repo is on the expected branch/commit, but it is not the active visible shell:

```text
hestia-shell branch: feat/hestia-voice-gateway
hestia-shell head: 44e52aa0 fix(assistant): align orb input region with wrapper
```

The AI runtime path is healthy:

```text
hestia-ai-bridge.service: active/running
hestia-unmute-voice.service: active/running
$XDG_RUNTIME_DIR/hestia-shell/ai.sock: present
$XDG_RUNTIME_DIR/hestia-shell/assistant.sock: present
bridge /health: status=ok, orchestrator_online=true
```

## Conclusion from the checks

`hestia-shell` is not currently the visible phone shell. It is a useful desktop/laptop and protocol/UI reference, but the phone is running Phosh/phoc on PureOS. Therefore the missing orb is expected: the Quickshell UI layer is not loaded.

For Hestia Mobile, the production direction should not be “port the current desktop shell wholesale.” The current desktop/laptop shell assumes a different stack and interaction model. The mobile product direction is substantially different:

- The normal app interface is secondary.
- The default screen can be mostly blank/desktop-like.
- The AI is the primary interface and brings up relevant freeform material only when needed.
- A bottom-right affordance opens the normal app interface.
- Voice remains the primary control surface.

This warrants a dedicated mobile UI/shell repository or at least a distinct mobile UI package under the Hestia Mobile umbrella.

## Product shape

Default/resting state:

```text
┌─────────────────────┐
│                     │
│                     │
│    blank calm AI    │
│      canvas         │
│                     │
│                 ◉   │  bottom-right app/interface affordance
└─────────────────────┘
```

When the AI has relevant material:

```text
┌─────────────────────┐
│                     │
│  ┌───────────────┐  │
│  │ contextual    │  │
│  │ card/material │  │
│  └───────────────┘  │
│                 ◉   │
└─────────────────────┘
```

When the user explicitly wants normal apps:

```text
┌─────────────────────┐
│ app launcher /      │
│ normal Phosh-like   │
│ interface           │
│                     │
│                 ◉   │
└─────────────────────┘
```

## Recommended repo decision

Create a separate repo when implementation starts:

```text
Code4me2/hestia-mobile-shell
```

Alternative names:

```text
Code4me2/hestia-mobile-ui
Code4me2/hestia-phosh-shell
```

Recommendation: use `hestia-mobile-shell` because the scope is broader than a single app, but still clearly separate from desktop `hestia-shell`.

`hestia-mobile` remains the integration/meta repo and should reference this future repo in `mobile-stack.json` once created.

## What to keep from current work

Keep and reuse:

- `hestia-ai-bridge` health and assistant socket.
- `unmute-streaming-client` voice/reconnect service.
- `hestia-mobile` probes, compatibility matrix, runbooks, release gates.
- `hestia-shell` event model and assistant UI ideas as reference.

Do not depend on:

- Hyprland-specific shell assumptions.
- Quickshell being present in PureOS/Phosh.
- Arch-based package assumptions.
- Desktop/laptop bar/dashboard patterns.

## Task 1: Add mobile UI stack discovery probe

**Objective:** Extend `hestia-mobile` with a read-only probe that reports the active phone session and whether a mobile UI layer is loaded.

**Files:**
- Create: `scripts/probe-mobile-ui-session.sh`
- Modify: `docs/acceptance-gates.md`

**Implementation notes:**

The script should report:

```bash
#!/usr/bin/env bash
set -euo pipefail

printf 'desktop=%s\n' "${XDG_CURRENT_DESKTOP:-}"
printf 'session_desktop=%s\n' "${XDG_SESSION_DESKTOP:-}"
printf 'session_type=%s\n' "${XDG_SESSION_TYPE:-}"
printf 'wayland_display=%s\n' "${WAYLAND_DISPLAY:-}"
printf 'display=%s\n' "${DISPLAY:-}"

printf '\nprocesses:\n'
pgrep -af 'phosh|phoc|gnome-shell|mutter|hyprland|Hyprland|qs|quickshell|hestia-mobile|hestia-shell' || true

printf '\nbinaries:\n'
for c in phosh phoc qs quickshell gsettings busctl gdbus; do
  if command -v "$c" >/dev/null 2>&1; then
    printf '%s=%s\n' "$c" "$(command -v "$c")"
  else
    printf '%s=missing\n' "$c"
  fi
done
```

**Verification:**

Run:

```bash
bash -n scripts/probe-mobile-ui-session.sh
scripts/probe-mobile-ui-session.sh
```

Expected on current phone:

```text
desktop=Phosh:GNOME
session_desktop=phosh
session_type=wayland
processes include phosh/phoc
qs=missing or no running qs process
```

## Task 2: Create mobile visual contract document

**Objective:** Define the shell-facing event contract for the AI-primary mobile canvas.

**Files:**
- Create: `docs/contracts/mobile-visual-surface.md`

**Contract outline:**

- Inputs:
  - assistant normalized events from `$XDG_RUNTIME_DIR/hestia-shell/assistant.sock`
  - bridge health from `http://127.0.0.1:8765/health`
  - optional call state source
- UI states:
  - blank/resting
  - listening
  - thinking
  - speaking
  - showing contextual material
  - normal app interface visible
  - call paused
  - offline/error
- Visual verbs:
  - `show_card`
  - `update_card`
  - `dismiss_card`
  - `show_transcript`
  - `show_tool_status`
  - `open_app_interface`
  - `close_app_interface`
  - `confirm_action`

**Verification:**

Document must explicitly say the visual layer consumes normalized `assistant.*` frames, not raw backend events.

## Task 3: Spike mobile UI implementation approach

**Objective:** Decide whether the first prototype should be a GTK/libadwaita fullscreen app, a Phosh plugin/extension path, or a compositor/session replacement experiment.

**Files:**
- Create: `docs/spikes/mobile-ui-approach.md`

**Options to compare:**

1. Fullscreen GTK/libadwaita app launched on login.
   - lowest risk
   - works with current Phosh
   - can subscribe to assistant socket
   - may not truly replace home shell
2. Phosh/plugin/extension integration.
   - better OS integration
   - likely more complex and packaging-sensitive
3. Dedicated compositor/session later.
   - closest product fit
   - highest risk
   - not first prototype

**Recommended first spike:** fullscreen GTK/libadwaita AI canvas that can be launched/killed without destabilizing Phosh.

**Verification:**

Plan should identify exactly how the prototype exits and returns to normal Phosh, so it cannot strand the phone.

## Task 4: Create `hestia-mobile-shell` repo skeleton

**Objective:** Create a dedicated repo for the mobile-native visual layer once the approach is approved.

**Files:**
- New repo: `Code4me2/hestia-mobile-shell`
- Initial files:
  - `README.md`
  - `docs/architecture.md`
  - `docs/contracts/mobile-visual-surface.md`
  - `docs/spikes/mobile-ui-approach.md`
  - `scripts/probe-runtime.sh`

**README must state:**

- This is not desktop/laptop `hestia-shell`.
- Target is PureOS/Phosh/mobile Wayland first.
- Voice is primary; app launcher is secondary.
- The default screen can be blank until the AI has relevant material.
- The UI consumes local assistant socket events.

**Verification:**

Repo exists, branch pushed, and `hestia-mobile/mobile-stack.json` references it as optional/experimental.

## Task 5: Prototype blank AI canvas

**Objective:** Build a minimal safe UI that proves the product shape without replacing Phosh.

**Files:**
- TBD after approach spike.

**Behavior:**

- Launches as a fullscreen or near-fullscreen mobile surface.
- Shows mostly blank canvas.
- Shows bottom-right app/interface button.
- Subscribes to assistant socket.
- Displays state text or minimal visual indicator for listening/thinking/speaking.
- Can exit cleanly and return to normal Phosh.

**Verification:**

- Voice continues speaking.
- UI receives assistant events.
- User can return to normal app interface.
- Phone is not stranded if the UI crashes.

## Immediate recommendation

Do not try to force desktop `hestia-shell` into the current PureOS/Phosh session as the production path. Use it as a reference, keep the current PRs as desktop/laptop/contract stabilization, and begin a mobile-native UI track under `hestia-mobile` with a separate `hestia-mobile-shell` repo when ready.
