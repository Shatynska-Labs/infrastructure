---
kind: change
waits_on: []
design_with: [manage-root-authorized-keys-from-a-role]
recorded_by: onboard-commerce-ops-to-staging
re_checked: 2026-10-19
---

`deploy_user` renders, per `deploy_apps` entry, `/opt/<name>`, `/etc/sudoers.d/app-deploy-<name>`, `/etc/sudoers.d/app-probe-<name>` and two `authorized_keys` lines (deploy and probe keys, each with a forced command), and removes none of them when the entry is deleted. `authorized_key` leaves `exclusive` at its default deliberately, so no application's entry disturbs another's. So deleting an entry leaves the host authorising that key as before; revocation is an edit on the host or a key rotation in the application's repository, neither of which a converge notices.

Follow `ops_user`'s per-entry `state:` model (`state: absent`, entry left in place until a converge has removed it); only `exclusive: true` actually revokes, and it can lock everyone out. `remove-commerce-ops-from-staging` needed this once (2026-10-18) and cleaned the host by hand instead (its `design.md` Decision 1), judging one revocation on one host not worth the mechanism; `remove-commerce-ops-from-production` needed it again (2026-10-19) and made the same judgement (its `design.md` Decision 1).

- **Kind**: It owes a delta to *Restricted Deploy Account Supports Per-Application Forced-Command Deploys* (`iac-host-configuration`) for revocation, and needs the `exclusive`-versus-per-entry decision.
- **Recorded by**: `onboard-commerce-ops-to-staging` (2026-09-13), which found nothing takes a `deploy_apps` entry back while stating what reverting it would cost; out of an onboarding change's scope.
