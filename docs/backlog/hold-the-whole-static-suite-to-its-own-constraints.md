---
kind: fix
waits_on: []
design_with: [share-the-static-suites-test-arrangement]
recorded_by: alert-on-certificate-expiry
re_checked: 2026-10-19
---

The suite-wide half is done: `TestEveryModuleInTheSuiteDirectoryNeedsNoPrivilegedResource` in `.github/tests/test_ci_configuration.py` holds every module in the directory to the suite's no-network, no-credential, no-container, no-Terraform constraints. What remains is the absorbed `prune-the-repository-walkers-of-provisioned-content` half: repository-scope walkers read a directory, not the committed tree.

`compose_shaped_files()` (used by `TestEveryComposeFileDeclaringAServiceImageIsCovered`) walks through `walked_files()`, which prunes `.git`, `.terraform`, `__pycache__`, `node_modules`, `openspec`, the Galaxy role and the worktree directories, but not `.molecule-home/`. On a developer machine provisioned for Molecule it finds `community.docker`/`community.general` fixture Compose files there and fails, while CI never provisions Molecule and stays green; it is also a race while Molecule creates and removes `tmp/` under that directory (observed 2026-09-11). The fix is to re-point repository-scope walkers at the existing `tracked_files()` helper in the same module, not to prune one more directory. Deleting `.molecule-home/` to get green throws away provisioning.

- **Kind**: No delta; the helper already exists.
- **Design with**: `share-the-static-suites-test-arrangement`, which gives the same suite a support module.
- **Recorded by**: `alert-on-certificate-expiry` (the self-check half), and the test author deriving `cache-the-apt-index-within-a-converge`, who met the walker half as a red suite; neither change's subject was the suite's walkers.
