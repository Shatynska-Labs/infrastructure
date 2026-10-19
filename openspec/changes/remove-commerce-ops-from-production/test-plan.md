# Test plan: remove-commerce-ops-from-production

Derived by `change-test-writer` from the change's delta spec (one MODIFIED requirement in `iac-safety-hardening`, *No Store on This Host Holds Data Requiring Backup*), against the plan committed at `eabde9c`, before any implementation. This file is not an artifact the OpenSpec schema defines; `openspec instructions apply` does not surface it.

Test command (from the repository root): `python3 -m unittest discover --start-directory .github/tests`. Tests below are named in the form `python3 -m unittest <name>` selects with `.github/tests` on `sys.path` (run from `.github/tests`, or through discovery).

New test module: `.github/tests/test_production_no_longer_carries_commerce_ops.py` (abbreviated `M` below, so `M.Class.test` means `test_production_no_longer_carries_commerce_ops.Class.test`).

## Baseline

Full suite, before any test was written: `python3 -m unittest discover --start-directory .github/tests`, 1600 tests, **OK**: none failing.

After this pass: 1628 tests, 7 failing. All 7 are new checks in `M`, each red on the property the change removes (listed below). Nothing that existed before fails.

## What the delta changes

Comparing the delta with the requirement in `openspec/specs/iac-safety-hardening/spec.md`:

- the sentence "One further store, an application's own, does not satisfy it and is named below rather than omitted" is removed from the table's preamble;
- the divergence paragraph (`commerce-ops`'s own PostgreSQL, as of 2026-09-08) and the "Resolving it takes two steps" paragraph are removed;
- the scenario *The stated divergence is not a precedent* is revised: its WHEN no longer names `commerce-ops`, and its THEN adds that a store is admitted only by one of the reasons or by the backup and rehearsed restore.

The other four scenarios are carried unchanged.

## Scenarios

Five `#### Scenario:` blocks in the delta, all under the one MODIFIED requirement. Five are accounted for below.

| # | Scenario | Disposition |
|---|---|---|
| 1 | A persistent store is added to the host | Uncovered: see below |
| 2 | A store's stated reason ceases to hold | Uncovered: see below |
| 3 | An application asks for durable storage on this host | Uncovered: see below |
| 4 | The stated divergence is not a precedent (revised) | Covered by every test in `M`, as listed below |
| 5 | A classified store moves between the host's disks | Uncovered: see below |

**Scenarios 1, 2, 3 and 5: deliberately untested by this pass.** The delta carries their text unchanged, so this change introduces no behaviour under them. Each is a rule on a future change or proposal, judged when that change is reviewed, not a property of a committed file this change alters. The parts that can be read statically are already asserted by existing modules this change does not touch: the `iac-safety-hardening / No Store on This Host Holds Data Requiring Backup` section of `test_ci_configuration.py` covers scenario 2 (Prometheus retention, Grafana provisioning), and `test_the_shared_instance_store_moved.TestNoCommittedFileStillNamesTheSupersededStore` and `test_the_platform_data_mount_moved` cover scenario 5.

**Scenario 4: what is covered and what is not.** The THEN ("SHALL NOT be treated as permission") is a judgement on a future proposal, and is deliberately untested. What this change does under it is remove what a proposal would cite: a stated divergence, and committed files placing `commerce-ops`'s store or its authorisation on the production host as present facts. The requirement text itself is **not read** by any test. `openspec/specs/` changes only at archive (tasks.md 3.4), after verification (3.1), so a check over it would be red through the whole of `apply`. `openspec validate --all` covers the delta's structure.

| Test | Asserts | Classification | State at authoring |
|---|---|---|---|
| `M.TestTheProductionHostVarsNoLongerAuthoriseCommerceOps.test_no_deploy_apps_entry_is_named_commerce_ops` | `main-production.yml`'s `deploy_apps` has no entry named `commerce-ops` | DERIVED: proposal.md, What Changes, first bullet | **red**: names are `platform, commerce-ops, shatynskyj, portfolio, basis-api` |
| `M.TestTheProductionHostVarsNoLongerAuthoriseCommerceOps.test_the_file_names_commerce_ops_nowhere` | no line of `main-production.yml`, comments included, names `commerce-ops` | DERIVED: design.md Decision 5, last item | **red**: lines 30, 65, 66, 67 |
| `M.TestTheProductionHostVarsNoLongerAuthoriseCommerceOps.test_every_other_application_keeps_its_entry` | `platform`, `shatynskyj`, `portfolio`, `basis-api` stay in `deploy_apps` | DERIVED: design.md Decision 2's expected 8 `authorized_keys` lines | green (static guard; its discriminator is `M.TestTheHostVarsReadersFire.test_an_application_dropped_with_it_is_reported`) |
| `M.TestNoDocumentStillPlacesCommerceOpsOnProduction.test_the_runbook_does_not_place_commerce_ops_on_production` | no line of `docs/runbook-rebuild.md` names `commerce-ops` together with `main-production`, `/health` or `trigger` | DERIVED: design.md Decision 5, runbook items 1 to 4 | **red**: 4 lines, starting at line 25 ("On `main-production` there is a third") |
| `M.TestNoDocumentStillPlacesCommerceOpsOnProduction.test_the_bootstrap_guide_does_not_say_host_vars_carry_commerce_ops` | no line of `docs/bootstrap-a-new-host.md` names `commerce-ops` with `host_vars` or `main-production` | DERIVED: design.md Decision 5 | **red**: line 1189 |
| `M.TestNoDocumentStillPlacesCommerceOpsOnProduction.test_the_onboarding_guide_cites_no_commerce_ops_entry_in_production` | no line of `docs/onboard-an-application.md` names `commerce-ops` with `main-production.yml` | DERIVED: design.md Decision 5 (comment-convention paragraph) | **red**: line 48 |
| `M.TestNoDocumentStillPlacesCommerceOpsOnProduction.test_the_onboarding_guide_states_no_production_divergence` | no line of the onboarding guide names `commerce-ops`, `production` and one of `postgres`/`database`/`divergen`/`backup` | DERIVED: design.md Decision 5 (production-divergence paragraph) | **red**: line 166 |
| `M.TestNoDocumentStillPlacesCommerceOpsOnProduction.test_the_platform_readme_describes_no_production_commerce_ops_store` | `platform/README.md` names neither `commerce-ops-postgres-1` nor `commerce_ops_pgdata`, and no line pairs `cutover` with `production` | DERIVED: design.md Decision 5 (`platform/README.md` items) | **red**: 2 lines, starting at line 63 |

Recorded per `testing`: each of the seven red checks is red on the property named, over real content. That transition to green as the change lands is the on-content evidence that the check discriminates. One check was first written passing over its target. The onboarding divergence pairing originally keyed on `main-production`, and the paragraph says "the **production** host". That green-at-authoring result was the alarm, and the pairing was repaired to `production` before this pass ended. It now matches exactly the one paragraph.

**Fixture-driven discriminators.** These all pass, and every detector is run over supplied material that must match and material that must not:

- `M.TestTheHostVarsReadersFire.test_an_entry_named_commerce_ops_is_found`
- `M.TestTheHostVarsReadersFire.test_a_file_without_it_does_not_name_it`
- `M.TestTheHostVarsReadersFire.test_a_comment_naming_it_is_found`
- `M.TestTheHostVarsReadersFire.test_an_absent_deploy_apps_list_is_refused_not_passed`
- `M.TestTheHostVarsReadersFire.test_an_unknown_tag_is_refused_rather_than_read_as_empty`
- `M.TestTheHostVarsReadersFire.test_an_application_dropped_with_it_is_reported`
- `M.TestTheDocumentDetectorsFire.test_the_runbook_warning_is_reported`
- `M.TestTheDocumentDetectorsFire.test_the_runbook_health_example_is_reported`
- `M.TestTheDocumentDetectorsFire.test_the_runbook_trigger_aside_is_reported`
- `M.TestTheDocumentDetectorsFire.test_a_staging_history_sentence_is_not_reported`
- `M.TestTheDocumentDetectorsFire.test_a_rewritten_health_example_is_not_reported`
- `M.TestTheDocumentDetectorsFire.test_the_bootstrap_statement_is_reported`
- `M.TestTheDocumentDetectorsFire.test_a_bootstrap_line_naming_only_the_application_is_not_reported`
- `M.TestTheDocumentDetectorsFire.test_the_onboarding_comment_convention_citation_is_reported`
- `M.TestTheDocumentDetectorsFire.test_the_onboarding_divergence_is_reported`
- `M.TestTheDocumentDetectorsFire.test_the_onboarding_worked_example_is_not_reported`
- `M.TestTheDocumentDetectorsFire.test_the_platform_readme_identifiers_are_reported`
- `M.TestTheDocumentDetectorsFire.test_the_platform_readme_cutover_sentence_is_reported`
- `M.TestTheDocumentDetectorsFire.test_a_platform_readme_without_them_is_not_reported`
- `M.TestTheDocumentDetectorsFire.test_an_empty_document_is_refused_rather_than_read_as_clean`

Every one of these is DERIVED: it fixes how this module reads its targets.

**Known limits of the derived pairings.** These are deliberately untested, with the reasons:

- The detectors key on co-occurrence in one line. Prose here is not hard-wrapped, so a line is a paragraph. A rewrite that still states `commerce-ops` on production, but splits the application and the host across paragraphs, passes. Code review is what catches that.
- Historical sentences and the worked example are kept by the proposal's Non-Goals. A kept sentence that happens to pair `commerce-ops` with a listed term will fail its check. If that happens it is a derived assertion to reconsider, recorded here, never edited silently. `trigger` (runbook) and `production` + `database` (onboarding) are the pairings most likely to over-reach.
- The host clean-up (sudoers files, `/opt/commerce-ops`, `authorized_keys` lines) is a read of a live host, which this suite may not make. It is evidenced by the operator's pasted output (tasks.md 3.3).
- `docs/backlog.md` (tasks.md 2.4, 3.4) is not tested. It is a record entry and not a statement about the host.

## What each task must make pass

- **2.1**: `M.TestTheProductionHostVarsNoLongerAuthoriseCommerceOps.test_no_deploy_apps_entry_is_named_commerce_ops` and `M.TestTheProductionHostVarsNoLongerAuthoriseCommerceOps.test_the_file_names_commerce_ops_nowhere`, while keeping `M.TestTheProductionHostVarsNoLongerAuthoriseCommerceOps.test_every_other_application_keeps_its_entry` green.
- **2.2**: all five tests in `M.TestNoDocumentStillPlacesCommerceOpsOnProduction`.
- **2.3**: see the obsolete-test list. Removing the runbook's production warning (2.2) turns entry 1 red, so 2.2 and 2.3 land together.
- **3.1**: the whole suite green.

## Obsolete tests (candidates for human confirmation)

These were searched for within `.github/tests/*.py` only, on `commerce`, `divergence`, `precedent`, `2026-09-08`, `iac-safety-hardening` and the requirement's name. No earlier `test-plan.md` was supplied. Each entry is a **candidate for human confirmation, not a conclusion**.

1. `test_the_rebuild_runbook_records_its_rehearsal.TestWhatARebuildLosesIsStatedBeforeItIsLost.test_the_losses_are_named_before_the_step_that_destroys_the_server`
   - **Superseded by:** the MODIFIED delta's removal of the divergence paragraph.
   - **Evidence:** it calls `losses_not_stated_before_the_destroy`, which requires `UNMET_STORE = "commerce-ops"` to be named before the destroy step. The module comment at that constant justifies it by quoting the removed paragraph ("this requirement SHALL be read as unmet in that one respect"). After this change it requires a sentence that `M.TestNoDocumentStillPlacesCommerceOpsOnProduction.test_the_runbook_does_not_place_commerce_ops_on_production` forbids.
   - design.md Decision 4 records the intended disposition: the set becomes an empty literal.
   - **Disposition (apply):** changed. `UNMET_STORE` became `UNMET_STORES: tuple[str, ...] = ()`, with its comment saying the requirement records none since this change, and `losses_not_stated_before_the_destroy` takes the set as a parameter defaulting to it. What the runbook must say about a recorded store is unchanged.
2. `test_the_rebuild_runbook_records_its_rehearsal.TestTheOrderingDetectorsFire.test_an_unmet_store_named_only_after_the_destroy_step_is_reported`
   - **Superseded by:** the same delta.
   - **Evidence:** it asserts `UNMET_STORE in entry`, where `UNMET_STORE` is the `commerce-ops` literal. Once the expected set is empty, it no longer has a store to look for.
   - Decision 4 keeps this negative case, showing that a store the requirement does record must be named. It would then use a fixture store.
   - **Disposition (apply):** changed. It passes `("commerce-ops",)` to the detector as the fixture's recorded store, asserts the unaltered fixture reports nothing, and that the fixture without the sentence reports that store.
3. `test_the_rebuild_runbook_records_its_rehearsal.TestTheOrderingDetectorsFire.test_the_losses_stated_before_the_destroy_step_are_not_reported`
   - **Superseded by:** the same delta, weakly.
   - **Evidence:** its `DOCUMENT` fixture states "on main-production, commerce-ops's own PostgreSQL is lost outright", which is the superseded fact. It does not fail as a result. It is listed so that the reader deciding entries 1 and 2 sees the fixture they share, and it may well be kept as it is.
   - **Disposition (apply):** kept unchanged. The fixture is a sample document, and entry 2 now relies on its sentence.

Examined and **not** obsolete:

- `test_a_shared_instance_reset_is_visible.py`: its fixture `deploy_apps` names `commerce-ops` only as a sample name.
- `test_the_shared_instance_has_its_first_database.py` and `test_the_requirement_names_where_the_recipe_lives.py`: these read the *iac-platform-services* divergence, which the proposal's Non-Goals keep.
- `test_the_bootstrap_documents_static_conventions.py`: `commerce-ops` is a sample application name there.

## Unresolved project questions

- **Python skill and linter.** The `python` skill was loaded. `ruff` is not installed in this environment, and `.pre-commit-config.yaml` runs no Python linter, so no lint was run on `M`. `pre-commit run --files` on it passed (gitleaks, ansible-lint). Assumption: the suite's own conventions, which are standard library plus PyYAML and no linter, are what the module must meet. All of `M` depends on this.
- **Line numbers quoted above** are from the tree at `eabde9c`, and only illustrate the red state. No test depends on them.

## Missing shared arrangement

AGENTS.md *Testing* records that no suite has a shared test arrangement, and the dispatch named none. Every piece below is declared in `.github/tests/test_production_no_longer_carries_commerce_ops.py`. The proposed home for each is **none to propose**: the project names no shared arrangement. `docs/backlog.md` `share-the-static-suites-test-arrangement` is the change that would give it one. There is no near-miss in any shared arrangement, since none exists.

1. `_repo_root` / `ROOT`
   - **Stands in for:** the repository-root locator.
   - **Used by:** every non-fixture test in `M`.
   - **Found in test module:** `test_ci_configuration.py` (`_repo_root`, `ROOT`), declared here identically.
   - **Disposition (apply):** kept local. The project records no shared test arrangement (`AGENTS.md` *Testing*), so there is nowhere to promote it; `docs/backlog.md` `share-the-static-suites-test-arrangement` is where it would go.
2. `read_text`, with `_shown`
   - **Stands in for:** reading a committed file, failing where it is absent.
   - **Used by:** every test in `M.TestTheProductionHostVarsNoLongerAuthoriseCommerceOps` and `M.TestNoDocumentStillPlacesCommerceOpsOnProduction`, and `M.TestTheDocumentDetectorsFire.test_an_empty_document_is_refused_rather_than_read_as_clean`.
   - **Found in test module:** `test_ci_configuration.py` (`read_text`). It is declared here with an added refusal of an empty file, because an absence check over an empty file would pass having read nothing.
   - **Disposition (apply):** kept local. The project records no shared test arrangement (`AGENTS.md` *Testing*), so there is nowhere to promote it; `docs/backlog.md` `share-the-static-suites-test-arrangement` is where it would go.
3. `_VaultTolerantLoader`, `host_vars`, `UnreadableHostVars`
   - **Stands in for:** reading an Ansible `host_vars` file that may carry `!vault`, refusing any other tag.
   - **Used by:** all of `M.TestTheProductionHostVarsNoLongerAuthoriseCommerceOps` and `M.TestTheHostVarsReadersFire`.
   - **Found in test modules:** equivalents in `test_the_platform_stack_deploys_per_stack.py` (`AnsibleTolerantLoader`, `inventory_variables`, `UnreadableInventoryVars`), `test_a_deploy_key_is_bound_to_one_host.py` (`AnsibleTolerantLoader`) and `test_a_shared_instance_reset_is_visible.py` (`_TolerantLoader`).
   - **Disposition (apply):** kept local. The project records no shared test arrangement (`AGENTS.md` *Testing*), so there is nowhere to promote it; `docs/backlog.md` `share-the-static-suites-test-arrangement` is where it would go.
4. `deploy_app_names`
   - **Stands in for:** the names in a host's `deploy_apps` list, refusing an absent or empty list.
   - **Used by:** `M.TestTheProductionHostVarsNoLongerAuthoriseCommerceOps.test_no_deploy_apps_entry_is_named_commerce_ops`, `M.TestTheProductionHostVarsNoLongerAuthoriseCommerceOps.test_every_other_application_keeps_its_entry` and `M.TestTheHostVarsReadersFire.*`.
   - **Found in test module:** a similar reader in `test_a_shared_instance_reset_is_visible.py`.
   - **Disposition (apply):** kept local. The project records no shared test arrangement (`AGENTS.md` *Testing*), so there is nowhere to promote it; `docs/backlog.md` `share-the-static-suites-test-arrangement` is where it would go.

Each entry's disposition (promoted, or kept and why) is to be written against it by `apply` (tasks.md 2.5).
