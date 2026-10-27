---
kind: change
waits_on: []
design_with: [bind-the-galaxy-name-resolution-to-ansible-itself]
recorded_by: unify-the-two-role-exclusion-rules
re_checked: 2026-10-19
---

`ansible-verify.yml`'s *Discover roles carrying scenarios* step enumerates roles in shell by the directory-name heuristic (`grep -v '\.'`). `unify-the-two-role-exclusion-rules` replaced that heuristic in both Python implementations (`.github/tests/test_ci_configuration.py` and `ansible/scripts/select_molecule_roles.py`) with the `ansible/requirements.yml`-derived rule, so the repository holds two rules again. They agree on today's tree (`geerlingguy.docker` is dotted and pinned) and diverge on a second pin in `src:` form or vendored content nobody pinned. No assertion compares the workflow's enumeration with the others; `test_the_workflow_names_no_role_literally` checks only that it names no role literally.

The smaller option is taking the role list from the selector. Expect `.github/tests/test_the_matrix_runs_the_roles_a_pull_request_owes.py`'s `_discovery_steps` fixtures, which build scratch trees with no `ansible/requirements.yml`, to meet the selector's `DerivationRefused`. The same module's `test_an_external_galaxy_dependency_contributes_no_edge_and_is_not_refused` still filters with `if "." in target`; under the unified rule it must be rewritten with a new way to express "an edge to content this repository does not carry", the same question this entry asks of the workflow.

- **Kind**: It changes what CI runs and needs a decision on how the workflow obtains the manifest-derived list.
- **Design with**: `bind-the-galaxy-name-resolution-to-ansible-itself`, which works on the same resolution of external role names from the same manifest.
- **Recorded by**: `unify-the-two-role-exclusion-rules` (archived 2026-09-15); nothing bound the workflow to the other two rules, and changing a workflow's discovery was no rider on a test-helper change.
