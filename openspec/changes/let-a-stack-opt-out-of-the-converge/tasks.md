Verification commands referenced below, from this project's conventions:

- `python3 -m unittest discover --start-directory .github/tests`, from the repository root
- `pre-commit run --all-files`
- `openspec validate --all`

No Molecule scenario is owed: no role changes. What changes is which stacks a workflow converges, which is a static property of committed files and belongs to `.github/tests`. No Terraform module changes, so no `terraform test` is owed.

## 1. Plan

- [x] 1.1 Plan review by `ai-toolkit:change-plan-reviewer` reaches a verdict that permits proceeding, and any conditions are applied.
- [x] 1.2 Commit the approved plan.
- [x] 1.3 Derive tests from this change's delta specification with `ai-toolkit:change-test-writer`, using the `.github/tests` row of the project's test table, and commit them.

## 2. The converge reads `converges_host`

- [ ] 2.1 In `.github/workflows/host-converge.yml`'s discovery step, read `converges_host` from each stack's `pipeline.yml` with the existing `field()` reader, immediately after confirming the declaration exists, and refuse a control character in it **at once, before branching on its value**, as `platform-deploy.yml` does for `deploys_platform` — so neither the exclusion branch nor the refusal echoes an unrepresentable value. Then: `true` or empty, continue as today; `false`, append the stack to an `excluded` list and `continue`, before the required-field checks (`design.md` Decision 3); anything else, refuse naming the stack and the value.
- [ ] 2.2 Before the empty-set check, echo `Excluded by their own declarations, and converged by nothing: <names>` when the list is non-empty.
- [ ] 2.3 When no stack remains and at least one is excluded, fail naming the excluded stacks (`design.md` Decision 4), keeping the existing message for a tree with no inventory source at all.
- [ ] 2.4 When a dispatched `stack` input names an excluded stack, fail saying it is excluded by its own declaration, distinct from the existing not-found message.
- [ ] 2.5 Keep the step body free of event-derived values, so `.github/tests` can execute it against a scratch tree as it does today.

## 3. Declarations

- [ ] 3.1 In `terraform/stacks/main-production/pipeline.yml`, document `converges_host` as the third optional field in the form the other two use — polarity, default and why it differs from `deploys_platform`'s, and that it is declared rather than derived from `server_enabled` — without setting it, so production keeps the default. Rewrite the passage headed "THE TWO OPTIONAL FIELDS DEFAULT TO OPPOSITE VALUES" for three optional fields whose defaults differ for one reason.
- [ ] 3.2 In `terraform/stacks/main-staging/pipeline.yml`, set `converges_host: false` and change `deploys_platform` to `false`, with a comment stating that the server was decommissioned on 2026-09-19 and that re-enabling staging flips both back in the same pull request that sets `server_enabled = true`. Rewrite the passages that become stale: the reference to "why the two optional fields default to opposite values", and the `deploys_platform` block's statement that the deploy proceeds on merge, which no longer holds while the stack is excluded.

## 4. Backlog

- [ ] 4.1 Add to `docs/backlog.md`: `check-a-decommissioned-stack-declares-no-converge` (the static cross-check of Decision 2) and `say-production-is-no-longer-reviewer-gated` (the specification and documentation update following the 2026-10-11 removal of the `main-production` Environment's required reviewer).

## 5. Verify and ship

- [ ] 5.1 Run the three verification commands above; all pass.
- [ ] 5.2 Commit the implementation and have `ai-toolkit:change-code-reviewer` review the committed diff; apply fixes.
- [ ] 5.3 Open the pull request; after the operator confirms the merge, dispatch Host Converge with an empty `stack` input and confirm with the operator that only `converge (main-production)` ran and the log names `main-staging` as excluded.
- [ ] 5.4 Archive the change on a freshly fetched trunk and open its record pull request.
