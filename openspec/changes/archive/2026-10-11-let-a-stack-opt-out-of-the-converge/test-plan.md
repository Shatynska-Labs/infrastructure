# Test plan: let-a-stack-opt-out-of-the-converge

Derived from this change's delta specification (`specs/iac-cicd-pipeline/spec.md`, two MODIFIED requirements) at commit `e0c3ce6`, before any implementation existed. Written by a test author who did not read the implementation: not `.github/workflows/host-converge.yml`, and not any committed `pipeline.yml`. The tests read both at run time. What a MODIFIED delta supersedes was worked out by diffing each delta requirement against `openspec/specs/iac-cicd-pipeline/spec.md`.

This file is not an artifact the OpenSpec schema knows about. It will not appear among `openspec instructions apply`'s context files, so it has to be read on purpose before implementing.

All new tests are in one module, `.github/tests/test_a_stack_opts_out_of_the_converge.py`. You can select any of them on its own:

    python3 -m unittest discover --start-directory .github/tests -k <ClassName or test_name>

or by full dotted name, run from the repository root: `python3 -m unittest test_a_stack_opts_out_of_the_converge.<Class>.<test>` (with `.github/tests` on `PYTHONPATH`). Below, `M.` is short for `test_a_stack_opts_out_of_the_converge.`.

## Baseline

**Full suite**, taken at `e0c3ce6` before any test was written: `python3 -m unittest discover --start-directory .github/tests` ran 1573 tests, all OK, none skipped.

**After this pass:** 1600 tests ran. The 27 new tests include 13 failing tests, which show up as 15 failure records because one test has three failing subtests. Every failure is in the new module. All 1573 existing tests still pass, including the suite-wide checks on every module in `.github/tests`: no privileged resource, citation form, and retired requirement names.

## Scenario accounting

The delta has 30 scenarios: 16 under *Host Configuration Is Applied by a Gated Workflow* (H) and 14 under *Each Stack Declares Its Own Pipeline Configuration* (E). 10 are covered by new tests and 20 are uncovered with a reason. 10 + 20 = 30.

### Covered

| # | Scenario | Tests | Red at authoring? |
|---|---|---|---|
| H1 | A merge to the host configuration converges without a workstation (revised: "other than one excluded by its own declaration") | `M.TestAStackExcludedByItsOwnDeclarationIsNamedAndNotConverged.test_a_merge_converges_every_stack_its_declaration_does_not_exclude`; also `M.TestTheCommittedTreeConvergesProductionAndExcludesStaging.test_a_merge_converges_production_alone_and_names_staging_as_excluded` (derived) | yes |
| H7 | A run is requested for an environment that does not exist (text unchanged; tested only because it now sits beside an excluded stack) | `M.TestARunRequestedForAnExcludedStackFailsNamingTheExclusion.test_a_dispatch_naming_an_unknown_stack_is_still_refused_as_not_found` | no (the behaviour already exists; it guards against a regression) |
| H8 | A stack excluded by its own declaration is named and not converged | `M.TestAStackExcludedByItsOwnDeclarationIsNamedAndNotConverged.test_an_excluded_stack_is_named_and_every_other_stack_is_converged` | yes |
| H9 | An excluded stack is not refused for a field only its converge would consume | `M.TestAnExcludedStackIsNotRefusedForAFieldOnlyItsConvergeWouldConsume.test_an_excluded_stack_declaring_no_ansible_group_is_accepted`, `…test_an_excluded_stack_whose_group_has_no_variables_file_is_accepted`, `…test_an_excluded_stack_declaring_no_read_only_secret_is_accepted` | yes (all three) |
| H10 | An excluded stack still needs its inventory source | `M.TestAnExcludedStackStillNeedsItsInventorySource.test_an_excluded_stack_with_no_inventory_source_is_refused` | no: see the note below |
| H11 | A run requested for an excluded stack fails naming the exclusion | `M.TestARunRequestedForAnExcludedStackFailsNamingTheExclusion.test_a_dispatch_naming_an_excluded_stack_fails_saying_it_is_excluded`, `…test_the_excluded_refusal_is_not_the_not_found_refusal`; converse (derived): `…test_a_dispatch_naming_a_converged_stack_beside_an_excluded_one_runs` | yes, yes; converse no |
| H12 | Every stack excluded fails rather than reporting success | `M.TestEveryStackExcludedFailsRatherThanReportingSuccess.test_every_stack_excluded_fails_naming_them` | yes |
| E1 | A new stack needs no workflow edit: covered for the host-converge leg only, where a new stack carries no converge field and must be converged | `M.TestAStackDeclaringNothingAboutTheConvergeIsConverged.test_a_stack_declaring_nothing_about_the_converge_is_converged` | no (the default already holds because nothing reads the field) |
| E7 | A stack declaring nothing about the converge is converged | `M.TestAStackDeclaringNothingAboutTheConvergeIsConverged.test_a_stack_declaring_nothing_about_the_converge_is_converged`, `…test_declaring_nothing_converges_exactly_as_declaring_true_does` | no (same reason; these guard the default's direction once the field is read) |
| E8 | An unrecognised converge value is refused | `M.TestAnUnrecognisedConvergeValueIsRefused.test_an_unrecognised_converge_value_is_refused_naming_stack_and_value` (subtests `maybe`, `yes`, `disabled`); `M.TestTheCommittedDeclarationsStateTheConvergeAsDecided.test_no_committed_declaration_states_the_converge_in_a_refused_form` | yes; committed-tree read no |

Note on H10: this test passes before implementation, and that is expected. The committed discovery reads no converge field, so it already applies the inventory/declaration cross-check to every stack. It is not the "passed before any implementation existed" alarm, because the behaviour already exists. The failure it guards against is the early exit for an excluded stack (design.md Decision 3) being placed before the cross-check.

### Uncovered, with reason

Each of these scenarios appears in the MODIFIED requirements with the same text as in `openspec/specs/iac-cicd-pipeline/spec.md`. This change does not touch the mechanism they describe, and existing modules already cover them. They were not re-derived, because a second copy of an existing test adds no evidence. Where the existing covering test is named, I read it. Where it is not named, I did not confirm which test covers the scenario.

- H2 A host's first converge is the operator's. Text unchanged. It is a run-time fact about a workstation, so `.github/tests` cannot observe it.
- H3 The pre-approval job holds no converge credential. Text unchanged. Existing coverage: `test_host_converge_workflow.TestThePreApprovalJobHoldsNoConvergeCredential`.
- H4 The converge job is gated on the environment's own GitHub Environment. Text unchanged. Existing coverage: `test_host_converge_workflow.TestTheConvergeJobIsGatedOnItsOwnGitHubEnvironment`.
- H5 An environment that cannot be converged fails the workflow. Text unchanged. Existing coverage: `test_host_converge_workflow.TestHostConvergeDiscoveryFailsClosed.test_discovery_fails_on_a_source_whose_environment_declares_no_pipeline` and `…test_discovery_fails_on_an_environment_with_no_inventory_source`. The new excluded-stack case is H10, above.
- H6 Discovery finding no environment fails rather than reporting success. Text unchanged. Existing coverage: `test_host_converge_workflow.TestHostConvergeDiscoveryFailsClosed.test_discovery_fails_when_it_finds_no_environment`. The new all-excluded case is H12. I did not test tasks.md 2.3's "keeping the existing message for a tree with no inventory source at all" separately; the existing test asserts the failure itself.
- H13 A wrong secret stops the run before the host is touched. Text unchanged. Existing coverage: `test_host_converge_workflow.TestAWrongSecretStopsTheRunBeforeTheHostIsTouched`.
- H14 The converge job supplies what the run needs. Text unchanged. Existing coverage: `test_host_converge_workflow.TestTheConvergeJobIsProvisionedBeforeItRuns`.
- H15 The converge runs the Ansible the roles were verified under. Text unchanged. Existing coverage: `test_host_converge_workflow.TestTheConvergeRunsTheAnsibleTheRolesWereVerifiedUnder`.
- H16 One environment's failure does not silence another's. Text unchanged. Existing coverage: `test_host_converge_workflow.TestOneEnvironmentsConvergeDoesNotSilenceAnother`.
- E2 A converge reads its Ansible group from the declaration, not from the stack's name. Text unchanged. Covered by existing modules (`test_a_stack_and_its_environment_are_named_separately`, `test_host_converge_workflow`); I did not map it to a specific test.
- E3 Two stacks declaring the same read-only secret are refused. Text unchanged. Covered by existing modules (`test_environment_agnostic_pipeline`).
- E4 Two stacks declaring the same GitHub Environment are refused. Text unchanged. Same as E3.
- E5 Two stacks declaring the same Ansible group are accepted. Text unchanged. Covered by existing modules.
- E6 A declaration naming the write token's own name is refused. Text unchanged. Existing coverage: `test_host_converge_workflow.TestNoDeclarationNamesTheWriteTokensOwnName`.
- E9 A stack missing its declaration fails the pipeline. Text unchanged. Existing coverage: `test_host_converge_workflow.TestHostConvergeDiscoveryFailsClosed.test_discovery_fails_on_a_declaration_missing_a_field`. Its "a field the running workflow requires" clause meets this change only for an excluded stack, which is H9.
- E10 Discovery finding no stack fails rather than reporting success. Text unchanged. Covered by existing modules (`test_environment_agnostic_pipeline`).
- E11 A stack declaring nothing about the platform stack does not receive it. Text unchanged. Existing coverage: `test_the_platform_stack_deploys_per_stack.TestPlatformDeployDiscoveryFailsClosed.test_a_stack_that_has_not_opted_in_is_excluded_and_named`.
- E12 A stack opting in without authorising the deploy on its host is refused. Text unchanged. Existing coverage: `test_a_deploy_key_is_bound_to_one_host`, `test_the_platform_stack_deploys_per_stack.TestAStackOptingInAuthorisesTheDeployOnItsHost`.
- E13 A host authorising the deploy key before the pipeline is pointed at it is accepted. Text unchanged. Existing coverage: `test_a_deploy_key_is_bound_to_one_host`'s `test_a_host_prepared_before_its_deploy_path_is_not_reported`. After this change `main-staging` is in exactly this state, and that existing test applies to it without modification.
- E14 Two stacks in one environment each owe their own authorisation. Text unchanged. Covered by existing modules (`test_a_deploy_key_is_bound_to_one_host`).

## Assertion classification

These are also annotated in each test's docstring.

**Specified**, tracing to delta SHALL text or a scenario:
- every test under H1, H7–H12, E7 and E8 above
- `M.TestTheCommittedDeclarationsStateTheConvergeAsDecided.test_no_committed_declaration_states_the_converge_in_a_refused_form` (E8, read against the committed tree)
- `M.TestTheCommittedDeclarationsStateTheConvergeAsDecided.test_the_converge_field_names_what_is_true_when_it_is_true` (polarity sentence)

**Derived**, tracing to proposal/design/tasks rather than a scenario:
- `M.TestTheCommittedDeclarationsStateTheConvergeAsDecided.test_staging_declares_its_host_is_not_converged` (design.md Decision 5)
- `…test_staging_declares_no_platform_deploy` (Decision 5)
- `…test_production_keeps_the_converge_default` (tasks.md 3.1)
- `M.TestTheCommittedTreeConvergesProductionAndExcludesStaging.test_a_merge_converges_production_alone_and_names_staging_as_excluded` (design.md Migration Plan step 2)
- `M.TestARunRequestedForAnExcludedStackFailsNamingTheExclusion.test_a_dispatch_naming_a_converged_stack_beside_an_excluded_one_runs` (the converse the refusals need)
- every test in `M.TestTheseReadsDiscriminate` (fixture-driven discriminators; they add no requirement)
- the field spelling `converges_host` (proposal, tasks.md 2.1)
- the stem `exclu` used to recognise "named as excluded" (tasks.md 2.2's message)
- the list of negation words in the polarity check

**Deliberately untested:**
- *"name each such stack ... before it emits the matrix"*: the ordering between the exclusion message and the `$GITHUB_OUTPUT` write. They go to different files, so a test cannot see the order between them.
- *tasks.md 2.1, control-character refusal of the converge value before branching on it*: a derived implementation detail with no scenario. YAML fixtures escape control characters, so testing it would need raw-text fixtures for a property the spec does not state.
- *"or invalidity of a field only its converge would consume"*: only absence is tested (no group, no secret name) plus a group with no vars file. I did not invent an "invalid" form of those fields, because the spec does not define one.
- *Excluded stack counted as "found" in the not-found refusal (H7)*: the spec does not say, so only the converged stack's name is asserted.
- *Comments in `main-staging/pipeline.yml` and `main-production/pipeline.yml` (tasks.md 3.1, 3.2)*: prose with no scenario. Asserting comment wording would turn review content into a brittle test.
- *`docs/backlog.md` entries (tasks.md 4.1)*: not behaviour.

## Static checks: discrimination record

The committed-tree reads in `M.TestTheCommittedDeclarationsStateTheConvergeAsDecided` are static. The ones about `main-staging`, and the polarity check (which requires at least one declaration to carry a converge field), are **red at authoring**. Each fails on its own property:
- `main-staging` does not declare `converges_host: false`
- `main-staging` declares `deploys_platform: true`
- no committed declaration carries a converge field

That red-to-green transition on real content is the observed failure. `M.TestTheseReadsDiscriminate` supplies the fixture that keeps establishing discrimination after the target goes green: the converge reader, the polarity check, the matrix-row parser and the excluded-line matcher, each run over material the test supplies. `test_production_keeps_the_converge_default` and `test_no_committed_declaration_states_the_converge_in_a_refused_form` pass at authoring because the target already carries the property. Their discrimination rests on `test_a_non_boolean_converge_field_is_an_offence` and `test_a_declared_converge_field_reads_as_declared` in that class. All discriminators ran and passed in this pass.

## Obsolete-test candidates

Every entry is a **candidate for human confirmation**, not a conclusion. The search was bounded to `.github/tests/*.py`, using these terms: `converges_host`, `deploys_platform`, `opposite`, `two optional`, `OPPOSITE VALUES`, `proceeds on merge`, `main-staging`, `"staging"`, `opting_in`, `platform_opt_ins`, `sorted(self.declarations)`, and phrases about every stack being converged. No earlier `test-plan.md` was supplied.

1. **`test_the_platform_stack_deploys_per_stack.TestEveryStackThatReceivesThePlatformStackDeclaresIt.test_both_committed_stacks_receive_the_platform_stack`**
   - Superseded by: the MODIFIED *Each Stack Declares Its Own Pipeline Configuration* (which permits a stack to declare `false`), together with design.md Decision 5 and tasks.md 3.2, which flip `main-staging`'s `deploys_platform` to `false`.
   - Evidence: it asserts `sorted(self.declarations) == opting_in()`, meaning every committed stack opts in to the platform deploy. Its own docstring says: "Reconsider this assertion, do not weaken it, if a stack is deliberately taken out of the platform deploy ... the repair is to record that decision here rather than to delete the assertion."
   - Expected effect: it will fail once tasks.md 3.2 lands.
   - Candidate for human confirmation.

Reviewed and judged **not** obsolete. They bear on superseded text but their assertions still hold:
- `test_host_converge_workflow.TestHostConvergeDiscoveryFailsClosed.test_discovery_emits_every_convergeable_environment` and `…test_an_empty_dispatch_input_selects_every_environment` bear on the superseded "each already-configured stack's host SHALL be converged". Their fixture declarations are built from `main-production`'s, which per tasks.md 3.1 will not set the converge field, so under the revised text every fixture stack is still converged.
- `test_a_deploy_key_is_bound_to_one_host.<class>.test_there_is_an_opt_in_to_check` has a docstring saying "GREEN today: both committed stacks opt in". The assertion (at least one stack opts in) still holds with production alone. Only the docstring prose goes stale.
- I searched for an assertion on the superseded sentence "the two defaults are opposite values" and on the stale pipeline.yml passages tasks.md 3.1–3.2 rewrite, and none was found by this search.

## Unresolved project questions

The project records no answer to any of these. Each lists the assumption taken and the tests that depend on it.

1. **The converge field's spelling.** The delta fixes none. I assumed `converges_host`, from the proposal and tasks.md 2.1, matched literally. Depends on it: every fixture-driven test in the module and every committed-tree read.
2. **The matrix encoding.** Assumed: discovery writes JSON to `$GITHUB_OUTPUT` (in `key=value` or heredoc form). A row "names" a stack when one of its values equals the stack name exactly. This matched the committed discovery's output during the baseline run (`stacks=[{...}]`), seen only as test output. Depends on it: every `assertConverges` / `assertNotConverged` call.
3. **What counts as "naming a stack as excluded".** Assumed: one line of stdout, stderr or the step summary carrying both the stack's name and the stem `exclu`. Depends on it: H8, H9, `test_a_stack_declaring_nothing_about_the_converge_is_converged`, and the committed-tree run. For H11, the refusal is recognised as the lines a dispatched run adds over the same tree's undispatched run, at least one of which must carry `exclu`.
4. **Discovery's input surface.** Assumed: discovery reads nothing outside `terraform/stacks/` and `ansible/inventory/`. Depends on it: `M.TestTheCommittedTreeConvergesProductionAndExcludesStaging`, which runs over a copy of those two directories. If discovery reads elsewhere, widen the copy rather than the assertion.
5. **The dispatch input's variable name inside the step body.** This is the same assumption `test_host_converge_workflow` already takes: resolved from the step's `env:` key whose value references `inputs.stack`. Depends on it: every H7/H11 test.
6. **Stack skill.** The library carries a `python` skill, which I loaded. There is no skill for GitHub Actions workflow step bodies. I proceeded on the testing floor plus the existing suite's extract-and-run idiom.
