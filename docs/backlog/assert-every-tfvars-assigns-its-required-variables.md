---
kind: fix
waits_on: []
design_with: []
recorded_by: add-a-staging-environment
re_checked: 2026-10-19
---

Nothing checks that each stack's `terraform.tfvars` assigns every variable its `variables.tf` declares without a `default`. A gap surfaces only at plan time: `pr-validation.yml`, `apply.yml` and `drift.yml` run with `-input=false`, so the plan fails `No value for required variable`, the required check fails, and the nightly drift sweep fails every night and takes the shared heartbeat with it. Detecting it that way needs a credential, a workspace and a network. The same fact is a static read for `.github/tests`; the only real work is a small parser of `variable` blocks and `.tfvars` assignments without HCL machinery the suite does not have. `.github/tests/test_a_second_environment.py` already reads `terraform.tfvars` and can lend its approach. Both stacks currently assign `server_type`.

- **Kind**: A static assertion with no delta or decision.
- **Recorded by**: `add-a-staging-environment`'s code review (2026-09-10), which met the gap as that change's own in-flight state (`server_type` unassigned in `main-staging`); a check failing the tree still being assembled belonged to a later change.
