## Why

`main-staging`'s server was decommissioned on 2026-09-19 (`fix: disable the staging server`, which set `server_enabled = false` and let the next apply remove the server and its volume). The stack itself was kept deliberately, so staging can return by flipping one value. Nothing in the pipeline was told.

Since then every merge touching `ansible/` starts a `converge (main-staging)` row that fails at inventory resolution — "the group 'staging' this stack declares names no host to converge" (Host Converge run 38149651057, 2026-10-11) — and every merge touching `platform/` would start a `deploy (main-staging)` row aimed at a tailnet peer that no longer exists. Production is unaffected, because rows are independent, but a check that is red on every run for a known reason is the kind that gets tuned out, and the one that matters next will be read the same way.

The operator does not need staging for the coming months and may add it back later. Removing the stack outright was measured and rejected for now: deleting it breaks 28 assertions across nine `.github/tests` modules that trace to six capabilities, because six archived changes made "this repository holds a second stack" part of the specification. What is wanted is narrower — a stack that says, in its own declaration, that the pipeline has no host to reach.

## What Changes

- **`pipeline.yml` gains a sixth field, `converges_host`, optional and defaulting to `true`.** A stack declaring `converges_host: false` is excluded from `host-converge.yml`'s matrix by its own committed declaration, and the run names it as excluded. The field names what is true when the value is **true**, as `destroy_policy_gate` and `deploys_platform` do. Its default is the opposite of `deploys_platform`'s for the reason the requirement already gives for every optional field: each default is the value that is safe when the field was forgotten, and for a converge that is "converged" — a host dropped by a forgotten field drifts from its firewall, SSH and account baseline with nothing reporting it.

- **`host-converge.yml`'s discovery reads the field** with the same `field()` reader and the same refusal shape `platform-deploy.yml` uses for `deploys_platform`: `true` or absent converges, `false` excludes and is echoed by name, anything else is refused naming the stack and the value. A dispatched run naming an excluded stack fails saying it is excluded. A run in which every stack is excluded fails as an empty discovery does.

- **`main-staging` declares `converges_host: false` and `deploys_platform: false`.** The second needs no workflow change at all: `deploys_platform` already exists and already excludes. Both comments say why — the server is decommissioned — and that re-enabling staging means flipping both back in the same pull request that sets `server_enabled = true`.

- **`iac-cicd-pipeline` is modified in two requirements**: *Each Stack Declares Its Own Pipeline Configuration* gains the third optional field, its default and its reasoning; *Host Configuration Is Applied by a Gated Workflow* states that an excluded stack is named rather than omitted, how a dispatch naming one fails, and that an all-excluded run fails.

## Non-Goals

- **Removing the staging stack.** Its Terraform, inventory source, vars files and GitHub Environment stay. Plan, apply and drift keep covering it — they read none of the fields this change touches, and they are what holds the decommissioned state in place.

- **Deriving the exclusion from `server_enabled`.** No workflow here reads a `.tfvars` file, and this change does not start. `design.md` Decision 2 gives the reasoning and what is accepted in exchange.

- **A static check that a decommissioned stack declares itself excluded.** It would be a `.github/tests` read of two committed files and is cheap, but it is a new cross-layer obligation rather than part of letting a stack opt out; it is recorded in `docs/backlog.md` instead.

- **Updating the specifications that still describe production as reviewer-gated.** The `main-production` Environment's required reviewer was removed in repository settings on 2026-10-11 at the operator's request, so *Gated Production Apply Applies the Reviewed Plan* and the gating language in *Host Configuration Is Applied by a Gated Workflow* now describe a setting that is not in force. That is a separate change with its own decision to record, and this one does not fold it in; it is recorded in `docs/backlog.md`.

The branch and working tree are removed after this record's own pull request merges, which is after the commit that writes `tasks.md`, so those steps are recorded here in prose rather than as tasks.
