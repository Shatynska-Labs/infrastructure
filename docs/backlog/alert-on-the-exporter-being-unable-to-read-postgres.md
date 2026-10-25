---
kind: change
waits_on: []
design_with: []
recorded_by: unknown
re_checked: 2026-10-19
---

`MetricsTargetDown` (`up == 0`) cannot catch postgres-exporter failing to reach the database: the exporter answers `/metrics` 200 with `pg_up 0`, and its healthcheck passes (measured against the pinned `v0.20.1`). On 2026-09-15 both hosts were found at `pg_up 0` for an unknown period (a `#` in the password broke `DATA_SOURCE_NAME`, since fixed) with nothing reporting it. The `pgexporter` role is recreated by hand after any store reset or rebuild, the step most likely to go wrong; `platform/README.md` tells the operator to check it by hand until this lands.

Owed: an alert on `pg_up == 0` for the `postgres-exporter` job in the inline `prometheus_rules` config (not `prometheus_config`, where a `groups:` block is not read), with a `for:` that rides out an instance restart, and the `platform.config-checksum` label regenerated or nothing deploys. The wider question is whether each exporter needs its own liveness signal rather than one alert per incident.

- **Kind**: The rule is one line, but it needs the per-exporter liveness decision and owes an `iac-platform-services` alerting delta.
- **Recorded by**: `unknown` change; found 2026-09-15 while writing `platform/README.md`'s *Upgrading the PostgreSQL major version*, and kept open for the wider exporter question.
