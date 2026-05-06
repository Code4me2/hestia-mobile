# Integration Manifest

`mobile-stack.json` is the machine-readable source of truth for the current Hestia Mobile integration target.

It records:

- component repository paths, remotes, owners, and expected branches;
- backend node name;
- live health endpoints;
- local phone sockets and user services;
- health fields that are blocking versus currently non-blocking.

Validate it with:

```bash
python3 scripts/validate-mobile-stack.py --config mobile-stack.json
```

Use it before cross-repo work to answer:

```text
Which branch should each component repo be on?
Which endpoint should probes use?
Which health failures are blockers?
Which service/socket names are expected on the phone?
```

The manifest intentionally uses Tailscale MagicDNS names such as `tiny-emerson` instead of hard-coded 100.x addresses.
