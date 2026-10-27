---
kind: change
waits_on: []
design_with: []
recorded_by: deploy-the-platform-stack-per-environment
re_checked: 2026-10-19
---

Prometheus in `platform/docker-compose.yml` declares no `external_labels`, and Alertmanager routes group on labels that name no host or stack, so staging's and production's alerts are identical text. Attribution currently comes from each stack's own `PLATFORM_SLACK_WEBHOOK_URL` and `PLATFORM_DEADMANSWITCH_URL` (`docs/bootstrap-a-new-host.md` §7.3), which nothing enforces: paste one stack's webhook into the other's Environment and alerts merge silently, and `.github/tests` cannot read repository settings.

The fix is `external_labels` under Prometheus's `global:`, its value rendered at deploy time, and a regenerated `platform.config-checksum`. Settle: stack (`main-staging`) or environment (`staging`), which are different axes; whether to derive it from `PLATFORM_DEPLOY_HOST` rather than add a secret; and whether Alertmanager routes group on it.

- **Kind**: It needs the stack-or-environment decision and owes an `iac-platform-deploy-pipeline` delta for the new rendered value.
- **Recorded by**: `deploy-the-platform-stack-per-environment`, which put the stack on a second host; parameterising the Compose file was its declared Non-Goal.
