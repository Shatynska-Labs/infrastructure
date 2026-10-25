---
kind: change
waits_on: []
design_with: [unify-the-workflows-own-role-discovery]
recorded_by: unify-the-two-role-exclusion-rules
re_checked: 2026-10-19
---

Two implementations resolve a `roles:` entry to the directory `ansible-galaxy` installs it under: `.github/tests/test_ci_configuration.py` and `ansible/scripts/select_molecule_roles.py`. A test binds them only to each other, and both were once wrong in the same two ways with every test green: they refused `- role: <name>`, and they split a `,version` qualifier before stripping `.git`, so `…/ansible-role-docker.git,8.0.0` was named `ansible-role-docker` instead of `ansible-role-docker.git`. Both were corrected by hand against Ansible 2.21.3. Nothing checks them against `RoleRequirement.role_yaml_parse`, so a future divergence goes unnoticed.

`.github/tests` cannot import `ansible-core`: *The Suite Needs No Privileged or External Resource* (`openspec/specs/iac-cicd-pipeline/spec.md`) limits it to the standard library and `.github/requirements-ci.txt` (`pre-commit`, `PyYAML`), and the suite catches even a lazy import. The check belongs where Ansible is pinned: a Molecule scenario, or an `ansible-verify.yml` step after `ansible/requirements-test.txt` is installed. Adding `ansible-core` to `requirements-ci.txt` instead changes what the static suite is.

- **Kind**: It needs a decision on where the check lives; the `requirements-ci.txt` option would owe a delta on *The Suite Needs No Privileged or External Resource*.
- **Recorded by**: `unify-the-two-role-exclusion-rules`, which found both copies wrong but could not write the check inside the static suite.
