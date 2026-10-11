## Context

`main-staging` has had no server since 2026-09-19: `server_enabled = false` in `terraform/stacks/main-staging/terraform.tfvars`, applied the same day, and nightly drift has reported "No changes" for the stack since. Its Hetzner project now holds only the stack's `operator` SSH key. The stack's pipeline declaration still opts it into everything: `host-converge.yml` converges every stack that has an inventory source, and `main-staging/pipeline.yml` declares `deploys_platform: true`.

`platform-deploy.yml` already has the mechanism this change needs. Its discovery reads `deploys_platform` with the shared `field()` reader, treats `true` as opted in, `false` or absent as excluded — echoing the excluded stacks by name — and refuses anything else. *Each Stack Declares Its Own Pipeline Configuration* already carves out "a stack excluded by an optional field it declares" from the fail-closed rule, provided the exclusion is reported by the workflow that read it. This change gives the converge the same shape.

## Goals / Non-Goals

**Goals:**

- A stack can declare that the host-configuration workflow has no host to reach, and the workflow then runs no converge row for it and names it as excluded.
- `main-staging` stops producing a red converge row on every `ansible/` merge and a doomed deploy row on every `platform/` merge.
- Staging stays revivable by editing its own declaration back, with no workflow change.

**Non-Goals:** see `proposal.md`. In particular the stack is not removed, nothing reads `.tfvars` from a workflow, and the production reviewer's removal is not specified here.

## Decisions

### Decision 1: A new optional field, `converges_host`, defaulting to `true`

The field joins `destroy_policy_gate` and `deploys_platform` as the third optional field, and follows the rules the requirement already sets for every optional field.

- **Polarity names what is true when the value is true.** `converges_host: true` converges. `host_excluded: false` or `dormant: true` would carry the same information with a polarity a reader can invert without noticing.
- **The default is the safe value when the field was forgotten.** For a converge that is "converged". A stack whose declaration forgot the field and was therefore *not* converged would have its firewall, SSH configuration and operator accounts silently stop being applied — the failure the converge exists to prevent, and one nothing reports. That makes this default the opposite of `deploys_platform`'s, and the requirement's sentence that the two defaults "are opposite values" is rewritten to say the defaults *differ* for one reason, since with three fields "opposite" no longer parses.
- **An unrecognised value is refused**, not read as either answer, exactly as `deploys_platform` does: a typo must not be a silent opt-out.

*Alternative rejected:* reuse `deploys_platform` for both. The two are different facts — a host can be converged and receive no platform stack, which is precisely the interval `deploy-the-platform-stack-per-environment` recorded for staging between 2026-09-10 and 2026-09-13.

### Decision 2: Declared, not derived from `server_enabled`

`server_enabled = false` already says the same thing about staging, so deriving the exclusion would avoid a second fact that can disagree with the first. It is rejected because no workflow in this repository reads a `.tfvars` file: `pipeline.yml` is `.yml` precisely so the pipeline layer and the Terraform layer read separate files, and an HCL value can be an expression a `sed` reader cannot evaluate. The cost accepted is an interval: a server re-enabled without flipping its declaration back is converged by nothing until it is. The declaration's comment says so and names the pull request that re-enables the server as the place to flip both. A static `.github/tests` check that a stack with `server_enabled = false` declares `converges_host: false` would close the gap cheaply, and is recorded in `docs/backlog.md` rather than folded in, as a separate cross-layer obligation.

### Decision 3: The excluded stack is skipped before its other fields are validated

As in `platform-deploy.yml`, a stack whose declaration says `converges_host: false` is recorded as excluded and discovery moves on, without checking its `target_environment`, `group_vars` file or read-only secret name. Those fields exist to configure a converge that will not run; refusing a stack the operator has switched off because a file it would need is missing would make switching off harder than switching on. The cross-check that an inventory source and a pipeline declaration exist for each other still runs for every stack, excluded or not, because it is a property of the tree rather than of a converge.

### Decision 4: Discovery's empty-set refusal covers an all-excluded tree, and a dispatch names the exclusion

A run in which every discovered stack is excluded fails, naming them, rather than emitting an empty matrix — the same reason the existing empty-discovery refusal gives. A run dispatched by hand for an excluded stack fails with a message saying it is excluded by its own declaration, distinct from "not found", so the operator is pointed at the declaration rather than at a typo.

### Decision 5: `main-staging` flips both fields in this change

`converges_host: false` uses the new field; `deploys_platform: false` uses the existing one and needs nothing else. Flipping `deploys_platform` to `false` is permitted by *Each Stack Declares Its Own Pipeline Configuration*: the obligation to authorise `platform` on the host runs only from `true`. `ansible/inventory/host_vars/main-staging.yml` keeps its entries, which is the "authorised but not deployed to" state that requirement already calls deliberate.

## Risks / Trade-offs

- **The re-enable interval (Decision 2).** Mitigated by the declaration comment and the backlog entry.
- **A sixth near-sibling divergence in the discovery bodies.** `host-converge.yml`'s discovery body is already outside the identity assertion in `.github/tests`; this change widens its difference from the Terraform workflows by one field read. No new copy is created.

## Migration Plan

1. This change's first pull request merges. It touches `.github/workflows/host-converge.yml` and `terraform/stacks/main-staging/pipeline.yml`, neither under `ansible/` or `platform/`, so it starts no converge and no platform deploy by itself.
2. The next merge touching `ansible/` runs a converge with `main-production` only, and the run names `main-staging` as excluded. That is the observation for **confirm**; a `workflow_dispatch` of Host Converge with an empty `stack` input provokes it without waiting for an Ansible change.

Rollback is reverting the pull request: staging returns to the matrix and resumes failing, which is the state before this change.
