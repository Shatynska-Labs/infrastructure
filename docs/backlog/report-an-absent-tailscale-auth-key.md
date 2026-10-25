---
kind: change
waits_on: []
design_with: []
recorded_by: fix-volume-discovery-and-consistency
re_checked: 2026-10-19
---

*A Role's Absent Required Input Is Reported by Name* (`iac-host-configuration`) is scoped to inputs consumed on every run; `tailscale_auth_key` is the excluded class. It is consumed only by *Bring the host onto the tailnet*, under a `when:` that skips an already-joined host, so an unconditional assertion would break every re-converge.

The diagnostic must fire under the same four-limb condition as the join, stated once; reading its `POLARITY` comment wrong silently stops a host joining the tailnet, which the deploy pipeline depends on. The consuming task's `no_log: true` censors an absent key into a redacted error. `host-converge.yml` passes `tailscale_auth_key=''` on every converge by design, so "undefined" and "empty" differ: firing on undefined never fires for the pipeline, and firing on empty fires on every pipeline converge. The trigger is the join condition itself. The role has no Molecule scenario; this change brings its first.

- **Kind**: It owes a delta to *A Role's Absent Required Input Is Reported by Name* for a conditionally consumed input, and needs the absent-versus-empty decision.
- **Recorded by**: `fix-volume-discovery-and-consistency` (its `design.md` Decision 3a), whose requirement deliberately excluded conditionally consumed inputs.
