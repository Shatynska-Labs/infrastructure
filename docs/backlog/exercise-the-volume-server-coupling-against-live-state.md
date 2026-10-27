---
kind: fix
waits_on: []
design_with: [decide-whether-the-data-volume-should-survive-a-server-toggle]
recorded_by: make-openspec-validation-a-usable-gate
re_checked: 2026-10-27
---

*Conditional Prod Volume Creation* (`openspec/specs/iac-data-volumes/spec.md`) states its toggle scenarios, and not all have been run against live state. The module tests under `terraform/modules/volume/tests/` cannot reach a stack's `count`.

Staging's half was observed on 2026-09-16 by `write-and-rehearse-the-rebuild-runbook` (`server_enabled = false` planned `0 to add, 0 to change, 3 to destroy`: server, firewall and volume; the apply destroyed the volume first). That also settled where the reads can run: the pull request's own plan job, which needs no local HCP credential (the workstation's credential belongs to another organisation). Production's server toggle no longer reaches its volume (`record-basis-api-durable-store`: `count = var.volume_enabled ? 1 : 0`), and that change observed it: its task 1.5's plan-only pull request (#288) set `server_enabled = false` and planned `0 to add, 0 to change, 2 to destroy`, server and firewall, the volume unchanged. What remains is production's `volume_enabled = false`: one plan-only read on a pull request that is read and closed, **never merged or applied**, since the volume now holds `basis-api`'s store.

- **Kind**: No delta, no decision. It runs an existing scenario as a plan and records the result.
- **Design with**: `decide-whether-the-data-volume-should-survive-a-server-toggle`, which would change the coupling these reads exercise.
- **Recorded by**: `make-openspec-validation-a-usable-gate`, which recovered it from `add-prod-data-volume`'s unticked task 3.5 (now under that archive's `## Not performed`), where it would otherwise have been lost.
