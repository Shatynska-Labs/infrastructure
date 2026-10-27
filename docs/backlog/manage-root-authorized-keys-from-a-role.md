---
kind: change
waits_on: []
design_with: [revoke-an-application-s-deploy-authorisation]
recorded_by: apply-host-configuration-through-a-gated-workflow
re_checked: 2026-10-19
---

No role manages `root`'s `authorized_keys`: its first entry comes from Hetzner at server creation (`hcloud_server.ssh_keys` cannot change without recreating the server), and each stack's `ansible-ci` converge key is appended by hand at `docs/bootstrap-a-new-host.md` §6.6. Revoking the most powerful credential CI holds is therefore an edit on the host rather than a commit.

A role owning that file can lock every operator out, a different class of risk from anything `hardening` does, so it wants scenarios of its own. Follow `ops_user`'s per-entry `state:` model (revocation is `state: absent`, entry left in place until a converge removes it). Only `exclusive: true` actually revokes, and that is the form that can lock everyone out. The first installation stays manual whatever the shape; the change buys every one after.

- **Kind**: It owes an `iac-host-configuration` requirement for a role owning `root`'s keys, and carries lockout risk too large for a fold-in.
- **Design with**: `revoke-an-application-s-deploy-authorisation` (same revocation shape and `exclusive` trade-off).
- **Recorded by**: `apply-host-configuration-through-a-gated-workflow`, which installs the converge key and cannot revoke it; not done there because of the lockout risk.
