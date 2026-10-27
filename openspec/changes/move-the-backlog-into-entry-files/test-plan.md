# Test plan: move-the-backlog-into-entry-files

Derived by `change-test-writer` from the plan at commit `728c0df`, before any implementation. This file is not an artifact the OpenSpec schema defines: `openspec instructions apply` does not surface it, so it must be read on purpose.

Test command: `python3 -m unittest discover --start-directory .github/tests`, from the repository root. Single tests are selected with `-k <module>.<Class>.<test>` through discovery (the form used below). Several sweeps read tracked files only, so run with every new file staged (task 4.1).

New file (staged, uncommitted): `.github/tests/test_a_requirement_cites_its_backlog_entry_by_name.py` — 36 tests.

## Baseline (before this pass)

Full suite, taken on `728c0df` with nothing staged: **1695 tests, 1 failure, 0 errors, no skips reported.**

- Pre-existing failure: `test_the_shared_instance_has_its_first_database.TestTheBacklogCarriesTheEntryTheRequirementNames.test_the_requirement_names_the_backlog_entry` (subtest on this change's iac-platform-services delta). It is caused by the committed MODIFIED delta itself: the test's pattern is fixed to `docs/backlog.md`, and the delta now reads `docs/backlog/`. Task 3.2 owes its repair; it is listed below as an obsolete-test candidate.

After this pass (new file staged): **1731 tests, 8 failures** — the baseline failure plus the 7 red-at-authoring tests listed below. The suite-wide audits in `test_ci_configuration.py` (imports, subprocesses, citation paths) and the retired-name sweep pass over the new file.

## Scenario accounting

The two deltas are MODIFIED and change one phrase each — "tracked in `docs/backlog.md` as" becomes "tracked in `docs/backlog/` as" — in a body paragraph, not in any scenario. Diffing each delta against its requirement under `openspec/specs/` confirms every scenario is word for word unchanged. No scenario introduces behaviour, so this pass wrote no new test for any scenario; the new tests trace to the changed body sentence and to design/tasks (next section). 10 scenarios in the deltas, 10 accounted for.

### iac-host-configuration — A Host-Scoped Variable Lives in the Host's Own Vars File

| # | Scenario | Accounting |
|---|---|---|
| 1 | Two stacks share an environment | Covered by existing tests (unchanged text): `test_a_deploy_key_is_bound_to_one_host.TestTwoStacksInOneEnvironmentEachOweTheirOwnAuthorisation`, `test_a_deploy_key_is_bound_to_one_host.TestTheDeployKeyAuthorisationsLiveInTheHostsOwnFile` |
| 2 | A value that is a property of the environment | Covered by existing tests (unchanged text): `test_a_deploy_key_is_bound_to_one_host.TestAnEnvironmentWideValueStaysInTheEnvironmentsFile` |
| 3 | A stack whose declared server has no vars file is reported | Covered by existing tests (unchanged text): `test_a_deploy_key_is_bound_to_one_host.TestEachStacksHostHasAVarsFileOfItsOwn.test_every_stack_has_a_host_vars_file_named_for_its_server` |
| 4 | A host vars file is keyed on the name Terraform declares | Covered by existing tests (unchanged text): `test_a_deploy_key_is_bound_to_one_host.TestEachStacksHostHasAVarsFileOfItsOwn.test_no_host_vars_file_is_named_for_a_server_no_stack_declares` |

### iac-platform-services — Single Shared PostgreSQL Instance, Per-Application Databases

| # | Scenario | Accounting |
|---|---|---|
| 5 | A new application requests a database | Covered by existing tests, as a necessary condition only (unchanged text): the recipe classes of `test_the_shared_instance_has_its_first_database` (e.g. `TestTheRecipeKeepsThePasswordOffCommandLines`). Host state is not statically readable. |
| 6 | An application needs durable storage | **Uncovered.** Text unchanged by this delta; no existing test was found bearing on it by a search of `.github/tests/*.py`. It obliges where data is placed, which no static read of a committed file establishes. Pre-existing gap, not introduced here. |
| 7 | An application's data divides into durable and non-durable parts | Covered by existing tests (unchanged text): `test_the_shared_instance_has_its_first_database.TestTheChangeRecordStatesTheTableDivision` |
| 8 | A staging database holds rehearsal data | **Uncovered.** Text unchanged by this delta; no existing test found by the same search. It obliges what data enters a database on a host — host state, not a static property. Pre-existing gap. |
| 9 | The automation trigger has fired and the mechanism is not built | Covered by existing tests (unchanged text): `test_the_shared_instance_has_its_first_database.TestTheRequirementStatesTheTriggerHasFired`. The changed citation sits in this scenario's paragraph but is not one of its stated elements; it is covered by the new tests below. |
| 10 | The document this requirement names holds the recipe | Covered by existing tests (unchanged text): `test_the_requirement_names_where_the_recipe_lives.TestTheNamedDocumentHoldsTheRecipe`, `...TestNoSecondDocumentHoldsACopyOfTheRecipe` |

## New tests, by task, with classification

Module prefix for every id below: `test_a_requirement_cites_its_backlog_entry_by_name.`

"Red" = failing at authoring, on the property named; it must go green when the task lands. "Green" = passing at authoring; its discriminators are listed.

### Task 3.1 / 3.2 (design D1, D2)

| Test | Classification | State at authoring |
|---|---|---|
| `TestEachRequirementCitesItsEntryInTheBacklogDirectory.test_each_requirement_cites_its_entry_in_the_new_form` | SPECIFIED — each delta's body: "tracked in `docs/backlog/` as `<entry>`", with the entry name the delta states | Green (the deltas already carry the phrase; read from the live delta, main spec once archived). Discriminated by `TestTheCitationDetectorFires.*` |
| `TestEachRequirementCitesItsEntryInTheBacklogDirectory.test_each_cited_entry_is_a_file_in_the_backlog_directory` | SPECIFIED (the citation); DERIVED sufficiency of a file check (design D2) | **Red**: `docs/backlog/automate-per-application-database-provisioning.md` and `docs/backlog/put-the-remaining-host-scoped-variables-on-the-host-axis.md` are not files (task 1.1) |
| `TestEachRequirementCitesItsEntryInTheBacklogDirectory.test_no_citing_requirement_names_an_entry_files_path` | DERIVED — design D1 (cite by name, not path) | Green. Discriminated by `TestTheCitationDetectorFires.test_the_path_form_yields_no_entry_and_is_reported_as_a_path` |
| `TestTheBasisApiFollowUpIsAnEntryFile.test_the_follow_up_entry_is_a_file` | DERIVED — design D2, task 3.2 (`finish-basis-api-s-move-to-its-own-database`) | **Red**: the entry file does not exist (task 1.1) |

### Task 3.4 (design Risks)

| Test | Classification | State at authoring |
|---|---|---|
| `TestNoRequirementCitesTheOldBacklogPath.test_the_guard_reads_requirements_at_all` | DERIVED — precondition (a guard reading nothing passes); the threshold of 10 is this pass's judgment | Green |
| `TestNoRequirementCitesTheOldBacklogPath.test_no_requirement_names_the_old_backlog_path` | DERIVED — design Risks, task 3.4 | Green: the two main-spec citations are shadowed by this change's live MODIFIED deltas, as design Risks states they should be. Discriminated by `TestTheOldPathGuardFires.*` |
| `TestTheOldBacklogFileIsGone.test_the_old_backlog_file_does_not_exist` | DERIVED — design Risks, task 3.4 | **Red**: `docs/backlog.md` exists (task 1.1) |

### Tasks 2.1 / 2.2 (design D4, D6)

| Test | Classification | State at authoring |
|---|---|---|
| `TestTheWorkflowBlockAndConventionsFollowTheMove.test_the_workflow_block_is_marked_v12` | DERIVED — task 2.1; asserts the marker only | **Red**: marker reads `v10` |
| `TestTheWorkflowBlockAndConventionsFollowTheMove.test_the_workstreams_readme_is_seeded` | DERIVED — design D4, task 2.1 | **Red**: `docs/workstreams/README.md` absent |
| `TestTheWorkflowBlockAndConventionsFollowTheMove.test_the_project_conventions_do_not_name_the_old_backlog` | DERIVED — task 2.2, design D6 | **Red**: the "Project conventions" section names `docs/backlog.md` twice |

### Fixture-driven discriminators (all DERIVED, all green)

- `TestTheCitationDetectorFires` (10 tests): new form yields its entry, also across a line break; old form and path form yield none; path form is reported as a path; an existing entry file is clean; a missing file, a directory of the entry's name, an entry named only inside a single `docs/backlog.md`, a citation of another entry, and an old-form citation are each reported.
- `TestTheRequirementIsReadWhereItIsAboutToStand` (3): a live delta is read over the main spec; the main spec is read where only an archived delta carries the requirement; a tree carrying it nowhere yields nothing.
- `TestTheOldPathGuardFires` (8): a main-spec requirement naming the old path is reported; one shadowed by a live MODIFIED delta is read from the delta; a live ADDED delta does not shadow; a live delta (ADDED or MODIFIED) naming the old path is reported; the archive is not read; text outside any requirement (a Purpose section) is not reported; a block stops at the next requirement.
- `TestTheOldFileCheckFires` (2): a tree with `docs/backlog.md` is detected; a tree with only entry files is clean.
- `TestTheConventionDetectorsFire` (3): the conventions section excludes the workflow block; a pointer inside it is seen; the marker version is read.

### Deliberately untested

- **Design D3 / task 3.3** (the line exemption in `test_the_shared_instance_store_moved.py` names `docs/backlog/rename-the-requirements-that-read-narrower-than-they-are.md`): that module's own `test_every_exemption_still_names_the_store` already fails where an exemption's marker matches no line in the file it names, so a duplicate here would add only a second coupling to that module's needle.
- **Task 2.1, "the block matches the fragment's body exactly"**: the fragment lives in ai-toolkit, outside this repository; the suite cannot read it. Only the marker is asserted.
- **Task 1.1/1.2** (entry count equals the old headings, frontmatter parses as YAML, `recorded_by` supported by each body): one-time verifications of a conversion against a file that is then deleted; the entry format is ai-toolkit's contract.
- **Design D6's other 118 pointers**: out of scope by D6 (recorded as `repoint-the-backlog-references`).
- **Task 1.3** (the `repoint-the-backlog-references` entry exists): not asserted; a test would have to be obsoleted when that fix closes. Can be added if wanted.

## Obsolete-test candidates

Every entry is a **candidate for human confirmation**, not a conclusion. None was edited or deleted. Found by a search of `.github/tests/*.py` for `backlog` and the names `docs/backlog.md`, the two entry names and `finish-basis-api-s-move-to-its-own-database`. No earlier `test-plan.md` was supplied.

| Test | Superseded by | Evidence |
|---|---|---|
| `test_the_shared_instance_has_its_first_database.TestTheBacklogCarriesTheEntryTheRequirementNames.test_the_requirement_names_the_backlog_entry` | MODIFIED iac-platform-services delta (design D2) | `BACKLOG_ENTRY` pattern is fixed to `` `docs/backlog\.md`\s+as `` and fails on the delta now (baseline failure) |
| `test_the_shared_instance_has_its_first_database.TestTheBacklogCarriesTheEntryTheRequirementNames.test_the_backlog_carries_that_entry` | MODIFIED iac-platform-services delta (design D2) | `read_text(BACKLOG)` with `BACKLOG = ROOT / "docs" / "backlog.md"`; the file is removed by task 1.1. Currently passes vacuously (entry is None, `continue`) |
| `test_the_shared_instance_has_its_first_database.TestTheDivergenceDetectorFires.test_a_conforming_requirement_yields_no_omission` and `...test_a_divergence_naming_no_backlog_entry_is_reported` | MODIFIED iac-platform-services delta | `CONFORMING_REQUIREMENT_FIXTURE` says "tracked in `docs/backlog.md` as"; once the pattern follows D1 the "conforming" fixture no longer conforms |
| `test_a_deploy_key_is_bound_to_one_host.TestTheUnmetPlacementsAreTheOnesTheRequirementNames.test_the_backlog_entry_the_requirement_cites_exists` | MODIFIED iac-host-configuration delta (design D2) | Asserts `BACKLOG.is_file()` and the entry name in its text, `BACKLOG = ROOT / "docs" / "backlog.md"`; docstring quotes the old phrase |
| `test_basis_api_durable_store.TestTheDocumentsRecordTheStore.test_the_backlog_carries_the_follow_up` | No delta — design D2 / task 3.2 (the conversion) | `read_required(ROOT / BACKLOG)` with `BACKLOG = "docs/backlog.md"` |
| `test_basis_api_durable_store.TestTheDocumentChecksDiscriminate.test_good_documents_are_accepted` and `...test_a_backlog_without_the_entry_is_reported` | No delta — design D2 | Exercise `backlog_offences(text)`, a text search; superseded only if task 3.2 replaces it with a file check |
| `test_the_shared_instance_store_moved.TestNoCommittedFileStillNamesTheSupersededStore.test_every_exemption_still_names_the_store` and `...test_no_committed_file_names_the_superseded_store` | No delta — design D3 / task 3.3 | `EXEMPT_LINES` names `"docs/backlog.md"`; after the conversion the exemption matches no file and the dated line, now in an entry file, is unexempted (design's "two failures") |

Not candidates: the fixture-tree tests in `test_the_shared_instance_store_moved.py` and other modules that use `docs/backlog.md` as a synthetic path (design D3 keeps them).

## Unresolved project questions

1. **No library skill for the stack under test.** The subject is OpenSpec Markdown read by `unittest`; no stack skill covers it. Proceeded on the `testing` floor alone. Affects: none specifically.
2. **The guard and source resolution walk `openspec/changes/` on disk**, not tracked files, so an untracked change directory in a working tree is read. Assumed acceptable because `test_the_shared_instance_has_its_first_database.requirement_sources` does the same. Affects: `TestNoRequirementCitesTheOldBacklogPath.*`, `TestEachRequirementCitesItsEntryInTheBacklogDirectory.*`.
3. **The guard reads every `### Requirement:` block in a live delta, including blocks under a `REMOVED` section** (their Reason/Migration text). Assumed this is what "any requirement ... in a live delta" means. Affects: `TestNoRequirementCitesTheOldBacklogPath.test_no_requirement_names_the_old_backlog_path`.
4. **`test_the_old_backlog_file_does_not_exist` uses `Path.exists()`**, so an untracked stray `docs/backlog.md` also fails it. Assumed intended (design: "fails while `docs/backlog.md` exists").
5. **The entry names are hard-coded** from the deltas. When either entry is closed and its requirement paragraph replaced, `test_each_requirement_cites_its_entry_in_the_new_form` and `test_each_cited_entry_is_a_file_in_the_backlog_directory` become obsolete-test candidates for that change.
6. **The sibling repository's reference test and test plan were not read**: they are outside this pass's read set (change artifacts, specs, convention files, files within `.github/tests/*.py`).

## Missing shared arrangement

The dispatch named no shared arrangement, and AGENTS.md "Testing" states the suite has none (so no project question is raised for that). Every declaration below lives in `.github/tests/test_a_requirement_cites_its_backlog_entry_by_name.py`. Proposed home: none to propose — no shared arrangement exists; the backlog entry `share-the-static-suites-test-arrangement` is the change that would create one.

| Declared | Stands in for | Used by | Near-miss in shared arrangement | Found in test module |
|---|---|---|---|---|
| `_repo_root`, `ROOT` | Repository root locator | every test reading the repository | n/a (none exists) | `test_ci_configuration.py` (`_repo_root`, `ROOT`) |
| `ARCHIVE_SEGMENT` | The archive directory's name | `_live_change_directories`, `TestTheRequirementIsReadWhereItIsAboutToStand.*`, `TestTheOldPathGuardFires.*` | n/a | `test_ci_configuration.py` |
| `_tree` | Scratch repository tree builder | all `...DetectorFires`/`...GuardFires`/`...ReadWhere...` classes | n/a | `test_the_shared_instance_has_its_first_database.py` (`TestTheRequirementIsReadWhereItIsAboutToStand._tree`) |
| `requirement_blocks`, `requirement_sources` | Spec parser and as-it-will-stand resolution | `TestEachRequirementCitesItsEntryInTheBacklogDirectory.*`, `TestTheRequirementIsReadWhereItIsAboutToStand.*` | n/a | Close equivalents in `test_the_shared_instance_has_its_first_database.py` and `test_the_requirement_names_where_the_recipe_lives.py`; neither returns every block with its delta operation, which the guard needs |
| `requirements_as_they_stand`, `old_path_citations` | Shadow-aware requirement enumeration | `TestNoRequirementCitesTheOldBacklogPath.*`, `TestTheOldPathGuardFires.*` | n/a | not found elsewhere |
| `NEW_FORM_BLOCK`, `OLD_FORM_BLOCK`, `PATH_FORM_BLOCK`, `_main`, `_delta`, `MAIN_SPEC`, `LIVE_DELTA`, `OTHER_LIVE_DELTA`, `ARCHIVED_DELTA` | Spec/delta fixtures | `TestTheCitationDetectorFires.*`, `TestTheRequirementIsReadWhereItIsAboutToStand.*`, `TestTheOldPathGuardFires.*`, `TestTheOldFileCheckFires.*` | n/a | Shape adapted from `CONFORMING_REQUIREMENT_FIXTURE` in `test_the_shared_instance_has_its_first_database.py` |
| `TestTheConventionDetectorsFire.AGENTS` | AGENTS.md fixture | `TestTheConventionDetectorsFire.*` | n/a | not found elsewhere |

Disposition: every entry above **kept** local. Reason: AGENTS.md "Testing" records that this suite has no shared test arrangement, so there is nothing to promote into; creating one is `share-the-static-suites-test-arrangement`.
