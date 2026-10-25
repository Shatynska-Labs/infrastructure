---
kind: change
waits_on: []
design_with: []
recorded_by: apply-host-configuration-through-a-gated-workflow
re_checked: 2026-10-19
---

`pr-validation.yml`, `apply.yml` and `drift.yml` share one ~160-line stack-discovery shell body, asserted identical by `.github/tests`, which locates a body by the `terraform/stacks` path literal it contains and executes it against a scratch tree. `host-converge.yml` and `platform-deploy.yml` carry near-siblings that are deliberately not identical (`host-converge.yml` also enumerates `ansible/inventory/*.hcloud.yml` and cross-checks both sets), and both sit outside the identity assertion; `platform-deploy.yml`'s comment counts "five near-siblings".

A script under `.github/scripts/` (none exists yet) is likely simpler than a composite action: executed directly, it removes the path-literal locator. The shared parts are the flat `key: value` reader, secret-name validation, the empty-result refusal and the JSON emission; the roots and cross-checks stay parameters. Weigh it against the cost: it restructures the production apply path and replaces the identity assertion rather than retargeting it.

- **Kind**: It restructures every gated workflow's discovery and replaces a test assertion, which is too large for one review sitting.
- **Recorded by**: `apply-host-configuration-through-a-gated-workflow`, which wrote the fourth body (`host-converge.yml`); factoring was out of scope for a change already restructuring gated workflows.
