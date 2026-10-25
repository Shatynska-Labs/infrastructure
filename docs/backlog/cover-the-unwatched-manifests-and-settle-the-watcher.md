---
kind: change
waits_on: []
design_with: [catch-up-the-drifted-galaxy-pins]
recorded_by: cover-platform-images-with-dependabot
re_checked: 2026-10-19
---

`.github/dependabot.yml` watches `terraform`, `github-actions`, `docker-compose` (`platform/` and `tools/env-rendering-probe/`) and `npm`. Nothing watches the pip manifests: `.github/requirements-ci.txt`, `ansible/requirements-test.txt` and `ansible/requirements.txt` (which also pins `ansible-core`'s dependencies). `ansible/requirements.txt`'s `ansible-core` must equal `requirements-test.txt`'s, and `.github/tests/test_host_converge_workflow.py` fails on a difference, so a bump of one alone is red on arrival: the two must move as a pair (a grouped update, or one watched and the other asserted to follow). Do not inherit the "one stanza" estimate: *Automated Dependency Updates* (`openspec/specs/iac-safety-hardening/spec.md`) enumerates ecosystems by name and the suite reads it back, so a stanza also needs a delta and its tests.

The watcher choice was settled with a recommendation: stay with Dependabot for now. Renovate covers `pre-commit` and `ansible-galaxy` natively, but hosted Renovate is a third party with write access; self-hosted Renovate could reuse the `infrastructure-autoupdate` App. Revisit when a second deployed Compose stack appears, the galaxy manifest grows, or the galaxy migration is done and small bumps start being missed. The old precondition (something notices a red scheduled run) is met by `notice-when-a-periodic-job-stops-reporting`'s heartbeat checks.

- **Kind**: It owes a delta widening *Automated Dependency Updates*' ecosystem enumeration, and a decision on how the two `ansible-core` pins move together.
- **Recorded by**: `unknown` change; the same shape as `cover-platform-images-with-dependabot` (archived 2026-09-08), which closed the image half; the watcher question was recorded 2026-09-08.
