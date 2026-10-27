## MODIFIED Requirements

### Requirement: No Store on This Host Holds Data Requiring Backup
Every store in which a platform-stack service or an application deployed to this host persists data outside its container's writable layer — any volume, named or anonymous, including one an image declares rather than the stack definition, or a host bind mount — SHALL be one that needs no backup of its own — either its contents are recoverable without one, or their loss is acceptable under a policy recorded here — unless the logical backup and rehearsed restore described below are in place before its data lands. For a store needing no backup, the reason SHALL be one of the following, or — where a store's contents divide — one of them for each part, with the division stated:

- its contents are bounded by a rolling retention the service enforces on itself;
- its contents are reproduced from this repository by a redeploy;
- its contents are re-issued on demand by an external authority;
- its contents are derived from a source that still exists, and are regenerated in use without a copy being restored — the source SHALL be named where the reason is stated, and SHALL itself either satisfy this requirement or live outside this host under backups of its own;
- its contents are non-durable by a policy recorded as a requirement in this repository's specifications, which states whose loss that policy treats as tolerable.

Host system state outside those stores — the converged filesystem, the container runtime's own state — is not in scope here: it is reproduced by convergence and by redeploy, and is separately covered by *Data Durability for Stateful Resources*.

Where data is placed in such a store and meets none of those reasons, a logical backup of it written outside this host, together with a restore rehearsed on representative data whose result was checked, SHALL be in place **before** that data first lands — not after.

This fallback reaches every store on this host **except** the shared PostgreSQL instance, which admits no durable data at all under *Single Shared PostgreSQL Instance, Per-Application Databases* (`openspec/specs/iac-platform-services/spec.md`) — a prohibition no backup lifts, because that instance's classification above depends on it holding unconditionally.

The platform stack's stores **as this change leaves them**, and the reason each satisfies this requirement. The census was re-read from both hosts on 2026-09-16 with `docker volume ls` and each container's mounts rather than from the stack definition — that reading is what the four unchanged rows rest on, and the shared instance's row names the location this change moves it to rather than the one that reading found:

| Store | Reason |
|---|---|
| The shared PostgreSQL instance's data (`/mnt/main/postgres`) | Non-durable by policy — *Single Shared PostgreSQL Instance, Per-Application Databases* (`openspec/specs/iac-platform-services/spec.md`) limits it to technical or temporary records whose loss is tolerable to the application that wrote them |
| Prometheus's time-series database (`/mnt/main/prometheus`) | Rolling retention it enforces on itself, bounded by both time and size |
| Grafana's data directory (`/mnt/main/grafana`) | Split, and both halves are covered: the datasource and the dashboards this repository provisions are reproduced by a redeploy, and the rest is non-durable under the dashboard-state policy stated below |
| Traefik's ACME storage — `traefik_letsencrypt`, on the host `platform_traefik_letsencrypt` | Certificates are re-issued on demand by the certificate authority |
| Alertmanager's state, in the anonymous volume its image declares at `/alertmanager` | Non-durable under the alerting-state policy stated below. This store is declared by the image rather than by the stack definition, which is why the scope above reaches an anonymous volume and why the table was built from the host rather than from `platform/docker-compose.yml` |

**Three of those five stores sit on the attached data volume and two on the root disk, and the split is not a durability ranking.** It follows from what each store costs to keep: Prometheus's database and the shared instance both grow with what the host does, and Grafana's sits there for the reason the change that moved it recorded, while what stays on the root disk — Traefik's ACME storage and Alertmanager's state — is small and re-issued or re-created. The consequence worth stating, because nothing else here would say it, is that the server's automatic backups reach the root disk alone — so a store on the volume is outside the only copy of anything this host takes. That is not a gap in this requirement: a store classified above needs no backup, and a store needing one owes the logical backup and rehearsed restore this requirement already demands, wherever it sits. It is stated so that the snapshot is not read as a safety net under a store it does not reach.

That table is the classification on one date and will age; the obligation above is what does not. A store added later SHALL state which of the reasons above it satisfies, in the artifacts of the change that adds it — or, where the store is added outside this repository, in the change here that records it. That is where the second scenario below finds a reason to test, and it costs no delta to this table. Such a store is in scope whether or not the table names it, and a store already named is in breach the moment its stated reason stops being true — a retention flag removed from Prometheus, the provisioning stanza that reproduces Grafana's dashboards deleted from `platform/docker-compose.yml` — whether or not any new data landed.

**Grafana state created outside this repository is non-durable.** Dashboards saved or edited through Grafana's own interface, and the users, preferences and annotations its internal database holds, SHALL be treated as data whose loss is tolerable **to the operator**, who is the only party that creates it, because committing a dashboard to the platform stack's definition is the mechanism by which a dashboard worth keeping is kept. The stack permits such edits — its dashboard provider sets `allowUiUpdates` true and `disableDeletion` false — so this is a standing property of that store rather than a hypothetical, and it is stated here rather than in the table above because the table is dated and this policy is not.

**Alerting state is non-durable.** Alertmanager's silences and its notification log SHALL be treated as data whose loss is tolerable **to the operator**: a lost silence lapses into a notification, which is the safe direction to fail in, and the notification log only suppresses repeats of an alert still firing.

This requirement is distinct from *Data Durability for Stateful Resources* in this capability, which requires the server's own automatic backups. Those are daily, crash-consistent, cover the root disk but not the attached data volume, and are retained on Hetzner's schedule; they shorten a rebuild and are a last-resort recovery of the root disk. They are not a substitute for a logical backup taken and restored per database, and their existence SHALL NOT discharge the obligation above.

Durable application data takes one of two routes, and no third. It lives in an external managed service that owns its own backups — that such a service's backups are in fact enabled and retained is a fact outside this repository: this requirement states the dependency, and nothing here verifies it — or it lives in a store of the application's own on this host, admitted under the fallback above. **The shared PostgreSQL instance is neither**, as stated above.

**A store admitted under the fallback owes two things beyond its backup.** It SHALL sit on a volume whose existence does not depend on the server's toggle, because a toggle that destroys the volume discards on an act meant only to stop a server what the backup exists to recover, and the server's own backups do not reach the volume (*Conditional Prod Volume Creation*, `openspec/specs/iac-data-volumes/spec.md`). And its backups' age SHALL be alerted on through the platform's alerting, because a backup that stops does so silently (*A Backed-Up Store's Backup Age Is Alerted On*, `openspec/specs/iac-platform-services/spec.md`). The backup, its storage and its restore rehearsal are the application's to perform and to record; the record here names the store, the backups it relies on, and where the evidence of its rehearsed restores is kept.

The application stores admitted under the fallback, recorded by the change in this repository that admitted each:

| Store | Backups | Evidence of the rehearsed restores | Recorded by |
|---|---|---|---|
| `basis-api`'s PostgreSQL data on `main-production` (`/mnt/main/applications/basis-api/postgres`), in a container of `Shatynska-Labs/basis`'s production Compose stack | A daily encrypted `pg_dump` of `basis-api`, and continuous WAL archiving with base backups, both written to Hetzner Object Storage in a location other than the server's (`hel1`) | `Shatynska-Labs/basis` change `move-to-durable-data-storage`, which SHALL record a checked restore from the dump and a checked point-in-time restore from the archive before durable data first lands | `record-basis-api-durable-store` |

**No other application has cleared the bar**, and a row here SHALL NOT be read as permission for another: a store is admitted only by one of the reasons above or by the backup and rehearsed restore above, as the scenario on precedent below states.

**Backup metrics directories are non-durable.** An application's metrics directory (`/mnt/main/applications/<application>/metrics`, `basis-api`'s among them) and the platform's empty one SHALL be treated as data whose loss is tolerable **to the operator**: they hold only the latest backup timestamps, rewritten by the next backup run, and their loss silences the backup-age alerts until then rather than making them wrong.

#### Scenario: A persistent store is added to the host
- **WHEN** a service that persists data outside its container's writable layer is added to the platform stack, or an existing service begins persisting there — including through a volume a bumped image newly declares — or an application deployed to this host persists data of its own in any volume — named or anonymous, declared by the stack definition or by the image — or in a host bind mount
- **THEN** that store SHALL be recoverable without a backup of it, for one of the reasons above
- **OR** a logical backup written outside this host, and a restore rehearsed on representative data whose result was checked, SHALL be in place before the store first holds data

#### Scenario: A store's stated reason ceases to hold
- **WHEN** a change would remove the property a classified store's reason rests on — the retention settings that bound Prometheus's database, or the provisioning from this repository that reproduces Grafana's dashboards
- **THEN** that change SHALL either preserve the property, or restate the store's reason as another of the reasons above, or put the backup and rehearsed restore above in place before it lands

#### Scenario: An application asks for durable storage on this host
- **WHEN** an application would keep data on this host whose loss would not be tolerable
- **THEN** it SHALL be directed to an external managed service that owns its own backups, unless the backup and the rehearsed restore above are already in place

#### Scenario: The stated divergence is not a precedent
- **WHEN** an application proposes keeping durable data on this host on the grounds that another application does or once did, or that this requirement states a divergence
- **THEN** that SHALL NOT be treated as permission, because a divergence is recorded as unmet rather than as allowed, and a store is admitted only by one of the reasons above or by the backup and rehearsed restore above

#### Scenario: A classified store moves between the host's disks
- **WHEN** a store named in the table above is relocated between the host's root disk and the attached data volume
- **THEN** the table SHALL name it at the location it then occupies, so that no row names a store the host no longer has
- **AND** its stated reason SHALL be reassessed against the reasons above rather than carried over unread, since a reason resting on where the store sits does not survive the move

#### Scenario: A store admitted under the fallback survives the server toggle
- **WHEN** a store admitted under the fallback sits on a stack's data volume and that stack's server toggle is set to `false`
- **THEN** `terraform plan` SHALL NOT plan that volume's destruction or replacement

#### Scenario: A store admitted under the fallback has its backups watched
- **WHEN** a store is admitted under the fallback
- **THEN** before its data first lands, each kind of backup it relies on SHALL publish its last success and maximum age as *A Backed-Up Store's Backup Age Is Alerted On* (`openspec/specs/iac-platform-services/spec.md`) requires, so that a backup overdue past its maximum age raises an alert
