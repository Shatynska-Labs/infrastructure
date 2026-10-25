---
kind: change
waits_on: []
design_with: [sweep-the-stale-scenario-titles-and-check-them, say-production-is-no-longer-reviewer-gated]
recorded_by: make-the-pipeline-environment-agnostic
re_checked: 2026-10-19
---

Requirement names are this repository's citation form, and several still name production or "this host" alone although two environments now share them. From `make-the-pipeline-environment-agnostic`: *Gated Production Apply Applies the Reviewed Plan* (a genuine mismatch) and *Credential Scoping by Privilege* (`iac-cicd-pipeline`), and *Write Credentials Confined to the Gated Pipeline* (`iac-safety-hardening`). Second set: *Conditional Prod Server Creation* (`iac-server-lifecycle`), *Conditional Prod Volume Creation* (`iac-data-volumes`), *Data Durability for Stateful Resources* and *No Store on This Host Holds Data Requiring Backup* (`iac-safety-hardening`), *Host Joins a Private Tailnet for Non-Operator SSH Access* and *Unprivileged Operator Accounts Support Interactive Host Inspection* (`iac-host-configuration`). Staging uses the same toggles, tailnet and operator account, and staging took the platform stack on 2026-09-13, so it holds stores: `platform_postgres_data`, Traefik's certificates and Alertmanager's volume; "this host" is now wrong about which host a durability obligation binds.

Renaming sweeps every citation: comments in `apply.yml`, `drift.yml`, `pr-validation.yml`, `docs/bootstrap-a-new-host.md`, `.github/tests`. `.github/tests/test_a_retired_requirement_name_is_reported.py` makes the sweep checkable. Precedent: `add-a-staging-environment` renamed *Each Stack Has a Dedicated Hetzner Cloud Project* where it had a content change to carry it.

- **Kind**: It owes RENAMED/MODIFIED deltas across four capabilities and a repository-wide citation sweep.
- **Design with**: `sweep-the-stale-scenario-titles-and-check-them`, the same citation-sweep mechanism over scenario titles; `say-production-is-no-longer-reviewer-gated`, which owes a delta to *Gated Production Apply Applies the Reviewed Plan*.
- **Recorded by**: `make-the-pipeline-environment-agnostic` (first set) and the staging changes that followed it (second set); both declined to mix a mechanical rename into diffs restructuring gated workflows or one environment directory.
