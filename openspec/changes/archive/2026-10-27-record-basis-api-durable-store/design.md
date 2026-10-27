## Context

Basis's ADR-0014 puts Basis's durable production data in a PostgreSQL container of its own on `main-production`, on the attached data volume, with two off-host backups and rehearsed restores before data lands. The rules that bound it here are *No Store on This Host Holds Data Requiring Backup* (`openspec/specs/iac-safety-hardening/spec.md`), *Single Shared PostgreSQL Instance, Per-Application Databases* (`openspec/specs/iac-platform-services/spec.md`, untouched: the shared instance still admits no durable data), and `docs/onboard-an-application.md` §3.1. The operator settled four questions on 2026-10-25, recorded as decisions 2–5 below.

## Goals / Non-Goals

**Goals:** record the store; make `main-production`'s volume survive the server toggle without replacing the existing volume; give the application a directory on the volume before its container needs it; alert on backup age through Prometheus and Alertmanager.

**Non-Goals:** the bucket, credential, backup tooling, container or rehearsals (Basis's); retiring the shared-instance `basis-api` database (after the move); staging.

## Decisions

### 1. The store is admitted under the fallback, conditionally on evidence held in Basis

The requirement says a store added outside this repository states its reason in the change here that records it. This change does that, and also writes the admission into the requirement itself, because the requirement currently says durable application data "is expected to live in an external managed service" — a sentence a later reader would take as contradicting the store. The admission is conditional on what the requirement already demands: Basis's data lands only once the dump restore and a point-in-time restore from the WAL archive have been rehearsed on representative data and checked, both procedures written down, recorded in Basis's `move-to-durable-data-storage`. Nothing here can verify that before this change archives; the record says where the evidence is, and the operator's confirmation of Basis's rehearsal is Basis's gate, not this one.

**Store reason, as the requirement asks:** `basis-api`'s production PostgreSQL data (`/mnt/main/applications/basis-api/postgres`) meets none of the needs-no-backup reasons; it is admitted by a daily encrypted `pg_dump` and continuous WAL archiving with base backups, both written to Hetzner Object Storage outside `hel1`, with rehearsed, checked restores in place before data lands. Its metrics directory (`…/basis-api/metrics`) holds the latest backup timestamps only, rewritten on each backup. It is classed non-durable by a policy the requirement now states: its loss is tolerable to the operator, because the next backup run rewrites it, and until then the alerts it feeds are silent rather than wrong. The platform's empty `applications/platform/metrics` holds nothing.

### 2. The backup-age alert uses node-exporter's textfile collector

Alternatives: Prometheus scraping a Basis sidecar would put a monitoring service on a network an application joins, against *Monitoring Services Are Not Reachable From Application Containers*; an external heartbeat bypasses the platform's alerting that ADR-0014 names. The textfile collector needs no new network and no new mount: node-exporter already mounts `/` read-only at `/host/root`, and `prom/node-exporter:v1.12.1` documents `--collector.textfile.directory` as glob-capable and repeatable (checked with `--help` on 2026-10-25). The flag is `--collector.textfile.directory=/host/root/mnt/main/applications/*/metrics`.

**The glob must always match.** Measured against `prom/node-exporter:v1.12.1` on 2026-10-25: a glob matching no directory sets `node_textfile_scrape_error 1` (the collector falls back to opening the literal pattern), while a matched empty directory reads `0`. So every host carries an empty, root-owned `applications/platform/metrics` from the environment's own `platform_data_volume_subdirs`, and the alert on an unreadable file means a real read failure. The image runs as `nobody` (`65534`), also measured, which is why the contract requires world-readable files.

The application writes files; it never reaches node-exporter. Each application has its own directory, so it cannot overwrite another's file. It can still emit a series labelled for another store. **Two files emitting the same series are not reported by the textfile collector**: measured against v1.12.1 on 2026-10-25, one value is served, the other dropped, `node_textfile_scrape_error` stays `0`, and node-exporter's own `promhttp_metric_handler_errors_total{cause="gathering"}` increments. A fourth rule watches that counter, because a dropped duplicate could mask a stale backup behind a fresh one, or the reverse.

**Metric contract**, which Basis's backup jobs implement:

- `backup_last_success_timestamp_seconds{store, kind}` — Unix time of the last successful backup of that kind;
- `backup_max_age_seconds{store, kind}` — the age beyond which it is overdue.

`kind` is free text chosen by the application (Basis: `dump`, `wal`, `base`). The threshold is the application's because the recovery targets are (ADR-0014: at most 5 minutes lost, daily dumps). Files are written atomically (write a temporary file in the same directory, then rename), as the collector requires; a file not ending in `.prom` is ignored, which is what makes the temporary file safe. Files SHALL be readable by others (`0644`): node-exporter runs as `nobody`, and `mktemp` creates `0600`, so a `chmod` precedes the rename. `# HELP` and `# TYPE` lines SHALL be omitted or byte-identical across every file emitting a metric name: measured against v1.12.1 on 2026-10-25, two files giving one name different help text set `node_textfile_scrape_error 1` and the second file's series are dropped. Basis's dump, WAL and base jobs writing separate files would otherwise trip it.

**Rules:**

- `BackupStale`: `time() - backup_last_success_timestamp_seconds > on(store, kind) backup_max_age_seconds`, `for: 10m`.
- `BackupAgeUnbounded`: `backup_last_success_timestamp_seconds unless on(store, kind) backup_max_age_seconds`, `for: 1h` — a timestamp nobody can judge.
- `TextfileMetricsUnreadable`: `node_textfile_scrape_error == 1`, `for: 15m`.
- `NodeExporterGatheringErrors`: `increase(promhttp_metric_handler_errors_total{job="node-exporter", cause="gathering"}[15m]) > 0` — a series collected twice, from two textfiles or any collector.

**Absence is not alerted on yet.** A rule firing on a missing series needs to know which stores are expected, and declaring `basis-api`'s now would fire from merge until Basis's first backup. The staleness rule already covers backups that stop, because the last file stays and ages; what it misses is a file never written or deleted. Declaring expected stores is part of `finish-basis-api-s-move-to-its-own-database`, which follows the move.

### 3. Only `main-production`'s volume is decoupled

The volume module gains an optional `location` and its `server_id` becomes nullable; it forwards both as given and validates that exactly one is non-null. hcloud-go v2.52.0, which provider v1.70.0 pins, refuses a create naming both (`VolumeCreateOpts.Validate`, `mutuallyExclusiveFields("Server", "Location")`). **The stack chooses between them on a value known at plan time**, `var.server_enabled`: `main-production` passes `server_id = one(module.server[*].id)` and `location = var.server_enabled ? null : var.location`, with `count = var.volume_enabled ? 1 : 0`. A condition on `server_id` itself would not do: on re-enable `server_id` is a server not yet created, unknown at plan time, so the condition and therefore `location` would be unknown — and an unknown value on a `ForceNew` attribute plans a replacement of the volume. Read against `hetznercloud/hcloud` v1.70.0's `internal/volume/resource.go`:

- `location` is `Optional, Computed, ForceNew`, and read back from the API. With the server enabled the stack passes null, which a `Computed` attribute does not diff; with it disabled it passes `hel1`, which state already holds. Both values are known at plan time in every transition — steady, toggle-off and re-enable — so none plans a change to `location` or a replacement.
- `server_id` is `Optional, Computed`; with the server enabled it is unchanged. With the server disabled it is null in configuration, which a `Computed` attribute does not diff, so Terraform plans only the server's destruction. Hetzner detaches a volume when its server is deleted. On re-enable, the new id differs and the provider's update attaches the volume.
- The address stays `module.volume[0].hcloud_volume.this`: no `moved` block.

Alternative considered: a separate `hcloud_volume_attachment`, which is the provider's documented decoupled form. It would need the existing attachment imported, adds a resource whose create on an attached volume fails, and buys nothing the nullable reference does not.

`main-staging` is unchanged: it holds no durable data, and decoupling there would change what its toggle means ("stop paying without deleting configuration") for nothing.

**Not exercised live.** The detach-on-delete and attach-on-re-enable path is not run against production in this change; toggling production's server off is an outage. What is checked: the production plan shows no change; a plan-only pull request setting `server_enabled = false`, closed unmerged, shows the server and firewall destroyed and the volume untouched; and module tests can assert what the module forwards for each input, though not the stack's `count` nor Terraform's retention of a `Computed` value. Observing the detach and re-attach on a live host stays with `docs/backlog.md` `exercise-the-volume-server-coupling-against-live-state`, whose production half this change rewrites.

### 4. Application subdirectories are host-scoped

`platform_data_volume_subdirs` lives in `group_vars/<environment>.yml`, because the platform's services are on every host. An application's directory is a property of the host it is deployed to — *A Host-Scoped Variable Lives in the Host's Own Vars File* — so a second list, `platform_data_volume_host_subdirs`, comes from `host_vars/main-production.yml`, defaults to empty, and is created by the same task after the environment's list and after the mount. Same entry shape (`path`, `owner`, `group`, `mode`). Lists are not merged across Ansible's precedence levels, which is why it is a second variable rather than a second definition of the first.

The environment's own list, in both `group_vars` files, gains `applications`, `applications/platform` and `applications/platform/metrics` (all `root:root 0755`) — the collector's always-present match (decision 2). The host list's entries, in order: `applications/basis-api` (`root:root 0755`), `applications/basis-api/postgres` (`999:999 0700`), `applications/basis-api/metrics` (`999:999 0755`). `999` is the Debian-based official `postgres` image's user (Alpine tags use `70`; the `host_vars` comment says the owner follows Basis's image variant), which Basis's container and its archive and dump jobs run as; Basis's Compose binds the first at the image's data path and the second wherever its jobs write. The `applications/` prefix keeps applications out of the platform's own subdirectories and gives the collector's glob one level to match.

### 5. The bucket is Basis's

Basis's backlog entry already lists the bucket, lifecycle rules, credential and feature verification as its own work, and the credential can only be issued in Hetzner's console. This repository has no Object Storage provider and gains none.

### 6. The rebuild runbook

`docs/runbook-rebuild.md` phases 3 and 4 describe a toggle route rehearsed on staging, where the volume goes with the server. For production that is no longer true: the plan destroys two things, not three, the volume id is unchanged, and the platform's own stores on it (shared instance, Prometheus, Grafana) survive the rebuild. Phase 1's statements that no store needs a restore and that stores come back empty are also wrong for production: there, a lost volume means a restore of `basis-api`'s store from Basis's backups, performed in Basis's repository. Phases 11, 14 and 16 assume the shared instance came back empty (recreate `pgexporter`, re-provision with `rotate=yes`, expect empty data), which on production's toggle route is false: the instance and its roles survive, and only a lost volume brings that back. Phase 1's expected alarms gain `BackupStale` for production, since metrics files age while the host is down. The runbook says so in phases 1, 3, 4, 11, 14 and 16, without re-recording its staging rehearsal.

## Risks / Trade-offs

- **The detach-and-reattach path is reasoned from provider source, not observed.** → The production plan must show no change; the path is first exercised by a deliberate rebuild, tracked by the existing backlog entry.
- **Production now pays for a volume while its server is off.** Tens of cents a month.
- **The platform's own stores on production's volume now outlive a server toggle.** They still need no backup; they simply survive more often. No store's reason rests on being destroyed.
- **An application can forge another store's series.** → A collision is reported by `NodeExporterGatheringErrors`; forging without collision is accepted on a single-operator host.
- **No alert on a backup that never wrote a file** until the follow-up entry. → `BackupStale` covers every backup that has succeeded once.

## Migration Plan

1. Merge: the production plan shows no change and its apply waits for approval; the converge creates the directories; the platform deploy adds the flag and rules to both hosts. **The converge should land before the platform deploy, or within `TextfileMetricsUnreadable`'s 15 minutes after it**: until `applications/platform/metrics` exists on a host the glob matches nothing there and the alert would fire. A late converge costs one false alert that resolves on its own.
2. Basis's change then creates its container on the directory, its backups, and the metrics files; its rehearsals precede any durable data.

Rollback: revert the pull request. The Terraform revert is again a no-op plan; the directories are empty until Basis uses them.
