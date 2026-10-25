---
kind: fix
waits_on: []
design_with: [decide-whether-the-data-volume-should-survive-a-server-toggle]
recorded_by: make-openspec-validation-a-usable-gate
re_checked: 2026-10-19
---

`terraform/stacks/main-production/main.tf` couples the volume to the server (`count = var.volume_enabled && var.server_enabled ? 1 : 0`). *Conditional Prod Volume Creation* (`openspec/specs/iac-data-volumes/spec.md`) states two scenarios, *Volume toggle disabled creates nothing* and *Disabling the server also removes the volume*, that nothing has run against production's live state. The module tests under `terraform/modules/volume/tests/` cannot reach a stack's `count`.

Staging's half was observed on 2026-09-16 by `write-and-rehearse-the-rebuild-runbook` (`server_enabled = false` planned `0 to add, 0 to change, 3 to destroy`: server, firewall and volume; the apply destroyed the volume first). That also settled where the reads can run: the pull request's own plan job, which needs no local HCP credential (the workstation's credential belongs to another organisation). What remains is production, where no backup covers the volume: two plan-only reads (each toggle set false in turn) on a pull request that is read and closed, **never merged or applied**.

- **Kind**: No delta, no decision. It runs two existing scenarios as plans and records the result.
- **Design with**: `decide-whether-the-data-volume-should-survive-a-server-toggle`, which would change the coupling these reads exercise.
- **Recorded by**: `make-openspec-validation-a-usable-gate`, which recovered it from `add-prod-data-volume`'s unticked task 3.5 (now under that archive's `## Not performed`), where it would otherwise have been lost.
