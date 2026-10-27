---
kind: change
waits_on: []
waits_for: "Basis's `move-to-durable-data-storage` reaching production, with its first backups' metrics files written; and Basis stating that its production relational data has no non-durable table."
design_with: []
recorded_by: record-basis-api-durable-store
re_checked: 2026-10-25
---

Once `Shatynska-Labs/basis`'s `move-to-durable-data-storage` has moved production's data into `basis-api`'s own PostgreSQL container (`/mnt/main/applications/basis-api/postgres`, admitted by `record-basis-api-durable-store`), two things are left here. First, retire production's shared-instance `basis-api` database and role and the `probe_public_key` of the `basis-api` entry in `ansible/inventory/host_vars/main-production.yml`, which only that database used; staging keeps all three. Second, declare `basis-api`'s backups as expected on `main-production`, so that a backup that never writes its metrics file, or whose file is deleted, alerts too: today `BackupStale` (`platform/docker-compose.yml`) covers only a backup that has succeeded once, because a rule on a missing series needs the set of stores each host expects (*A Backed-Up Store's Backup Age Is Alerted On*, `openspec/specs/iac-platform-services/spec.md`). **It must not** drop the shared-instance database's contents unless the operator decides so against Basis's `retire-the-health-connect-intake`, and must not retire it while any of Basis's production relational data is non-durable, which *Single Shared PostgreSQL Instance, Per-Application Databases* keeps in the shared instance.

- **Kind**: It owes an `iac-platform-services` delta for the expected-stores declaration and its alert, and the operator's decision on the shared-instance database's contents.
- **Recorded by**: `record-basis-api-durable-store`, which records the store, decouples production's volume and alerts on backup age; retiring the database waits on the move, and declaring the backups before they exist would alert from the moment of merge.
