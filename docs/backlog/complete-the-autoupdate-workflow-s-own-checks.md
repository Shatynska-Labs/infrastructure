---
kind: change
waits_on: []
design_with: []
recorded_by: open-autoupdate-pr-with-app-token
re_checked: 2026-10-19
---

`open-autoupdate-pr-with-app-token` added a section to `.github/tests/test_ci_configuration.py` that finds pull-request-opening steps and asserts their identity. Its helpers have four reading limits, each a false positive on a legitimate change: `token_inputs` reads only step-level `env:` and misses a job- or workflow-level `GH_TOKEN` (the likeliest to bite, the first time a workflow opens a PR with `gh`); `step_opens_a_pull_request` matches a POST and `/pulls` anywhere in one `run:` block; `secrets_referenced_by` scans the whole job, not the identity path (`HEARTBEAT_PING_KEY` already sits in that workflow); `readme_sections` splits at any `#` line, including inside code fences.

The section also asserts nothing about two properties of `.github/workflows/pre-commit-autoupdate.yml`: the minting step's `permission-contents: write` / `permission-pull-requests: write` down-scoping, and the restricted input set on the PR step (no `labels`/`assignees`, which need Issues). Neither is live while the App's own scope matches. They come from prose, not a scenario, so a scenario must be written before a test can be derived. The workflow header notes which claims the suite does not stand behind.

- **Kind**: It owes a delta adding scenarios for the two unasserted properties, and edits tests an independent author derived.
- **Recorded by**: `open-autoupdate-pr-with-app-token`, whose tests were independently derived from its deltas; fixing or extending them was a change of its own.
