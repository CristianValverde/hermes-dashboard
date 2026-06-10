# Hermes Dashboard Access Modes Design

Updated: 2026-06-09

## Objective

Add a clean access model for the dashboard with two user tiers:

- Casual users: keep the current `localhost` experience with zero networking setup.
- Power users: optionally expose the dashboard over LAN or a mesh VPN without coupling the project to any specific VPN vendor.

This should remain a local-first tool. The dashboard is meant to run on the same PC that already hosts Hermes, not as a public internet service.

## Product Positioning

- Default mode should stay private and simple.
- Remote/mobile access should be opt-in.
- The repo should document LAN and mesh-VPN access as supported patterns.
- The repo should explicitly avoid encouraging public internet exposure without auth and HTTPS.

## Current State

Relevant files:

- `api/flask_app.py`
- `launch-dashboard.ps1`
- `launch-dashboard.bat`
- `hermes-dashboard.bat`
- `README.md`

Current technical observations:

- The frontend already calls `fetch('/api/all')`, so it is same-origin and compatible with LAN/VPN access as long as Flask serves the SPA and API from the same host.
- The SPA already has responsive layouts and was visually validated in mobile viewport.
- `api/flask_app.py` currently hardcodes:
  - `app.run(host='0.0.0.0', port=8590, debug=True)`
- The launch scripts currently present the dashboard as `http://localhost:8590`.

Main gap:

- The project does not yet expose a deliberate, documented access strategy.
- `0.0.0.0` is effectively power-user behavior, but it is not surfaced as an explicit mode and does not preserve the desired local-first default.

## Proposed Access Model

### Mode 1: Localhost (default)

Use for normal local usage on the PC running Hermes.

Behavior:

- Bind host: `127.0.0.1`
- Port: `8590`
- Browser target: `http://localhost:8590`

Why:

- Safest default
- No firewall prompt in many setups
- Matches user expectation for “just run it”

### Mode 2: LAN / Mesh VPN (optional)

Use for:

- Same-Wi-Fi mobile access
- Remote access through Tailscale, ZeroTier, WireGuard, OpenVPN, or equivalent private network

Behavior:

- Bind host: `0.0.0.0` by default for remote mode
- Port: `8590`
- Browser target:
  - LAN: `http://<LAN-IP>:8590`
  - VPN: `http://<VPN-IP>:8590`

Why:

- Keeps the app vendor-agnostic
- Works for any private routed network
- Requires no frontend origin changes because the SPA is same-origin

## Configuration Design

Add environment-driven runtime configuration instead of hardcoding host/port.

Suggested env vars:

```text
HERMES_DASHBOARD_HOST=127.0.0.1
HERMES_DASHBOARD_PORT=8590
HERMES_DASHBOARD_DEBUG=true
```

Optional convenience variable:

```text
HERMES_DASHBOARD_ACCESS_MODE=localhost|network
```

Recommended precedence:

1. Explicit `HERMES_DASHBOARD_HOST`
2. Fallback derived from `HERMES_DASHBOARD_ACCESS_MODE`
3. Default to `127.0.0.1`

Derived behavior example:

- `ACCESS_MODE=localhost` => host `127.0.0.1`
- `ACCESS_MODE=network` => host `0.0.0.0`

## File-Level Change Plan

### 1. `api/flask_app.py`

Replace hardcoded `app.run(...)` values with environment-based configuration.

Expected changes:

- Read host, port, and debug from env vars.
- Default host to `127.0.0.1`.
- Keep port default at `8590`.
- Print a clearer startup summary including:
  - local URL
  - whether network mode is enabled
  - reminder not to expose publicly

Suggested output shape:

```text
Hermes Dashboard running
- Local:   http://localhost:8590
- Network: enabled
```

If host is not localhost-only, print an extra warning:

```text
Warning: dashboard is reachable from LAN/VPN. Do not expose to public internet without auth/HTTPS.
```

### 2. `launch-dashboard.ps1`

Keep this as the casual-user launcher.

Expected changes:

- Set `HERMES_DASHBOARD_HOST=127.0.0.1`
- Open `http://localhost:8590`
- Preserve current simple UX

### 3. `launch-dashboard.bat`

Same intent as the PowerShell launcher.

Expected changes:

- Set `HERMES_DASHBOARD_HOST=127.0.0.1`
- Open `http://localhost:8590`

### 4. `hermes-dashboard.bat`

Align behavior with the other casual-user launcher.

Expected changes:

- Same localhost-first defaults
- Same messaging consistency

### 5. New launcher: `launch-dashboard-network.ps1`

Add an explicit power-user launcher.

Expected behavior:

- Set `HERMES_DASHBOARD_HOST=0.0.0.0`
- Keep port `8590`
- Print guidance:
  - “Use your LAN IP or VPN IP from another device”
  - “Best for Tailscale/ZeroTier/WireGuard/OpenVPN private networks”

Optional:

- Attempt to print likely IPv4 addresses for convenience
- Keep it informational, not magic-heavy

### 6. Optional new launcher: `launch-dashboard-network.bat`

Windows batch equivalent if desired for parity.

### 7. `README.md`

Add an `Access Modes` section with three documented patterns:

- Localhost
- LAN
- Mesh VPN

Content to include:

- `localhost` is the default and recommended for normal use
- LAN/mobile access works if both devices can reach the PC
- Mesh VPN works if mobile and PC share a private VPN network
- No special frontend change is needed because the app is same-origin
- Do not expose directly to public internet

Suggested examples:

```text
http://192.168.1.23:8590
http://100.x.y.z:8590
```

### 8. `CONTEXT.md`

Update repo memory after implementation lands:

- localhost is the default access mode
- network mode is opt-in
- power-user launcher exists

## Security Posture

Recommended project stance:

- Supported:
  - localhost
  - trusted LAN
  - private mesh VPN
- Not recommended:
  - direct internet exposure

Reason:

- No built-in auth layer
- No HTTPS termination in current local stack
- SQLite + local Flask architecture is not intended as a hardened public service

## VPN Guidance

The repo should stay neutral and not integrate with a specific provider.

Recommended wording:

- “Any VPN that places your mobile and your PC on the same private routed network should work.”

Examples that fit:

- Tailscale
- ZeroTier
- WireGuard
- OpenVPN

The project should not depend on their SDKs or CLIs.

## Non-Goals

- No native mobile app
- No standalone hosted mobile product
- No internet-facing deployment flow in this change
- No auth system in this change

## Validation Plan

After implementation:

1. Start default launcher and verify only localhost access is intended.
2. Verify `GET /api/all` still returns `200`.
3. Start network launcher and verify access from:
   - another browser on LAN, or
   - a second device over mesh VPN
4. Verify mobile rendering on a real phone/browser after network access is enabled.
5. Confirm `fetch('/api/all')` works unchanged from the remote device because it remains same-origin.

## Recommended Session Scope

The implementation session should do all of the following together:

- Runtime config in `api/flask_app.py`
- Localhost-first launchers
- New network launcher
- README access-mode documentation
- Cleanup and commit of the accumulated dashboard UI work before merging `agent-dashboard-ui-ux` into `master`

## Merge Considerations

As of 2026-06-09:

- Current branch: `agent-dashboard-ui-ux`
- Base branch present locally: `master`
- The working tree contains substantial uncommitted dashboard work plus many screenshot artifacts.

Before merge:

1. Curate which screenshots are final promotional assets versus temporary validation captures.
2. Exclude `.playwright-mcp/` from version control.
3. Create one or more coherent commits instead of merging the entire dirty tree blindly.
4. Merge into `master`, not `main`, because this repo currently uses `master`.

