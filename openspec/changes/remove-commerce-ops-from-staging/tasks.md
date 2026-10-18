Verification commands referenced below, from this project's conventions:

- `python3 -m unittest discover --start-directory .github/tests`, from the repository root
- `pre-commit run --all-files`
- `openspec validate --all`

No Molecule scenario is owed: no role changes. No Terraform module changes, so no `terraform test` is owed. No specification delta, so no tests are derived.

## 1. Plan

- [ ] 1.1 Plan review by `ai-toolkit:change-plan-reviewer` reaches a verdict that permits proceeding, and any conditions are applied.
- [ ] 1.2 Commit the approved plan.

## 2. Repository

- [ ] 2.1 Delete the `commerce-ops` entry from `ansible/inventory/host_vars/main-staging.yml`, and rewrite the comments in that file that describe it.
- [ ] 2.2 Rewrite `docs/runbook-rebuild.md` phases 1, 9, 14, 15 and 16 so they do not assume `commerce-ops` is staging's application, keeping the production warning that names `commerce-ops`'s own PostgreSQL before the destroy step, and update the staging references in `docs/onboard-an-application.md`; historical sentences stay.
- [ ] 2.3 Add to `docs/backlog.md`'s `revoke-an-application-s-deploy-authorisation` that it was worked around by hand once.

## 3. Verify and ship

- [ ] 3.1 Run the three verification commands above; all pass.
- [ ] 3.2 Commit the implementation and have `ai-toolkit:change-code-reviewer` review the committed diff; apply fixes.
- [ ] 3.3 Open the pull request; after the operator confirms the merge and the converge, hand the operator the cleanup block and read the host to confirm `/opt/commerce-ops`, both sudoers files and both `authorized_keys` lines are gone and `platform`'s are intact.
- [ ] 3.4 Archive the change on a freshly fetched trunk, delete the `remove-commerce-ops-from-staging` entry from `docs/backlog.md` in the same commit, and open its record pull request.
