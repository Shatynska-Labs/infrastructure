---
kind: change
waits_on: []
design_with: [hold-the-whole-static-suite-to-its-own-constraints]
recorded_by: sync-ai-toolkit-workflow-v10
re_checked: 2026-10-19
---

The `.github/tests` suite has no shared test arrangement: several modules import helpers from `test_ci_configuration.py`, a test module, so a module that is rewritten for its own reasons breaks others, and a test author has nowhere to take a builder from. Give the suite a support module the tests import from, move those helpers into it, and record its location under *Testing* in `AGENTS.md` as the suite's shared test arrangement. Molecule and `terraform test` have none either; say whether either needs one.

- **Kind**: It decides the project's testing strategy (where shared arrangement lives), which is the operator's decision.
- **Design with**: `hold-the-whole-static-suite-to-its-own-constraints`, which also changes how that suite's modules read the tree.
- **Recorded by**: `sync-ai-toolkit-workflow-v10`, which recorded the shared test arrangement as none when taking ai-toolkit's development-workflow v10; creating one is not a sync.
