---
kind: fix
waits_on: []
design_with: []
recorded_by: let-a-stack-opt-out-of-the-converge
re_checked: 2026-10-19
---

`let-a-stack-opt-out-of-the-converge` lets a stack declare `converges_host: false` in its `pipeline.yml`, declared rather than derived from `server_enabled = false` in `terraform.tfvars` because no workflow reads a `.tfvars` file (its `design.md`, Decision 2). The cost is an interval: a server re-enabled without flipping the declaration back is converged by nothing, and nothing reports it. A `.github/tests` check reading both committed files (a stack with `server_enabled = false` declares `converges_host: false`, and one with `server_enabled = true` or absent does not) closes it statically. `.github/tests/test_a_stack_opts_out_of_the_converge.py` does not read `terraform.tfvars` today.

Decide whether it also covers `deploys_platform`, which the same decommissioning flips. From that change's code review: `platform-deploy.yml` never reads `converges_host`, so `converges_host: false` with `deploys_platform: true` is caught only by `test_the_platform_stack_deploys_per_stack`'s committed-stack assertion and would otherwise fail late against a missing host; and an excluded stack's required fields go unvalidated by requirement, so a static check of an excluded stack's declaration would surface rot before re-enabling rather than in the pull request that re-enables it.

- **Kind**: A static assertion over two committed files; whether to cover `deploys_platform` is decided within it.
- **Recorded by**: `let-a-stack-opt-out-of-the-converge` (archived 2026-10-11), as a separate cross-layer obligation.
