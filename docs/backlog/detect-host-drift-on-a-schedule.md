---
kind: change
waits_on: [report-an-absent-tailscale-auth-key]
waits_for: "`report-an-absent-tailscale-auth-key`, which brings the `tailscale` role its first Molecule scenario; checkable as `ansible/roles/tailscale/molecule/` existing."
design_with: []
recorded_by: apply-host-configuration-through-a-gated-workflow
re_checked: 2026-10-19
---

Nothing reports what a host has drifted to between converges; the host layer is the only one without that (`drift.yml` sweeps Terraform nightly; the platform stack is redeployed on every merge). A scheduled `--check --diff` against each host is the host layer's `drift.yml`. It cannot live in the converge workflow, since a pre-approval job must hold no credential that reaches a host and check mode must authenticate.

It cannot ship on today's baseline: the `tailscale` role's two `get_url` tasks (*Add the Tailscale apt signing key*, *Add the Tailscale apt repository*) have no `checksum:` and report changed under `--check` forever, so a healthy host reads `changed=2`. Remedies: pin a checksum (upstream rotates the key), replace `get_url` with something check-mode-verifiable, or filter those two by name with the reason stated. Check mode also skips `command` tasks (`ops_user`, `swap`) and `geerlingguy.docker` ignores errors in check mode, so a clean check speaks for files and packages, not the host; the report must say so where it reports. `docs/bootstrap-a-new-host.md` §6.3 states the `changed=2` baseline and changes when this lands.

Shape it as `drift.yml`'s sibling: scheduled, per environment, one deduplicated issue per environment, and a liveness report (*Scheduled Workflows Report Their Own Liveness*).

- **Kind**: It adds a scheduled workflow owing an `iac-cicd-pipeline` delta and needs a decision on the `get_url` remedy.
- **Recorded by**: `apply-host-configuration-through-a-gated-workflow` (its `design.md` Decision 10), which made it possible and declined it because a check-mode run needs a host credential the pre-approval job must not hold.
