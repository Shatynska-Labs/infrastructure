---
kind: change
waits_on: []
design_with: []
recorded_by: close-ci-verification-gaps
re_checked: 2026-10-19
---

Two unrelated CI improvements deferred by `close-ci-verification-gaps`:

- **The destroy-policy gate's inspection logic is inline workflow shell.** Moving it into a version-controlled script with executable fixtures would make the highest-consequence logic here testable. That change's `design.md` Decision 5 deferred it on scope, not merit; four fixtures are described in its `tasks.md` 1.1 (clean, destructive, malformed, valid-JSON-not-a-plan). `.github/tests/test_ci_configuration.py` asserts the routes are closed, not that each is reached.
- **`actionlint` is cited as a verification means, but nothing installs it** (absent from `.pre-commit-config.yaml`). Landing the hook first needs a disposition of two pre-existing, intentional `SC2016:info` findings (single-quoted markdown in `echo`, in `pr-validation.yml`'s plan-comment step and `apply.yml`'s job-summary step).

- **Kind**: The first restructures the production destroy gate; the second needs an operator decision on dispositioning the two findings.
- **Recorded by**: `close-ci-verification-gaps`, which deferred both on scope rather than rejecting them.
