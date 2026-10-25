---
kind: change
waits_on: []
design_with: [make-a-rotated-secret-reach-its-inline-config]
recorded_by: apply-shipped-config-on-deploy
re_checked: 2026-10-19
---

Nothing establishes that a deploy reporting success applied everything it shipped. After `docker compose up -d --wait`, compare each running container's `com.docker.compose.config-hash` with `docker compose config --hash='*'` and fail on a mismatch. This catches the whole class of containers not replaced, but is a backstop, not a replacement for the `platform.config-checksum` label: without the label, a configuration-only change hashes equal on both sides.

It must run on the host, where `.env` is: several platform services interpolate `${...}` from it, so a hash computed elsewhere mismatches as an artefact. It edits `app-deploy` (installed by `ansible/roles/deploy_user`), which is generic across applications, and needs a decision on what a mismatch does to a deploy that has already replaced and health-checked some services.

It does not catch a secret rotated inside an embedded config such as `alertmanager_config` (both sides hash the same unchanged value). That case is `make-a-rotated-secret-reach-its-inline-config`; a host-side digest taken after interpolation would settle both, which is the deploy-time computation `apply-shipped-config-on-deploy` rejected in its Decision 1, so the two are one decision about the mechanism.

- **Kind**: It changes `app-deploy` for every application, needs the mismatch-handling decision, and owes an `iac-platform-deploy-pipeline` delta to *A Shipped Configuration Change Is Visible to the Container Runtime*.
- **Recorded by**: `apply-shipped-config-on-deploy`, which deliberately stops at making a change visible; checking it applied edits generic `app-deploy` and needs its own decision. The rotated-secret half was found in that change's code review.
