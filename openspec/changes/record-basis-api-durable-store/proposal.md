## Why

`Shatynska-Labs/basis` decided, in its ADR-0014 (change `choose-durable-data-storage`, archived 2026-10-25), that Basis's durable production data lives in a PostgreSQL container of Basis's own on `main-production`, its data on the host's attached data volume, backed up off-host by a daily encrypted `pg_dump` and by continuous WAL archiving with base backups, and admitted only once a restore from each has been rehearsed and checked. Basis's `move-to-durable-data-storage` performs that move and waits on this repository for three things ADR-0014 assigns here:

- **recording the store** — *No Store on This Host Holds Data Requiring Backup* (`openspec/specs/iac-safety-hardening/spec.md`) admits a store that needs a backup only under its fallback, and says an application's store is recorded "in the change here that records it"; `docs/onboard-an-application.md` §3.1 still says no application has cleared that bar;
- **decoupling `main-production`'s data volume from its server toggle** — today `server_enabled = false` destroys the volume, first, and the server's backups do not reach it. `docs/backlog.md` `decide-whether-the-data-volume-should-survive-a-server-toggle` deferred this until durable data lands, and says decoupling and a real backup are owed together;
- **an alert on backup age** through the platform's alerting, so that backups cannot stop silently.

## What Changes

- **The store is recorded.** *No Store on This Host Holds Data Requiring Backup* names `basis-api`'s production PostgreSQL store as admitted under the fallback, states the backup it relies on and where the evidence of its rehearsed restores lives (Basis's `move-to-durable-data-storage`), and replaces the sentence expecting all durable application data to live in an external managed service with the two routes the requirement already allows. `docs/onboard-an-application.md` §3.1 says the same.
- **`main-production`'s volume survives its server toggle.** The volume module takes an optional `location`, of which it requires exactly one with `server_id` (Hetzner's client refuses a create naming both); `main-production` passes its stack location only while `server_enabled` is false, and gates the volume on `volume_enabled` alone. With the server disabled the volume is detached and kept; re-enabling attaches it to the new server. The existing volume is not replaced: its state already holds `hel1`, and the server reference is unchanged while the server exists. **`main-staging` keeps the coupling**: it holds no durable data, and its toggle keeps meaning "stop paying without deleting configuration". `docs/runbook-rebuild.md` states that production's toggle route now keeps the volume.
- **A directory tree for the application on the volume.** `platform_data_volume` also creates host-scoped subdirectories declared in a host's own vars file. `main-production` declares `applications/basis-api/postgres` (`999:999`, `0700`, the Debian-based PostgreSQL image's user) and `applications/basis-api/metrics` (`999:999`, `0755`), under root-owned parents. Every host gets an empty `applications/platform/metrics` from its environment's list, so the collector's glob always matches.
- **Backup age is alerted on.** node-exporter's textfile collector is enabled over `/mnt/main/applications/*/metrics`, read through its existing read-only root mount. An application writes `backup_last_success_timestamp_seconds` and `backup_max_age_seconds`, labelled `store` and `kind`, into its own metrics directory, world-readable. Four platform rules: `BackupStale` (a last success older than its declared maximum age), `BackupAgeUnbounded` (a timestamp with no declared maximum), `TextfileMetricsUnreadable` (the collector failing to read a file), `NodeExporterGatheringErrors` (a series collected twice, which the collector itself drops silently). They route to Slack like every other rule.
- **Backlog.** A new entry, `finish-basis-api-s-move-to-its-own-database`, for what follows Basis's move: retiring production's shared-instance `basis-api` database, role and probe key, and declaring `basis-api`'s backups as expected so that their absence alerts too. The retirement waits on Basis stating that none of its production relational data is non-durable, since non-durable relational data belongs in the shared instance.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `iac-safety-hardening`: *No Store on This Host Holds Data Requiring Backup* records the first application store admitted under the fallback, and what such a store owes beyond the backup: a volume that survives the server toggle, and a watched backup age.
- `iac-data-volumes`: *Conditional Prod Volume Creation* and *Volume Attached to Prod Server at Creation* — `main-production`'s volume carries its stack's location and exists by its own toggle.
- `iac-server-lifecycle`: *Conditional Prod Server Creation* — disabling the server detaches the volume rather than destroying it.
- `iac-host-configuration`: *Platform Data Volume Is Mounted at a Fixed Host Path* — host-scoped application subdirectories.
- `iac-platform-services`: new requirement *A Backed-Up Store's Backup Age Is Alerted On*.

## Workstream

This repository has no workstreams. In `Shatynska-Labs/basis` it serves the `reach-the-calibration-period` workstream, through `move-to-durable-data-storage`.

## Not in this change

- **The bucket, its lifecycle rules, the write-only credential, and the verification of Hetzner Object Storage's versioning, object lock and lifecycle features** — Basis's `move-to-durable-data-storage`, by the operator's decision (2026-10-25). Hetzner issues Object Storage credentials from its console only.
- **The PostgreSQL container, the backup tooling and the restore rehearsals** — Basis's, in its production Compose stack.
- **Retiring production's shared-instance `basis-api` database, role and probe key**, and the alert on an expected backup being absent — the new backlog entry above; neither gates Basis's move.
- **Any other store of Basis's on this host**, such as the Redis container ADR-0014 classifies as needing no backup. `move-to-durable-data-storage` adds PostgreSQL only; a Basis change that adds another store on a host is recorded by a change here, with its reason, as *No Store on This Host Holds Data Requiring Backup* requires.
- **Staging** — unchanged: it keeps its data in the shared instance (`docs/onboard-an-application.md` §3.1), and its volume stays coupled.

## Impact

- `terraform/modules/volume/` (an optional `location`, a nullable `server_id`), `terraform/stacks/main-production/main.tf`, `variables.tf` and `outputs.tf`. The production plan is expected to show **no change** to any resource.
- `ansible/roles/platform_data_volume/` (a second, host-scoped subdirectory list, and its README), `ansible/inventory/group_vars/{production,staging}.yml` and `ansible/inventory/host_vars/main-production.yml`. Production's converge waits for the operator's approval, and nothing announces that it is waiting.
- `platform/docker-compose.yml`: one node-exporter flag and four rules; a platform deploy to both hosts. On staging the glob matches only the empty platform directory.
- `docs/onboard-an-application.md`, `docs/runbook-rebuild.md`, `docs/backlog.md`.
