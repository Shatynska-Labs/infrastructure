---
kind: change
waits_on: []
design_with: [rename-the-requirements-that-read-narrower-than-they-are]
recorded_by: let-a-stack-opt-out-of-the-converge
re_checked: 2026-10-19
---

On 2026-10-11, at the operator's request, the `main-production` GitHub Environment's required reviewer was removed (its protection rules are empty), so Terraform apply, Host Converge and Platform Deploy run on merge without approval; the Destroy Policy Gate still applies. Committed texts still describe the reviewer as in force: *Gated Production Apply Applies the Reviewed Plan* and its scenario "Merge does not apply immediately" (`openspec/specs/iac-cicd-pipeline/spec.md`), the `github_environment` comment in `terraform/stacks/main-production/pipeline.yml` ("`main-production` requires a reviewer"), `AGENTS.md` ("Prod's apply waits for a human to approve the saved plan"), and `README.md` ("gates every apply behind manual approval"). The change owes a decision record (why an unreviewed production apply is acceptable here, and what bounds it) and the corresponding deltas, not a silent text edit. If the repository were made private on GitHub Free, Environment protection rules and branch protection would stop applying too, which bears on what "gated" can mean; it is public today.

- **Kind**: It owes `iac-cicd-pipeline` deltas and a recorded operator decision.
- **Design with**: `rename-the-requirements-that-read-narrower-than-they-are`, which renames *Gated Production Apply Applies the Reviewed Plan*.
- **Recorded by**: `let-a-stack-opt-out-of-the-converge` (archived 2026-10-11), which declined to fold it in.
