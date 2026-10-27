---
kind: fix
waits_on: []
design_with: [make-a-rotated-secret-reach-its-inline-config]
recorded_by: record-basis-api-durable-store
re_checked: 2026-10-27
---

The `slack` receiver in `platform/docker-compose.yml`'s Alertmanager config titles a notification `{{ .CommonLabels.alertname }}` and its body lists each alert's summary and description, so with `send_resolved: true` a resolve notice reads exactly like the alert it resolves; only Slack's attachment colour (red or green) tells them apart, and the 4h repeat of a still-firing alert looks the same again. Observed during `record-basis-api-durable-store`'s alert drill (2026-10-26), where every resolve had to be told from a repeat by its timing. The title should carry `.Status` (e.g. `[RESOLVED]`), keeping `CommonLabels.alertname`, which `name-every-alert-in-a-grouped-slack-notification` relies on.

- **Kind**: No delta, no decision; one template line and a `.github/tests` assertion. Editing the block also moves the config checksum, so the deploy recreates Alertmanager.
- **Recorded by**: `record-basis-api-durable-store`'s confirm step; a template change is outside its scope.
