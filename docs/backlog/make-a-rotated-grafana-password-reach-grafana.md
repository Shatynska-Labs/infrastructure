---
kind: change
waits_on: []
design_with: [make-a-rotated-secret-reach-its-inline-config, perform-the-stack-separation-check-that-was-never-run, verify-at-deploy-time-that-what-shipped-is-what-runs]
recorded_by: give-each-stack-its-own-grafana-password
re_checked: 2026-10-19
---

Rotating `PLATFORM_GRAFANA_ADMIN_PASSWORD` recreates `platform-grafana-1` with the new value and leaves Grafana accepting the old one: `admin_password` is read only when Grafana's database is created, and that database lives on the data volume (`/mnt/main/grafana`). Measured on staging 2026-09-17: deploy green, container `Recreated`, new value in the environment, `/api/user` answered `401`. Every signal is green; the shape that hurts is a rotation after a leak that leaves the leaked credential working. Until it lands, the host step in `docs/bootstrap-a-new-host.md` Appendix A (`grafana cli admin reset-admin-password`) completes a rotation, and the operator confirms a login.

The change owes either a deploy that reconciles the service with the shipped value (smaller for Grafana alone; belongs where the deploy can hold a credential, `app-deploy`) or a post-deploy probe asserting the running service accepts what was shipped. The probe generalises to every credential a service stored once: `PLATFORM_POSTGRES_EXPORTER_PASSWORD` (typed into Postgres at §7.5) and `PLATFORM_POSTGRES_USER`/`_PASSWORD` (used by `initdb` at first boot). It has the same home problem as its siblings: a property of a running host.

- **Kind**: It needs the operator to choose reconcile or probe, and owes a platform deploy delta.
- **Recorded by**: `give-each-stack-its-own-grafana-password` (2026-09-17), which rotated staging's password and checked a login; fixing the rotation mechanism was outside that fix's scope.
