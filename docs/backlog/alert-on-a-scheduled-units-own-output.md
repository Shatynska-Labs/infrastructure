---
kind: change
waits_on: []
design_with: [notice-a-pending-reboot-and-decide-what-does-it]
recorded_by: report-refused-removals-in-the-host-prune
re_checked: 2026-10-27
---

`prune-host-images` writes its outcome to the journal and nothing reads it. The dead-man's switch covers the unit not running, not what a successful run reported, so a prune that refuses the same image weekly, or whose `considered` count collapses, is green. The sharpest case: a runtime that stops responding mid-loop leaves the prune reporting every remaining candidate refused and still exiting zero, so the heartbeat goes green on a half-done run (signature in `ansible/roles/image_prune/README.md`, which cites this entry).

Mechanism: node-exporter's textfile collector, with rules in the inline `prometheus_rules`. Node-exporter's textfile collector is enabled since `record-basis-api-durable-store`, but over `/mnt/main/applications/*/metrics` only, for applications' backup metrics; a host unit's metrics need a directory that glob reaches, or the glob widened, and the file contract in `docs/onboard-an-application.md` §3.1 (temporary name, `chmod 0644`, rename; identical or absent help text) applies to them too. Decide whether the prune script writes the textfile (making metrics part of a script governed by *A Run That Cannot Determine the Keep Set Completely Removes Nothing*) or a wrapper does (a second thing that can silently stop). Shape it for every scheduled host unit, not the prune alone.

- **Kind**: It needs the script-or-wrapper decision, spans a role, a collector directory and alert rules, and owes deltas to `iac-host-configuration` and `iac-platform-services`.
- **Recorded by**: `report-refused-removals-in-the-host-prune`, which found `image_prune`'s README already citing this deferral without a record; out of a reporting change's scope.
