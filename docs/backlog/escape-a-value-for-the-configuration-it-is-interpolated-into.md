---
kind: change
waits_on: []
design_with: [make-a-rotated-secret-reach-its-inline-config]
recorded_by: render-the-env-file-so-a-secret-survives-it
re_checked: 2026-10-19
---

The `.env` escaping guarantees only what the dotenv parser yields. `SLACK_WEBHOOK_URL` and `DEADMANSWITCH_URL` are then interpolated unquoted into the embedded Alertmanager YAML in `platform/docker-compose.yml`, and `ACME_EMAIL` into a Traefik `command:` argument. A `: `, `#`, quote or line break would change or break those documents, and nothing escapes for either context. That today's vendor-issued values carry no such character is a property of the values, not the file, so this is owed work.

Settle: escape at render time (a second escaper per destination) or move the two URLs out of embedded configuration via Alertmanager's file reference, which removes the question. Either way, a corrected value reaches the container only when it is next replaced (*A Shipped Configuration Change Is Visible to the Container Runtime*, `openspec/specs/iac-platform-deploy-pipeline/spec.md`).

- **Kind**: It needs the escape-or-file-reference decision and owes an `iac-platform-deploy-pipeline` delta.
- **Design with**: `make-a-rotated-secret-reach-its-inline-config` (moving the URLs out of embedded config changes how a rotation reaches the container).
- **Recorded by**: `render-the-env-file-so-a-secret-survives-it`, whose obligation deliberately stops at the dotenv parser.
