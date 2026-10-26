# Test plan: record-basis-api-durable-store

Written by the independent test-authoring pass (`change-test-writer`) against the plan committed as e002eea, before any implementation. This file is not an artifact the OpenSpec schema knows about: `openspec instructions apply` will not list it, so it has to be read on purpose.

The pass is additive only: it added one Terraform test file, one static test module and two Molecule scenario directories and edited, deleted or disabled no existing test.

## Files written

| Suite | File | Command (from) |
|---|---|---|
| Terraform module | `terraform/modules/volume/tests/location.tftest.hcl` | `terraform test -filter=tests/location.tftest.hcl` (from `terraform/modules/volume`) |
| Molecule | `ansible/roles/platform_data_volume/molecule/with-application-subdirs/` (`molecule.yml`, `prepare.yml`, `converge.yml`, `verify.yml`) | `../../scripts/run-molecule test -s with-application-subdirs` (from `ansible/roles/platform_data_volume`) |
| Molecule | `ansible/roles/platform_data_volume/molecule/without-application-subdirs/` (same four files) | `../../scripts/run-molecule test -s without-application-subdirs` |
| Static | `.github/tests/test_basis_api_durable_store.py` | `python3 -m unittest discover --start-directory .github/tests -k test_basis_api_durable_store.<Class>.<test>` (from the repository root) |

`terraform test` selects by file, not by run block; the run names below identify which assertion failed. Molecule scenarios take loop-minor offsets 7 and 8 (0 to 6 are taken). Both scenario names sort after every existing scenario, so while `with-application-subdirs` is red, `test --all` still executes every pre-existing scenario before stopping.

Static-suite IDs below are abbreviated `T.<Class>.<test>` for `test_basis_api_durable_store.<Class>.<test>`.

## What the implementation must make pass, per task

- **1.1 (volume module)** — `location.tftest.hcl`: `plan_forwards_the_declared_location_when_no_server_is_given`, `plan_forwards_server_id_when_location_is_null`, `plan_rejects_both_server_id_and_location`, `plan_rejects_neither_server_id_nor_location`, `plan_rejects_an_empty_location`. The existing four files must stay green (12 runs), including `creation.tftest.hcl` `plan_requires_non_empty_server_id`.
- **1.2 (main-production stack)** — `T.TestProductionVolumeSurvivesTheServerToggle.test_the_production_volume_survives_its_server_toggle`. Must stay green: `…test_the_production_volume_server_reference_is_null_without_a_server`, `…test_the_production_volume_keeps_its_address`, `…test_the_staging_volume_stays_coupled_to_its_server`.
- **2.1 (role)** — Molecule `with-application-subdirs` (`verify: Executed: Successful` in DETAILS). Must stay green: `without-application-subdirs` and every existing scenario.
- **2.2 (inventory)** — `T.TestTheApplicationsDirectoriesAreHostScoped.test_every_environment_carries_the_platform_metrics_directory`, `…test_production_declares_basis_api_directories_in_its_own_host_vars`, `…test_host_scoped_entries_sit_beneath_their_application`. Must stay green: `…test_no_environment_wide_file_declares_an_applications_directory`, `…test_no_other_host_declares_basis_api_directories`.
- **3.1 (node-exporter flag)** — `T.TestABackedUpStoresBackupAgeIsAlertedOn.test_node_exporter_collects_the_application_metrics_directories`.
- **3.2 (rules)** — `T.TestABackedUpStoresBackupAgeIsAlertedOn.test_the_four_rules_say_what_the_requirement_says`, `…test_three_rules_wait_before_firing`. Must stay green: `…test_the_rules_are_routed_like_every_other_rule`.
- **4.1** — `T.TestTheDocumentsRecordTheStore.test_the_onboarding_guide_records_the_admitted_store`. **4.2** — `…test_the_rebuild_runbook_names_the_production_store`. **4.3** — `…test_the_backlog_carries_the_follow_up`.
- Every `T.Test…Discriminate.*` test is green at authoring and must stay green: they are the fixture-driven discriminators showing each static check can fail.

## Baseline

Taken before any test was written, in this working tree at e002eea:

- Static suite, full: `python3 -m unittest discover --start-directory .github/tests` — 1628 tests, OK.
- `terraform/modules/volume`, full: `terraform test` — 12 passed, 0 failed.
- Molecule: no baseline was taken before writing. A scoped run of `platform_data_volume`'s `default` scenario after writing (the new scenarios do not touch it) — exit 0, `verify: Executed: Successful`. The other five existing scenarios of the role were not run in this pass.

After writing: static suite 1692 tests, 10 failures, all in the new module (the 1628 pre-existing tests still pass with the new Molecule files present, so the scenario-definition conventions `test_ci_configuration.py` enforces accept them). `ansible-lint` over the two new scenario directories: 0 failures.

## Failure state of each new test at authoring

- `location.tftest.hcl` — **target absent** (state 2). The first run fails with `required variable may not be set to null` on `var.server_id` and a warning that the module declares no `location`; Terraform then skips the other four runs. None of the five runs' assertions has executed, and their soundness is unverified until the module declares `location`.
- `T.TestProductionVolumeSurvivesTheServerToggle.test_the_production_volume_survives_its_server_toggle` — **red on real content** (state 1): `count` reads `var.server_enabled`; no `location` is passed.
- `T.TestTheApplicationsDirectoriesAreHostScoped`: `test_every_environment_carries_the_platform_metrics_directory` (neither group_vars file declares the three `applications` entries), `test_production_declares_basis_api_directories_in_its_own_host_vars` and `test_host_scoped_entries_sit_beneath_their_application` (no `platform_data_volume_host_subdirs`) — red on real content (state 1).
- `T.TestABackedUpStoresBackupAgeIsAlertedOn`: `test_node_exporter_collects_the_application_metrics_directories` (node-exporter has no textfile directory flag; it already mounts `/` read-only at `/host/root` and is not on `platform_edge`), `test_the_four_rules_say_what_the_requirement_says` and `test_three_rules_wait_before_firing` (no rule of those names) — red on real content (state 1).
- `T.TestTheDocumentsRecordTheStore`, all three — red on real content (state 1): the onboarding guide still says "no application has cleared that bar" and names neither `basis-api` nor the contract metrics nor the host list; the runbook names neither `BackupStale` nor `basis-api`; the backlog lacks the entry.
- Molecule `with-application-subdirs` — red, state 1. Converge and idempotence pass. In verify, the environment's entries (`prometheus`, `applications`, `applications/platform`, `applications/platform/metrics`) pass, but `applications/basis-api*` is missing. The role ignores a variable it doesn't know about.
- Green at authoring, protecting a property the tree already has. Each one is paired with a fixture discriminator: `…test_the_production_volume_server_reference_is_null_without_a_server`, `…test_the_production_volume_keeps_its_address`, `…test_the_staging_volume_stays_coupled_to_its_server`, `…test_no_environment_wide_file_declares_an_applications_directory`, `…test_no_other_host_declares_basis_api_directories`, `…test_the_rules_are_routed_like_every_other_rule`. The last one is green only because none of the four rules exists yet, so its real reading starts at 3.2.
- Molecule `without-application-subdirs` — **passed on its first run before implementation** (state 4, investigated). This behaviour already exists: today's role never refers to a host-scoped list, so it creates exactly the environment's list and does not fail when no list is set. This is not counted as coverage of anything new. What it guards is the implementation: if the role references `platform_data_volume_host_subdirs` without a default, the converge fails. If the role creates application directories out of any list other than the host's own, verify fails. Its ability to fail was not demonstrated by a fixture in this pass, because a Molecule scenario cannot be fed a deliberately broken role without writing role code.

## Scenario accounting

38 `#### Scenario:` blocks across the five delta specs; 38 accounted for below — 20 covered by at least one named test (most of them partially), 18 uncovered with a reason. "Partial" marks a scenario whose THEN is a `terraform plan` outcome or a runtime alert: the tests cover the committed shape that outcome rests on, and the outcome itself is checked by tasks 1.4/1.5 or 7.1/7.2.

### iac-data-volumes (MODIFIED) — 9

| Scenario | Tests | Coverage |
|---|---|---|
| Toggle enabled creates the volume | `T.TestProductionVolumeSurvivesTheServerToggle.test_the_production_volume_survives_its_server_toggle`; `location.tftest.hcl` `plan_forwards_server_id_when_location_is_null`; existing `creation.tftest.hcl` `plan_creates_volume_with_declared_configuration`, `plan_attaches_to_server_at_creation` | Partial |
| Volume toggle disabled creates nothing | `T.…test_the_production_volume_survives_its_server_toggle` (count reads `var.volume_enabled`) | Partial |
| Disabling the server keeps the production volume | `T.…test_the_production_volume_survives_its_server_toggle`, `T.…test_the_production_volume_server_reference_is_null_without_a_server`, `T.…test_the_production_volume_keeps_its_address`; `location.tftest.hcl` `plan_forwards_the_declared_location_when_no_server_is_given` | Partial |
| Disabling the server also removes the volume (staging) | `T.…test_the_staging_volume_stays_coupled_to_its_server` | Partial |
| Re-enabling requires no lost configuration | `T.…test_the_production_volume_survives_its_server_toggle` (the kept volume's location comes from the stack's own variable; nothing new to reconstruct) | Partial |
| Volume is created already attached | `location.tftest.hcl` `plan_forwards_server_id_when_location_is_null`; `T.…test_the_production_volume_survives_its_server_toggle` (server_id references the server) | Covered |
| Volume shares the server's location | `T.…test_the_production_volume_survives_its_server_toggle` (the disabled-server branch is the server module's own `location` expression); `location.tftest.hcl` `plan_forwards_the_declared_location_when_no_server_is_given` | Covered |
| Declaring the existing volume's location changes nothing | `T.…test_the_production_volume_survives_its_server_toggle` (null while the server is enabled, the server's own variable otherwise) | Partial — the no-change plan is tasks.md 1.4 |
| Re-enabling the server does not replace the kept volume | `T.…test_the_production_volume_survives_its_server_toggle` (the choice turns on `var.server_enabled`, never on a module reference) | Partial — not exercised live (design.md decision 3) |

### iac-server-lifecycle (MODIFIED) — 5

| Scenario | Tests | Coverage |
|---|---|---|
| Toggle enabled creates the server | — | Uncovered: text unchanged by this delta and the behaviour is not touched by the change; `terraform/modules/server/tests/` already covers server creation; not re-derived |
| Toggle disabled creates nothing | — | Uncovered: same reason |
| Toggle disabled also removes resources coupled to the server | — | Uncovered: the scenario says it has "no subject in `main-production`" — a scenario with nothing to test. Staging's coupled volume is covered under iac-data-volumes. |
| Toggle disabled keeps the production volume | `T.TestProductionVolumeSurvivesTheServerToggle.test_the_production_volume_survives_its_server_toggle`, `…test_the_production_volume_keeps_its_address` | Partial |
| Re-enabling requires no lost configuration | `T.…test_the_production_volume_survives_its_server_toggle` (the kept volume's attachment clause, via the server reference) | Partial; the server-configuration half is unchanged and not re-derived |

### iac-host-configuration (MODIFIED) — 11

| Scenario | Tests | Coverage |
|---|---|---|
| Volume is mounted at a known path | — | Uncovered: text unchanged; existing `platform_data_volume/molecule/default` |
| Mount survives a reboot | — | Uncovered: text unchanged; existing `default` |
| Dependent subdirectories exist before a service needs them | — | Uncovered: text unchanged; existing `default`. (The new scenarios re-check nested environment entries in passing.) |
| No device is supplied and none can be discovered | — | Uncovered: text unchanged; existing `no-device-discoverable` |
| More than one candidate device is attached | — | Uncovered: text unchanged; existing `multiple-devices-*` |
| A superseded mount path is declared | — | Uncovered: text unchanged; existing `superseded-path-retired` |
| No superseded mount path is declared | — | Uncovered: text unchanged; existing `superseded-path-retired` |
| A path is declared superseded and is also the path in force | — | Uncovered: text unchanged; existing `superseded-path-in-force-refused` |
| A running service still holds the superseded path | — | Uncovered: text unchanged; existing `superseded-path-retired` |
| An application's subdirectories exist on the host it is declared for | Molecule `with-application-subdirs`; `T.TestTheApplicationsDirectoriesAreHostScoped.test_production_declares_basis_api_directories_in_its_own_host_vars`, `…test_host_scoped_entries_sit_beneath_their_application`, `…test_no_environment_wide_file_declares_an_applications_directory`, `…test_no_other_host_declares_basis_api_directories` | Covered. Ordering "after the environment's own" is not observable (see the classification table). |
| A host declaring no application subdirectories | Molecule `without-application-subdirs` | Covered (green at authoring — see failure states) |

### iac-platform-services (ADDED) — 6

| Scenario | Tests | Coverage |
|---|---|---|
| An overdue backup raises an alert | `T.TestABackedUpStoresBackupAgeIsAlertedOn.test_the_four_rules_say_what_the_requirement_says` (BackupStale), `…test_three_rules_wait_before_firing`, `…test_the_rules_are_routed_like_every_other_rule` | Partial — firing is tasks.md 7.2 |
| A timestamp without a maximum age raises an alert | same tests (BackupAgeUnbounded) | Partial |
| An unreadable metrics file raises an alert | same tests (TextfileMetricsUnreadable) | Partial |
| Two files emitting the same series raise an alert | `…test_the_four_rules_say_what_the_requirement_says` (NodeExporterGatheringErrors), `…test_the_rules_are_routed_like_every_other_rule` | Partial |
| A host with no application metrics raises nothing | `T.TestTheApplicationsDirectoriesAreHostScoped.test_every_environment_carries_the_platform_metrics_directory`; `T.…test_node_exporter_collects_the_application_metrics_directories` (the glob is `…/applications/*/metrics`, which that directory matches); Molecule `with-application-subdirs` (the platform directory is empty after converge) | Partial — that nothing fires is tasks.md 7.1 |
| Collection attaches no monitoring service to the application network | `T.…test_node_exporter_collects_the_application_metrics_directories` | Covered |

### iac-safety-hardening (MODIFIED) — 7

| Scenario | Tests | Coverage |
|---|---|---|
| A persistent store is added to the host | — | Uncovered: text unchanged. It obliges future changes and reviews, not a committed file this change edits. |
| A store's stated reason ceases to hold | — | Uncovered: same reason |
| An application asks for durable storage on this host | — | Uncovered: same reason |
| The stated divergence is not a precedent | — | Uncovered: same reason. A review obligation; no committed file expresses it. |
| A classified store moves between the host's disks | — | Uncovered: text unchanged; no store moves in this change |
| A store admitted under the fallback survives the server toggle | `T.TestProductionVolumeSurvivesTheServerToggle.test_the_production_volume_survives_its_server_toggle`, `…test_the_production_volume_keeps_its_address` | Partial |
| A store admitted under the fallback has its backups watched | — | Uncovered: the WHEN/THEN obliges the application (Basis) to publish the series before its data lands. Nothing in this repository writes them. The platform half (collection and rules) is covered under iac-platform-services. |

Count: 9 + 5 + 11 + 6 + 7 = 38 scenarios; covered (including partial) 9 + 2 + 2 + 6 + 1 = 20, uncovered 0 + 3 + 9 + 0 + 6 = 18.

## Assertion classification

- **Specified** — traces to a scenario or a SHALL in the delta:
  - production `count` reads `volume_enabled` and not `server_enabled`;
  - production `location` is null when the server is enabled, is the server module's own location variable otherwise, and turns on the toggle and never on a module reference;
  - production `server_id` references the server;
  - staging `count` reads both toggles and passes no `location`;
  - the module forwards a given `location` and a given `server_id`;
  - group_vars carry `applications/platform/metrics` root-owned, in both environments;
  - an application's directories sit in host_vars, beneath `applications/<application>/`, are in no group_vars file and in no other host's file;
  - Molecule: declared directories exist with the declared uid/gid/mode, on the mounted volume, and the platform metrics directory is empty;
  - without a host list, the volume carries exactly the environment's directories;
  - node-exporter mounts `/` read-only, mounts nothing under `/mnt/main` directly, is not on `platform_edge`, and has a textfile directory under its root mount covering `mnt/main/applications/*/metrics`;
  - the staleness and unbounded rules read both contract series and their annotations name `store` and `kind`;
  - the unreadable rule reads `node_textfile_scrape_error`;
  - the gathering rule reads `promhttp_metric_handler_errors_total`;
  - no child route diverts the four alerts.
- **Derived**, from design.md or tasks.md:
  - the exactly-one validation, the empty-location rejection, and where those failures attach (`var.server_id`, tasks.md 1.1);
  - `server_id = one(module.server[*].id)` exactly (design.md decision 3);
  - no `moved` block for `module.volume` (design.md decision 3);
  - the parents `applications` and `applications/platform` being `root:root 0755`;
  - the host entries and their `999:999`/`0700`/`0755` values (design.md decision 4);
  - the flag name `--collector.textfile.directory` (design.md decision 2);
  - the four rule names;
  - `on(store, kind)` matching in BackupStale and BackupAgeUnbounded;
  - `time()` and `>` in BackupStale; `unless` in BackupAgeUnbounded;
  - `cause="gathering"`;
  - a `for:` on three rules;
  - every document check (tasks.md 4.1 to 4.3).
- **Deliberately untested**:
  - that `server_id` or `location` is null on the resource when the module is given null — both are `Optional, Computed`, so under `mock_provider` a null input plans as unknown and the assertion cannot be evaluated;
  - every `terraform plan` outcome (tasks.md 1.4, 1.5);
  - detach and re-attach on a live host (design.md decision 3, backlog `exercise-the-volume-server-coupling-against-live-state`);
  - whether host subdirectories are created after the environment's — Ansible creates missing parents, so the final tree is identical in either order;
  - rules firing or staying silent at runtime (tasks.md 7.1, 7.2);
  - the exact `for:` values (10m/1h/15m) — presence only;
  - the alert expression's arithmetic beyond the tokens named;
  - that the root receiver delivers to Slack;
  - the role README and `defaults/main.yml` contents — Molecule `without-application-subdirs` observes the default's effect instead;
  - the `host_vars` header comment and the comments tasks.md asks for in group_vars, the stack and compose;
  - the runbook's phase-by-phase wording (phases 1, 3, 4, 11, 14, 15, 16): its headings were not read, because documents are outside this pass's read set, so only whole-file tokens are checked;
  - onboarding §4.3, for the same reason.

## Discriminators

Every static check is a function over a path or text, and each has fixture-driven discriminators in the same module (`T.TestTheStackChecksDiscriminate`, `T.TestTheInventoryChecksDiscriminate`, `T.TestThePlatformChecksDiscriminate`, `T.TestTheDocumentChecksDiscriminate`, 48 tests, all green). Each discriminator either feeds material that must be rejected and sees it rejected, or feeds a conforming fixture that must be accepted, or checks that an absent or empty target fails rather than passes. No discriminator came back negative. The Molecule `with-application-subdirs` verify discriminated on real content (red for the missing host directories, green for the present environment ones). For `without-application-subdirs` no discriminator could be run without writing role code (see failure states).

## Obsolete tests (candidates for human confirmation)

The search covered the three dispatched test-path globs only. No earlier `test-plan.md` was supplied. Both entries below are **candidates, not conclusions**, and neither is expected to fail. In each, the stated basis is superseded while the assertion probably still holds.

1. `terraform/modules/volume/tests/creation.tftest.hcl`, run `plan_requires_non_empty_server_id` (select with `terraform test -filter=tests/creation.tftest.hcl` from `terraform/modules/volume`). **Superseding delta:** MODIFIED *Volume Attached to Prod Server at Creation* — a volume may now be created with no server reference. **Evidence:** its DERIVED comment grounds it in "modules/volume never supplies `location` … so `server_id` must always be non-null whenever the volume is created", and expects it be met by `nullable = false`. Both are superseded by tasks.md 1.1, which makes `server_id` nullable. Its assertion (an empty `server_id` fails on `var.server_id`) remains consistent with tasks.md 1.1 ("rejecting an empty string for either"), and tasks.md 1.1 says to leave existing assertions unchanged. The file's header comment also describes the production stack as `count = var.volume_enabled && var.server_enabled`, which this change makes false for production.
2. `.github/tests/test_the_rebuild_runbook_records_its_rehearsal.py`, `TestWhatARebuildLosesIsStatedBeforeItIsLost.test_the_losses_are_named_before_the_step_that_destroys_the_server` (via `STORES_THAT_DO_NOT_COME_BACK = ("prometheus", "grafana")`). **Superseding delta:** MODIFIED *Conditional Prod Volume Creation* (production's volume is kept when the server toggle is off). **Evidence:** the constant is commented "the two stores whose contents a rebuild does not bring back on either stack". Design.md decision 6 says that on production's toggle route the platform's stores on the volume now survive. The check only requires the two names to appear before the destroy step, which the revised runbook will most likely still satisfy.

No test was found that asserts production's volume is destroyed with its server, or that the volume declares no location, within the searched globs. That is "none found by this search", not "none exists" — the search was bounded to the dispatched globs and keyed on `volume_enabled`, `server_enabled`, `coupl`, `location`, the retired onboarding sentence, `platform_data_volume_subdirs` and `textfile`. iac-safety-hardening's and iac-host-configuration's MODIFIED requirements supersede no behaviour that any test was found to assert: the first replaces a sentence about external managed services, and the second only adds obligations.

**Disposition (apply, 2026-10-25).** Both kept unedited and both pass: 17/17 `terraform test` runs in the module and 1692/1692 in the static suite. (1) `plan_requires_non_empty_server_id` still asserts what the module now does — an empty `server_id` fails on `var.server_id`; only its comment's reasoning and the file header's description of production's `count` are stale, and editing a test is outside this change's derivation, so they stand as history of the change that wrote them. (2) The runbook still names `prometheus` and `grafana` as lost before the destroy step, which remains true of staging and of a lost production volume; phase 1 now adds that production's toggle route keeps them.

## Unresolved project questions

1. **Which variable the module's new validations attach to.** Assumed: `var.server_id`, for both the exactly-one rule and the empty-`location` rejection. tasks.md 1.1 *replaces* server_id's validation with one covering both, and Terraform 1.9.8, which is installed here, allows cross-variable references in a validation. Dependent runs: `plan_rejects_both_server_id_and_location`, `plan_rejects_neither_server_id_nor_location`, `plan_rejects_an_empty_location`. If the implementation puts the empty-`location` check on `var.location` instead, those runs fail on the `expect_failures` target and not on behaviour. That is a derived assertion to reconsider and record, not a defect in the code.
2. **The host-scoped variable's name, `platform_data_volume_host_subdirs`.** Taken from design.md decision 4 and tasks.md 2.1; the requirement names no variable. Dependent: Molecule `with-application-subdirs` and `without-application-subdirs`; `T.TestTheApplicationsDirectoriesAreHostScoped.*`; `T.TestTheDocumentsRecordTheStore.test_the_onboarding_guide_records_the_admitted_store`.
3. **Ownership spelling in vars files.** The checks accept `root` or `0` for root, numeric strings for `999`, and a mode as a 4-digit string or a YAML integer. Dependent: the inventory tests. Another module, `test_the_shared_instance_store_moved.py`, separately reports unquoted fields; this pass imposes no quoting.
4. **The stack's server module's `location` attribute.** `test_the_production_volume_survives_its_server_toggle` compares the volume's disabled-server branch with the literal expression the stack passes to `module "server"`'s `location` (expected `var.location`). The stack file was not read, as it is implementation.
**Resolved at apply:** (1) both validations attach to `var.server_id` — Terraform requires a cross-variable condition to name the variable it sits on, so the empty-`location` check is folded into the exactly-one rule there; (2) the name is `platform_data_volume_host_subdirs`; (3) inventory spells root as `root` and numbers and modes as quoted strings; (4) the server module takes `location = var.location`, and the volume's disabled branch passes the same variable.

5. **Stack-skill coverage.** The library carries `terraform`, `ansible` and `python` skills; all three were loaded. No unresolved question arises from a missing skill.

## Missing shared arrangement

Dispatch and AGENTS.md ("Testing") both state there is no shared test arrangement in any of the three suites, so no proposed home exists for any entry below; per AGENTS.md, `apply` keeps each local with that reason. `docs/backlog.md` `share-the-static-suites-test-arrangement` is the change that would give the static suite one. No near-miss exists, there being nothing shared to miss.

All entries below are declared in `.github/tests/test_basis_api_durable_store.py` unless stated.

| Declared | Stands in for | Used by | Found in another test module |
|---|---|---|---|
| `ROOT`, `read_required` | repository root; reading a committed file that must exist | every `T.*` test reading the tree | `test_ci_configuration.py` (`ROOT`, `read_text`); `test_a_shared_instance_reset_is_visible.py` (`_read`) |
| `_VaultTolerantLoader`, `load_vars` | parsing inventory vars files that carry `!vault` tags | `T.TestTheApplicationsDirectoriesAreHostScoped.*`, `T.TestTheInventoryChecksDiscriminate.*` | `test_a_shared_instance_reset_is_visible.py` (`load_tolerant_yaml`), used by `test_the_shared_instance_store_moved.py` |
| `_strip_hcl_comments`, `hcl_block`, `hcl_blocks_of_kind`, `top_level_attributes`, `stack_module_attributes`, `location_by_server_toggle` | reading a Terraform stack's module arguments without a Terraform binary | `T.TestProductionVolumeSurvivesTheServerToggle.*`, `T.TestTheStackChecksDiscriminate.*` | not found in another module (none was searched beyond the ones read) |
| `compose_document`, `node_exporter_service`, `service_command`, `service_mounts`, `service_networks` | reading `platform/docker-compose.yml`'s services and their mounts | `T.TestABackedUpStoresBackupAgeIsAlertedOn.test_node_exporter_collects_the_application_metrics_directories`, `T.TestThePlatformChecksDiscriminate.*` | `test_ci_configuration.py` (`compose_services`, `normalised_mount`) |
| `config_content`, `alerting_rules`, `_expr`, `_word`, `_matching_labels`, `annotations_name_store_and_kind` | reading the stack's inline `prometheus_rules` and `alertmanager_config` | `T.TestABackedUpStoresBackupAgeIsAlertedOn.*`, `T.TestThePlatformChecksDiscriminate.*` | `test_ci_configuration.py` (`stack_configs`, `config_content`); `test_certificate_expiry_alerting.py` (`rules_document`, `alerting_rules`, `child_routes`, `declared_receivers`) |
| Molecule `prepare.yml` loop-device fixture, at offsets 7 and 8, in `with-application-subdirs/prepare.yml` and `without-application-subdirs/prepare.yml` | an attached Hetzner Volume block device | Molecule `with-application-subdirs`, `without-application-subdirs` | copied from `platform_data_volume/molecule/default/prepare.yml` (a sibling scenario, not a shared arrangement); the Molecule suite has no shared fixture to take it from |

**Disposition (apply, 2026-10-25): every entry kept local.** This project records no shared test arrangement in any suite (AGENTS.md, "Testing"), and creating one is a testing-strategy decision outside this change; `share-the-static-suites-test-arrangement` is where the static suite's would come from.
