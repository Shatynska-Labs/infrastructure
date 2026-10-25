## 1. Terraform: production's volume survives its server toggle

- [ ] 1.1 `terraform/modules/volume/`: add an optional `location` (default `null`); make `server_id` nullable with default `null`; replace its non-empty validation with one requiring exactly one of `server_id` and `location` to be non-null, and rejecting an empty string for either. Pass both to `hcloud_volume.this` as given (`design.md` decision 3). Rewrite the comment above the resource and the variables' descriptions to say why both exist. Leave the existing `tests/*.tftest.hcl` assertions unchanged.
- [ ] 1.2 `terraform/stacks/main-production/main.tf`: `count = var.volume_enabled ? 1 : 0`; pass `location = var.server_enabled ? null : var.location`; keep `server_id = one(module.server[*].id)`. Rewrite the comment above the module, saying why the choice turns on `server_enabled` rather than on `server_id`; update `volume_enabled`'s and `server_enabled`'s descriptions in `variables.tf` and `volume_id`'s in `outputs.tf`. `main-staging` is not edited.
- [ ] 1.3 `terraform fmt -check -recursive`, `terraform validate` in both stacks and the module, `tflint`, and `terraform test` in `terraform/modules/volume/`.
- [ ] 1.4 Read the pull request's production plan: it SHALL show no change to any resource. A planned replacement or destruction of `module.volume[0].hcloud_volume.this` stops the change.
- [ ] 1.5 Open a plan-only pull request from a throwaway branch setting `main-production`'s `server_enabled = false`; its plan SHALL destroy the server and firewall and leave the volume unchanged. Record the plan summary here and close the pull request unmerged.

## 2. Ansible: the application's directories on production's volume

- [ ] 2.1 `ansible/roles/platform_data_volume/`: add `platform_data_volume_host_subdirs: []` to `defaults/main.yml` and create its entries in the subdirectory task after `platform_data_volume_subdirs`'s (same shape, same task position after the mount). Update the role's README.
- [ ] 2.2 `ansible/inventory/group_vars/production.yml` and `staging.yml`: append `applications`, `applications/platform` and `applications/platform/metrics` (`root:root 0755`) to `platform_data_volume_subdirs`, with a comment on why the glob must always match. `ansible/inventory/host_vars/main-production.yml`: declare `applications/basis-api` (`root:root 0755`), `applications/basis-api/postgres` (`999:999 0700`) and `applications/basis-api/metrics` (`999:999 0755`), with a comment naming the application, the store's admission under *No Store on This Host Holds Data Requiring Backup*, and why `999` (Debian-based image; Alpine would be `70`). Update the file's header, which lists the volume subdirectories among what stays in `group_vars`, to say an application's subdirectories live here.
- [ ] 2.3 Run the role's Molecule suite through `ansible/scripts/run-molecule test --all` and confirm `verify: Executed: Successful` for every scenario in DETAILS; run `ansible-lint` and the syntax check.

## 3. Platform: backup-age alerts

- [ ] 3.1 `platform/docker-compose.yml`: add `--collector.textfile.directory=/host/root/mnt/main/applications/*/metrics` to node-exporter's `command`, with a comment on why no new mount or network is needed.
- [ ] 3.2 Add the rules `BackupStale`, `BackupAgeUnbounded`, `TextfileMetricsUnreadable` and `NodeExporterGatheringErrors` to `prometheus_rules`, as `design.md` decision 2 states them, each with a summary and description naming `store` and `kind` where the series carry them. Document the metric contract, including atomic `0644` files, beside the rules.
- [ ] 3.3 Run the `.github/tests` suite and `docker compose -f platform/docker-compose.yml config` with the stack's placeholder environment.

## 4. Documents

- [ ] 4.1 `docs/onboard-an-application.md` §3.1: replace "no application has cleared that bar" with the admitted store, the two further obligations (a volume surviving the toggle, a watched backup age), and how an application declares its directories and publishes its backup metrics (atomic, world-readable files, consistent or absent `# HELP`/`# TYPE` lines). §4.3 names the two obligations for any store admitted under the fallback, relational or not, and points to §3.1.
- [ ] 4.2 `docs/runbook-rebuild.md` phases 1, 3, 4, 11, 14 and 16: in phase 1, that on production no volume store comes back empty on the toggle route, that a lost volume means a restore of `basis-api`'s store from Basis's backups, performed in Basis's repository, and that `BackupStale` joins the expected alarms; in phases 11, 14 and 16, that on production's toggle route the shared instance, its roles and its databases survive, so `pgexporter` is not recreated, no password is rotated and data is not expected empty; in phase 15, that on production after a lost volume `basis-api`'s store is restored from Basis's backups, in Basis's repository, before its deploy; in phases 3 and 4, state that production's toggle route keeps the volume — two destroys in the plan, not three; the same volume id afterwards; the platform's stores and `basis-api`'s survive — and that the staging rehearsal recorded there is unchanged.
- [ ] 4.3 `docs/backlog.md`: add `finish-basis-api-s-move-to-its-own-database` (retire production's shared-instance `basis-api` database, role and probe key; declare `basis-api`'s backups expected so that their absence alerts), waiting on Basis's `move-to-durable-data-storage`, and on Basis stating that its production relational data has no non-durable table (*Single Shared PostgreSQL Instance, Per-Application Databases*).

## 5. Verify

- [ ] 5.1 `openspec validate --all --strict`.
- [ ] 5.2 `python3 -m unittest discover --start-directory .github/tests` from the repository root.
- [ ] 5.3 `pre-commit run --all-files` with the Galaxy role installed in this working tree.

## 6. Ship

- [ ] 6.1 Open the pull request; let CI run; read the production plan comment against 1.4.
- [ ] 6.2 The operator merges, approves production's apply (expected no-op) and production's converge — before the platform deploy or within 15 minutes of it (`design.md` Migration Plan) — and confirms the platform deploy is healthy on both hosts.

## 7. Confirm the effect

- [ ] 7.1 On `main-production`: `ls -ldn /mnt/main/applications/basis-api/{postgres,metrics}` shows `999 999` with modes `0700` and `0755`; on both hosts `/mnt/main/applications/platform/metrics` exists, empty and root-owned; on `main-staging`, `/mnt/main/applications/basis-api` does not exist; neither host has `TextfileMetricsUnreadable` firing, and `node_textfile_scrape_error` reads `0` on both.
- [ ] 7.2 On `main-production`, as `999`, write `/mnt/main/applications/basis-api/metrics/confirm.prom` the way the contract requires — `mktemp` in that directory, `chmod 0644`, `mv` — with `backup_last_success_timestamp_seconds{store="confirm",kind="test"}` two hours old and `backup_max_age_seconds{store="confirm",kind="test"} 3600`; `BackupStale` reaches Slack naming `confirm`/`test`. Remove the max-age line; `BackupAgeUnbounded` fires. Delete the file; both resolve. Then write two files carrying the same series; `NodeExporterGatheringErrors` fires. Delete both; it resolves after its window. Then write a `0600` `.prom` file; `node_textfile_scrape_error` reads `1` and `TextfileMetricsUnreadable` reaches Slack after 15 minutes. Delete it; it resolves.
- [ ] 7.3 Tell Basis's `move-to-durable-data-storage` that this change is in place.

## 8. Archive

- [ ] 8.1 Bring the branch back to the freshly fetched trunk; update `docs/backlog.md`: `decide-whether-the-data-volume-should-survive-a-server-toggle` narrows to staging, `alert-on-a-scheduled-units-own-output` and `notice-a-pending-reboot-and-decide-what-does-it` note that the textfile collector is enabled (over application directories only), `exercise-the-volume-server-coupling-against-live-state`'s production half rewritten to the toggle that keeps the volume (citing 1.5's plan), `announce-a-rebuild-to-the-applications-that-hold-databases` and `probe` references re-checked; commit the record and open its own pull request.
