## ADDED Requirements

### Requirement: A Backed-Up Store's Backup Age Is Alerted On
The platform stack SHALL collect, from each application's own metrics directory on the host's data volume, the age of that application's backups, and SHALL alert when a backup is overdue. This is what *No Store on This Host Holds Data Requiring Backup* (`openspec/specs/iac-safety-hardening/spec.md`) relies on for a store admitted under its fallback: a backup that stops does so silently, and a restore rehearsed once does not recover data the backup never took.

**Collection** SHALL be by node-exporter's textfile collector, reading `*.prom` files from every `/mnt/main/applications/<application>/metrics` directory through node-exporter's existing read-only mount of the host's root filesystem. No monitoring service SHALL be attached to a network an application joins for this purpose, consistent with *Monitoring Services Are Not Reachable From Application Containers*. An application writes its files into its own directory and never reaches a monitoring service.

**The contract an application implements**, one pair of series per kind of backup it takes:

- `backup_last_success_timestamp_seconds{store, kind}` — the Unix time of that kind's last successful backup;
- `backup_max_age_seconds{store, kind}` — the age beyond which that kind is overdue, set by the application from its own recovery targets.

The application SHALL write each file atomically — to a name not ending in `.prom` in the same directory, then renamed — so that the collector never reads a partial file, and SHALL make it readable by others, because the collector does not run as the application's user. Any `# HELP` or `# TYPE` line for a metric name SHALL be byte-identical across every file that emits that name, or omitted, because differing help text is a read error that drops a file's series.

**The collector's pattern SHALL match at least one directory on every host**, an empty one owned by the platform where no application has one, because a pattern matching nothing is itself reported as a read error and would hold the unreadable-file alert permanently firing.

**Alerts**, routed like every other rule:

- a backup whose last success is older than its declared maximum age;
- a last-success timestamp published with no maximum age to judge it by;
- the textfile collector failing to read a file;
- node-exporter failing to gather a series, which is how two files emitting the same series surface — the collector itself serves one, drops the other and reports no read error.

**An expected backup that publishes nothing is not yet alerted on.** That needs the set of stores each host expects, and declaring a store before its first backup would fire from the moment it was declared. Until it is declared, the rule on staleness covers every backup that has succeeded at least once, because its file remains and ages.

#### Scenario: An overdue backup raises an alert
- **WHEN** an application's metrics directory publishes a `backup_last_success_timestamp_seconds` for a `store` and `kind` that is older than the `backup_max_age_seconds` it publishes for the same pair
- **THEN** an alert SHALL fire naming that store and kind

#### Scenario: A timestamp without a maximum age raises an alert
- **WHEN** an application publishes `backup_last_success_timestamp_seconds` for a `store` and `kind` with no `backup_max_age_seconds` for the same pair
- **THEN** an alert SHALL fire naming that store and kind, rather than the backup going unjudged

#### Scenario: An unreadable metrics file raises an alert
- **WHEN** the textfile collector fails to read a file from an application's metrics directory
- **THEN** an alert SHALL fire

#### Scenario: Two files emitting the same series raise an alert
- **WHEN** two files in the application metrics directories emit a series with the same name and labels
- **THEN** an alert SHALL fire, although the textfile collector reports no read error for it

#### Scenario: A host with no application metrics raises nothing
- **WHEN** the platform stack runs on a host where no application has a metrics directory, or none holds a file
- **THEN** none of these alerts SHALL fire

#### Scenario: Collection attaches no monitoring service to the application network
- **WHEN** the committed platform stack definition is read
- **THEN** node-exporter SHALL read the application metrics directories through its read-only root filesystem mount, and SHALL NOT be attached to `platform_edge`
