---
kind: change
waits_on: []
design_with: [make-a-rotated-secret-reach-its-inline-config, make-a-rotated-grafana-password-reach-grafana, label-each-stack-s-alerts-with-the-stack-they-came-from]
recorded_by: write-and-rehearse-the-rebuild-runbook
re_checked: 2026-10-19
---

`docs/bootstrap-a-new-host.md` §7.5 asks the operator to confirm the two stacks hold different per-stack secrets (two Grafana logins with different passwords, a test alert arriving in one channel only). It had never been performed; when it was (2026-09-16), production and staging shared the Slack webhook (production's alerts were landing in the staging workspace), the dead-man's-switch URL and the Grafana admin password. All three are now separated (`apply-the-per-stack-alert-routing`, PR #244, 2026-09-16; `give-each-stack-its-own-grafana-password`, 2026-09-17, rotating staging's only), and §7.5 then passed.

What remains is a repeatable check. These are GitHub Environment secrets, invisible to `.github/tests`, Molecule and review; the only defence is a runbook step read once, which is what let three values sit shared for weeks. A probe across the two running hosts is the workable shape, and it needs a home. It must compare what the hosts **accept**, not only what they hold: on 2026-09-17 Grafana held a new password and accepted the old one.

- **Kind**: It needs a decision on where a cross-host probe lives and whether the separation is worth asserting repeatably, and owes a delta for it.
- **Recorded by**: the rebuild rehearsal's pre-state capture (2026-09-16) during `write-and-rehearse-the-rebuild-runbook`; the three values were fixed as fixes, and the repeatable check is a change of its own.
