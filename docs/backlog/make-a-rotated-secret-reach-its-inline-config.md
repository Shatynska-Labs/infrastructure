---
kind: change
waits_on: []
design_with: [make-a-rotated-grafana-password-reach-grafana, perform-the-stack-separation-check-that-was-never-run, verify-at-deploy-time-that-what-shipped-is-what-runs]
recorded_by: give-staging-its-own-dead-mans-switch-check
re_checked: 2026-10-19
---

A secret interpolated into an inline `configs:` block in `platform/docker-compose.yml` does not reach the container on a deploy, and the deploy reports success. `platform.config-checksum` (from `apply-shipped-config-on-deploy`) is computed from committed text; a secret moves only the rendered config, so `docker compose up -d --wait` sees an identical service and leaves it running. Affected today: `DEADMANSWITCH_URL` and `SLACK_WEBHOOK_URL` in `alertmanager_config`, i.e. the dead-man's-switch and alert routing, both of which fail silently. Measured on staging 2026-09-16: Alertmanager still pinged the old URL eleven hours after a green deploy. Rotating `PLATFORM_SLACK_WEBHOOK_URL` and revoking the old one would leave alert delivery dead with every check green.

Options: force-recreate services whose configs interpolate a secret; compute the checksum over the rendered config at deploy time (ends the static check, catches both cases); or a post-deploy probe asserting the running config carries the shipped value, in the shape `make-a-shared-instance-reset-visible-to-its-applications` used. It is a property of a running container, so neither `.github/tests` nor Molecule can hold the test. Until it lands, a rotation is followed by recreating the service by hand and confirming the value arrived (the comment in `alertmanager_config` says so). A non-inline `environment:` value is recreated correctly; Grafana ignoring a delivered password is `make-a-rotated-grafana-password-reach-grafana`, not this.

- **Kind**: It needs the operator to choose among the three options and owes a delta to the platform deploy requirements.
- **Recorded by**: found 2026-09-16 while closing `give-staging-its-own-dead-mans-switch-check`, by checking whether the fix had landed rather than reading the deploy's result; it is a separate defect in the deploy mechanism.
