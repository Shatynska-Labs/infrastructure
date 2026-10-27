---
kind: change
waits_on: []
waits_for: "durable data landing on `main-staging`'s data volume, i.e. a store there that *No Store on This Host Holds Data Requiring Backup* cannot classify as needing no backup."
design_with: [exercise-the-volume-server-coupling-against-live-state]
recorded_by: write-and-rehearse-the-rebuild-runbook
re_checked: 2026-10-27
---

`main-staging` couples its data volume to its server (`count = var.volume_enabled && var.server_enabled ? 1 : 0`), so `server_enabled = false` discards the volume, which has no Hetzner backup; the server's backups reach the root disk only. `add-prod-data-volume`'s design accepted this deliberately. The 2026-09-16 rehearsal showed the apply destroys the volume **first**, before the server. Decoupling would give the volume its own `location` and gate it on `volume_enabled` alone; the cost is not money (tens of cents a month) but the toggle's meaning (`terraform/stacks/main-staging/variables.tf`: `server_enabled` is "the way to stop paying for staging without deleting its configuration").

`main-production` no longer does: `record-basis-api-durable-store` gave its volume a `location` of its own and gated it on `volume_enabled` alone, delivered with `basis-api`'s backups, so this entry is staging's alone. It is not worth doing while *No Store on This Host Holds Data Requiring Backup* (`openspec/specs/iac-safety-hardening/spec.md`) holds: nothing on the volume is durable. **Must not undo**: when durable data lands on a host, decoupling and a real backup are owed together; decoupling alone looks like protection while protecting against nothing.

- **Kind**: It owes an `iac-safety-hardening`/stack delta and the operator's decision on the toggle's meaning, delivered with a backup.
- **Recorded by**: a question during `write-and-rehearse-the-rebuild-runbook`'s rehearsal (2026-09-16), once the destroy had shown what the coupling does; deliberately deferred as not yet worth doing.
