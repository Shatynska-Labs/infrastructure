Verification commands referenced below, from this project's conventions:

- `python3 -m unittest discover --start-directory .github/tests`, from the repository root
- `pre-commit run --all-files`
- `openspec validate --all`

No Molecule scenario is owed: no role changes. No Terraform module changes, so no `terraform test` is owed.

## 1. Plan

- [x] 1.1 Plan review by `ai-toolkit:change-plan-reviewer` reaches a verdict that permits proceeding, and any conditions are applied.
- [x] 1.2 Commit the approved plan.
- [ ] 1.3 Derive tests from the delta with `ai-toolkit:change-test-writer` (test command and glob: the `.github/tests` row of `AGENTS.md`'s *Testing*), and commit them.

## 2. Repository

- [ ] 2.1 Delete the `commerce-ops` entry from `ansible/inventory/host_vars/main-production.yml`, and rewrite that file's comments that name it or compare its keys with `main-staging.yml`'s (design.md Decision 5).
- [ ] 2.2 Apply design.md Decision 5's rewrites to the documents: the runbook's production warning, phase 14 and phase 15 sentences and `/health` example; the onboarding guide's production-divergence paragraph; `platform/README.md`'s cutover and `commerce-ops-postgres-1` sentences; the onboarding guide's comment-convention paragraph; `docs/bootstrap-a-new-host.md`'s `host_vars` statement.
- [ ] 2.3 Change `.github/tests/test_the_rebuild_runbook_records_its_rehearsal.py` as design.md Decision 4 describes, and record the disposition against its obsolete-test entry in `test-plan.md`.
- [ ] 2.4 Add to `docs/backlog.md`'s `revoke-an-application-s-deploy-authorisation` that production was cleaned by hand too.
- [ ] 2.5 Deal with every entry under **Missing shared arrangement** in `test-plan.md` (the project records none, so each is kept with that reason).

## 3. Verify and ship

- [ ] 3.1 Run the three verification commands above; all pass.
- [ ] 3.2 Commit the implementation and have `ai-toolkit:change-code-reviewer` review the committed diff; apply fixes.
- [ ] 3.3 Open the pull request. After the operator confirms the merge and its converge, hand the operator the read in design.md Decision 2, and stop if `/opt/commerce-ops` holds anything else; otherwise hand them the clean-up block, and confirm from the pasted output and a read of `/opt` that `/opt/commerce-ops`, both sudoers files and both `authorized_keys` lines are gone and every other application's are intact.
- [ ] 3.4 Archive the change on a freshly fetched trunk, delete the `remove-commerce-ops-from-production` entry from `docs/backlog.md` in the same commit, and open its record pull request.
