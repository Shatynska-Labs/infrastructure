# Backlog

Changes this project has identified and not yet archived. Each entry is a change recorded here instead of being folded into the change that found it, or opened on a branch of its own.

An entry's heading is the change's name in kebab-case — the name its branch and change directory are expected to take, though the session that opens the change may rename it if the work turns out different. A fix takes the name as its branch's only. Refer to an entry only by that name.

The order of entries carries no meaning. What an entry waits on, and which entries share a design with it, it states in its own fields.

Keep an entry short: what is needed and why, naming files, specifications and changes as pointers. Leave out line numbers, census tables and step-by-step plans; they go stale first, and the session that takes the entry up redoes them.

Delete an entry when its change is archived, when the operator takes it as a fix rather than a change, when a change makes it obsolete, or when the operator decides the change will not be made. When a change is archived, also update the entries it unblocked or made stale, and set their **Re-checked** date. Keep this file when it has no entries.

An entry takes this shape:

```
## `change-name`

What the change is and why it is needed, written for a session that has not seen the work that found it.

**Kind**: `fix` or `change`, and why. A fix owes no specification delta, needs no decision from the operator, and fits one review sitting; anything else is a change, and says which delta it owes, which decision it needs, or that it is too large.

**Waits on**: `nothing`, or something that can be checked: a change by name, a person's answer, an event.

**Design with**: the entries that share a design with this one, by name, or `nothing`.

**Recorded by**: the change that identified it, and why it was not done there.

**Re-checked**: the date the entry was last verified against the repository.
```

## `close-public-ssh-and-manage-sshd-explicitly`

Port 22 is open on the cloud firewall and in UFW to one ISP `/24` (`ssh_allowed_cidrs` in each stack's `terraform.tfvars`, mirrored as `hardening_ssh_allowed_cidrs` in `group_vars`). Every non-operator path, `host-converge.yml` included, already reaches hosts over the tailnet, which `ansible/roles/hardening/tasks/main.yml` admits independently from `100.64.0.0/10` (that task's own comment calls an empty public list "safer than what prod runs"), so the public rule serves only the operator, who is on the tailnet too. Closing it means `ssh_allowed_cidrs = []`, which `terraform/modules/server/variables.tf` refuses on lockout grounds; that validation is what to revisit. The Terraform and UFW rules move together (*Host-Level Security Owned by Ansible, Cloud Firewall Owned by Terraform*), and the recovery path when the tailnet is unreachable is Hetzner's console, which the cloud firewall does not gate.

Must not break: the public address is the only path for a host's *first* converge (`docs/bootstrap-a-new-host.md` §6.3, `docs/runbook-rebuild.md`'s converge phase), since that play is what joins the tailnet. The change must say how a new or rebuilt host is bootstrapped afterwards (a temporarily widened `ssh_allowed_cidrs` through the pipeline, or the console). It must not precede a converge pipeline seen to work over more than one production run; the ISP `/24` is the fallback for a converge that wedges `tailscaled`.

Also here: `sshd_config` (no drop-in under `/etc/ssh/sshd_config.d/`; `PasswordAuthentication` unset, harmless only because no account has a password) runs on the image's defaults although `iac-host-configuration` assigns SSH hardening to Ansible. It belongs to `hardening` and can be asserted by its Molecule scenario. The `unattended-upgrades` reboot half is `notice-a-pending-reboot-and-decide-what-does-it`.

**Kind**: `change`. It needs the operator's policy decision to close public SSH and to choose the bootstrap path, and owes deltas to the server module's lockout validation and to `hardening`'s managed `sshd_config` (`iac-host-configuration`).

**Waits on**: `nothing`. It used to wait on the host converge moving into the pipeline, which `apply-host-configuration-through-a-gated-workflow` delivered.

**Design with**: `notice-a-pending-reboot-and-decide-what-does-it`.

**Recorded by**: `unknown`; the entry predates the tailnet-based converge and was kept as a policy decision the `hardening` role anticipates.

**Re-checked**: 2026-10-19.

## `notice-a-pending-reboot-and-decide-what-does-it`

Both hosts carried `/var/run/reboot-required` (kernel, `linux-base`, `libc6`) from 2026-09-10 to 2026-09-16 with nothing reporting it, until rebooted by hand. `unattended-upgrades` is installed and enabled by the image, not by `hardening`, and every `Automatic-Reboot` line is commented out, so patches install and do not take effect for an unbounded time while the host looks healthy.

It is two changes under one name. *Noticing* is a metric and an alert: node-exporter's textfile collector is not enabled (`platform/docker-compose.yml`'s `node-exporter` has no `--collector.textfile.directory` and no mount), so it needs a `platform/` change for the collector and rule plus an `ansible/` unit that writes the metric, through two pipelines. *Deciding what reboots* is a `hardening` change: an `Automatic-Reboot` policy with a window, or a stated operator ritual. Rebooting is known-safe: both hosts rebooted cleanly on 2026-09-16 in about forty seconds (containers back on `restart: unless-stopped`, `/mnt/main` mounted before Docker, including production's first boot with the shared database on that volume; swap, `ufw`, `tailscaled` up). A reboot is an outage of every application on the host, so an automatic production policy is a scheduled outage; `hold-every-platform-deploy-for-the-length-of-a-window` is what would keep a deploy out of it.

**Kind**: `change`. It needs the operator's reboot-policy decision, spans two pipelines, and owes deltas to `iac-host-configuration` (unattended updates owned by `hardening`) and `iac-platform-services` (the collector and alert).

**Waits on**: `nothing`.

**Design with**: `alert-on-a-scheduled-units-own-output` (the same unenabled textfile collector: flag, directory, ownership and mount are built once for both), `close-public-ssh-and-manage-sshd-explicitly` (the other half of the image-default `hardening` gap).

**Recorded by**: the operator and a session on 2026-09-16, from the hosts after rebooting them by hand; not by a change.

**Re-checked**: 2026-10-19.

## `manage-root-authorized-keys-from-a-role`

No role manages `root`'s `authorized_keys`: its first entry comes from Hetzner at server creation (`hcloud_server.ssh_keys` cannot change without recreating the server), and each stack's `ansible-ci` converge key is appended by hand at `docs/bootstrap-a-new-host.md` §6.6. Revoking the most powerful credential CI holds is therefore an edit on the host rather than a commit.

A role owning that file can lock every operator out, a different class of risk from anything `hardening` does, so it wants scenarios of its own. Follow `ops_user`'s per-entry `state:` model (revocation is `state: absent`, entry left in place until a converge removes it). Only `exclusive: true` actually revokes, and that is the form that can lock everyone out. The first installation stays manual whatever the shape; the change buys every one after.

**Kind**: `change`. It owes an `iac-host-configuration` requirement for a role owning `root`'s keys, and carries lockout risk too large for a fold-in.

**Waits on**: `nothing`.

**Design with**: `revoke-an-application-s-deploy-authorisation` (same revocation shape and `exclusive` trade-off).

**Recorded by**: `apply-host-configuration-through-a-gated-workflow`, which installs the converge key and cannot revoke it; not done there because of the lockout risk.

**Re-checked**: 2026-10-19.

## `revoke-an-application-s-deploy-authorisation`

`deploy_user` renders, per `deploy_apps` entry, `/opt/<name>`, `/etc/sudoers.d/app-deploy-<name>`, `/etc/sudoers.d/app-probe-<name>` and two `authorized_keys` lines (deploy and probe keys, each with a forced command), and removes none of them when the entry is deleted. `authorized_key` leaves `exclusive` at its default deliberately, so no application's entry disturbs another's. So deleting an entry leaves the host authorising that key as before; revocation is an edit on the host or a key rotation in the application's repository, neither of which a converge notices.

Follow `ops_user`'s per-entry `state:` model (`state: absent`, entry left in place until a converge has removed it); only `exclusive: true` actually revokes, and it can lock everyone out. `remove-commerce-ops-from-staging` needed this once (2026-10-18) and cleaned the host by hand instead (its `design.md` Decision 1), judging one revocation on one host not worth the mechanism; `remove-commerce-ops-from-production` needed it again (2026-10-19) and made the same judgement (its `design.md` Decision 1).

**Kind**: `change`. It owes a delta to *Restricted Deploy Account Supports Per-Application Forced-Command Deploys* (`iac-host-configuration`) for revocation, and needs the `exclusive`-versus-per-entry decision.

**Waits on**: `nothing`.

**Design with**: `manage-root-authorized-keys-from-a-role`.

**Recorded by**: `onboard-commerce-ops-to-staging` (2026-09-13), which found nothing takes a `deploy_apps` entry back while stating what reverting it would cost; out of an onboarding change's scope.

**Re-checked**: 2026-10-19.

## `say-what-the-host-firewall-actually-gates`

A container-published port is not filtered by UFW on any interface: Docker DNATs it in `nat/PREROUTING` and accepts it in `FORWARD`, and UFW's rules hang off `INPUT`. So `hardening_web_allowed_cidrs` gates nothing for Traefik's `80`/`443` (published on all addresses), and the Hetzner cloud firewall alone refuses public traffic (measured on staging 2026-09-13 with UFW active and both CIDR lists empty: 301 and 404 over the tailnet). Nothing in `ansible/roles/` touches `DOCKER-USER` or `after.rules`.

This falsifies the two-layer statement where it is still made unqualified: `AGENTS.md`'s *Firewall split*, the requirement *Host-Level Security Owned by Ansible, Cloud Firewall Owned by Terraform* ("exactly one layer SHALL be the documented access gate"), and `ansible/roles/hardening/README.md` (its sync and *Tailnet-scoped rules* sections). Each must say which ports it is true of. `docs/bootstrap-a-new-host.md`, `docs/onboard-an-application.md` and `check-public-endpoints-from-outside` already say it correctly. The `terraform.tfvars`/`group_vars` mirror obligation still holds for every port UFW does gate.

Settle first: `add-grafana-tailnet-ufw-rule` (archived) added a UFW allow for 3000 because Grafana was unreachable from the tailnet, and `hardening/README.md` still says that rule "is what actually lets tailnet peers reach it", yet Grafana is a container-published port (`${GRAFANA_BIND_ADDRESS}:3000`), which UFW should never filter. Either that diagnosis was wrong or something distinguishes the case. This is a documentation defect, not an exposure; whether to close container ports at the host layer too (`DOCKER-USER`, or publishing to `127.0.0.1`) is a separate change this one does not prejudge.

**Kind**: `change`. It owes an `iac-host-configuration` delta to *Host-Level Security Owned by Ansible, Cloud Firewall Owned by Terraform* saying which layer gates a container-published port, and an investigation of the Grafana case before the rule is written.

**Waits on**: `nothing`.

**Design with**: `put-the-remaining-host-scoped-variables-on-the-host-axis` (its firewall-pair decision depends on which ports UFW gates).

**Recorded by**: `onboard-commerce-ops-to-staging`, whose code review probed the host and caught documents asserting the opposite; that change corrected only `group_vars/staging.yml`'s comment, which it was already editing.

**Re-checked**: 2026-10-19.

## `put-the-remaining-host-scoped-variables-on-the-host-axis`

*A Host-Scoped Variable Lives in the Host's Own Vars File* (`openspec/specs/iac-host-configuration/spec.md`) names three placements it is to be read as unmet in, and this entry resolves them with it: `hardening_ssh_allowed_cidrs` and `hardening_web_allowed_cidrs` (they mirror one stack's `terraform.tfvars`, so are per stack by nature) and `ops_user_accounts` (a root-equivalent login; an operator of one tenant's host is not thereby one of another's). The requirement's paragraph is replaced when those move, not before.

Each needs a decision: for the firewall pair, whether per-stack CIDRs defeat an environment-wide hardening baseline (settle `say-what-the-host-firewall-actually-gates` first); for the accounts, whether host access is per environment or per tenant. An audit of the rest of both `group_vars` files against the requirement's test is part of the entry; `ghcr_pull_token`/`ghcr_pull_username` come first, since two tenants' GHCR organisations differ. The mechanism (`ansible/inventory/host_vars/<server name>.yml`) already exists and takes precedence.

Ride-along: `.github/workflows/host-converge.yml` checks that a stack's `group_vars` file exists but not its host vars file, so a `workflow_dispatch` run lacks the guard a pull request gets from `.github/tests`. Add the host-vars half beside the existing group-vars check; it completes a pair, it does not restate a role's contract.

**Kind**: `change`. It needs the operator's per-environment-or-per-tenant decisions and owes an `iac-host-configuration` delta to the requirement's unmet paragraph.

**Waits on**: `nothing`.

**Design with**: `say-what-the-host-firewall-actually-gates`.

**Recorded by**: `bound-a-deploy-key-to-one-host-when-an-environment-holds-two-stacks`, which moved `deploy_apps` to host vars and left these deliberately because each needs a decision it did not make; it also declined the dispatch-path check on cost.

**Re-checked**: 2026-10-19.

## `narrow-the-converge-trigger-to-what-a-converge-reads`

`host-converge.yml` triggers on any merge touching `ansible/**`, so comment-only and test-fixture changes converge both hosts (`changed=0`), three times observed: PR #148 (2026-09-12), PR #161 (2026-09-13, Molecule fixtures only, which held a production approval open 6h34m), and PR #210 (2026-09-15, a comment-only `requirements.yml`/`requirements.txt` diff). A converge changes the firewall, logins and container runtime; relying on idempotency is weaker than not running.

It is not a copy of `narrow-the-molecule-trigger-to-what-it-reads`: the exclusion sets are near inverses. A converge reads the inventory, `group_vars`, `host_vars`, the playbooks and every role's `tasks/`, `defaults/`, `handlers/`, `templates/`, `meta/`, so all of those stay. The safe exclusions are roughly documentation (`**/README.md`), `.envrc*`, and Molecule scenario directories plus `ansible/scripts/run-molecule`.

Must not: let a host silently not converge. Getting this filter wrong reports green while a host keeps its old firewall. Keep the exclusion list conservative, use the `some-with-excludes` discipline `ansible-verify.yml` documents, and add a `.github/tests` assertion that every path a converge reads is not excluded. A reviewer may legitimately keep the coarse trigger because the failure mode is silent.

**Kind**: `change`. It owes an `iac-cicd-pipeline` delta for the converge trigger and needs a decision that narrowing is worth the silent-failure risk.

**Waits on**: `nothing`.

**Design with**: `nothing`.

**Recorded by**: the session that merged `rename-terraform-environments-to-stacks` (PR #148) on 2026-09-12; outside that change's subject.

**Re-checked**: 2026-10-19.

## `make-the-converge-survive-a-galaxy-outage`

The Galaxy install (`ansible-galaxy collection install` then `role install`, from `ansible/requirements.yml`) runs with no retry, cache or fallback in `host-converge.yml`, `ansible-verify.yml` and `pr-validation.yml`. It failed transiently twice on 2026-09-12: a production converge after PR #155 (a cache-shaped "Missing expected 'results'" error) and a Molecule job on PR #161 (connection reset fetching `hetzner.hcloud`). Neighbouring identical installs passed and re-runs went green. On the gated production path the cost is a spent approval and a host left unconverged.

Must not: a blind retry would hide a genuine pin failure. `ansible/requirements.yml` pins exact versions, so "could not reach the server" must be distinguished from "this version does not exist", and only the first retried. Options in rising cost: bounded retry with backoff; `--no-cache`/`--clear-response-cache`; caching resolved collections between runs (interacts with pinning); vendoring the collections. The fix belongs to every workflow that installs Galaxy content.

**Kind**: `change`. It needs a decision among the options and spans three workflows.

**Waits on**: `nothing`.

**Design with**: `nothing`.

**Recorded by**: the session that merged `rename-the-external-services` (PR #155), whose gated production converge failed on it; outside that change's subject.

**Re-checked**: 2026-10-19.

## `detect-host-drift-on-a-schedule`

Nothing reports what a host has drifted to between converges; the host layer is the only one without that (`drift.yml` sweeps Terraform nightly; the platform stack is redeployed on every merge). A scheduled `--check --diff` against each host is the host layer's `drift.yml`. It cannot live in the converge workflow, since a pre-approval job must hold no credential that reaches a host and check mode must authenticate.

It cannot ship on today's baseline: the `tailscale` role's two `get_url` tasks (*Add the Tailscale apt signing key*, *Add the Tailscale apt repository*) have no `checksum:` and report changed under `--check` forever, so a healthy host reads `changed=2`. Remedies: pin a checksum (upstream rotates the key), replace `get_url` with something check-mode-verifiable, or filter those two by name with the reason stated. Check mode also skips `command` tasks (`ops_user`, `swap`) and `geerlingguy.docker` ignores errors in check mode, so a clean check speaks for files and packages, not the host; the report must say so where it reports. `docs/bootstrap-a-new-host.md` §6.3 states the `changed=2` baseline and changes when this lands.

Shape it as `drift.yml`'s sibling: scheduled, per environment, one deduplicated issue per environment, and a liveness report (*Scheduled Workflows Report Their Own Liveness*).

**Kind**: `change`. It adds a scheduled workflow owing an `iac-cicd-pipeline` delta and needs a decision on the `get_url` remedy.

**Waits on**: `report-an-absent-tailscale-auth-key`, which brings the `tailscale` role its first Molecule scenario; checkable as `ansible/roles/tailscale/molecule/` existing.

**Design with**: `nothing`.

**Recorded by**: `apply-host-configuration-through-a-gated-workflow` (its `design.md` Decision 10), which made it possible and declined it because a check-mode run needs a host credential the pre-approval job must not hold.

**Re-checked**: 2026-10-19.

## `report-an-absent-tailscale-auth-key`

*A Role's Absent Required Input Is Reported by Name* (`iac-host-configuration`) is scoped to inputs consumed on every run; `tailscale_auth_key` is the excluded class. It is consumed only by *Bring the host onto the tailnet*, under a `when:` that skips an already-joined host, so an unconditional assertion would break every re-converge.

The diagnostic must fire under the same four-limb condition as the join, stated once; reading its `POLARITY` comment wrong silently stops a host joining the tailnet, which the deploy pipeline depends on. The consuming task's `no_log: true` censors an absent key into a redacted error. `host-converge.yml` passes `tailscale_auth_key=''` on every converge by design, so "undefined" and "empty" differ: firing on undefined never fires for the pipeline, and firing on empty fires on every pipeline converge. The trigger is the join condition itself. The role has no Molecule scenario; this change brings its first.

**Kind**: `change`. It owes a delta to *A Role's Absent Required Input Is Reported by Name* for a conditionally consumed input, and needs the absent-versus-empty decision.

**Waits on**: `nothing`.

**Design with**: `nothing`.

**Recorded by**: `fix-volume-discovery-and-consistency` (its `design.md` Decision 3a), whose requirement deliberately excluded conditionally consumed inputs.

**Re-checked**: 2026-10-19.

## `collect-each-role-s-apt-installs-into-one-task`

`hardening` installs `ufw` and `fail2ban` as two `apt` tasks where `ansible.builtin.apt` takes a list. Collapsing them reaches the case `cache-the-apt-index-within-a-converge`'s staleness bound does not: a production host with a maintained `update-success-stamp`, where `cache.update()` never advances what `get_cache_mtime()` reads, so every bounded task fetches again. It saves little in CI, where the first fetch is owed either way.

It moves things readers depend on: which task a failure surfaces under, what the scenarios assert (they observe `ufw` and `fail2ban` separately), and the install-then-configure ordering. Measure the production saving before proposing it.

**Kind**: `change`. It needs a measured decision that the production saving justifies changing two roles' task structure and their scenario assertions.

**Waits on**: `nothing`.

**Design with**: `nothing`.

**Recorded by**: `cache-the-apt-index-within-a-converge` (its Non-Goals); a larger refactor of two roles than that bound.

**Re-checked**: 2026-10-19.

## `reclaim-a-multiply-referenced-untagged-image`

An untagged image with more than one repository reference (pulled by digest from a registry and its mirror) cannot be removed by identity unforced: the runtime refuses with "referenced in multiple repositories", so the host prune (`ansible/roles/image_prune`) offers and refuses it every run, now counted under `refused` and pointed here from the role's README.

Must not: force removal; *Unreferenced Host Images Are Pruned on a Schedule* forbids it because the unforced refusal backstops a defective keep set. The likely shape is removing through each repository reference in turn, as tags are, but that makes a digest reference something the run drops and has no counterpart to the pre-removal re-check that guards a re-pointed tag. Neither host is known to carry such an image.

**Kind**: `change`. It changes what the run removes, owing a delta to *Unreferenced Host Images Are Pruned on a Schedule*.

**Waits on**: `nothing`.

**Design with**: `nothing`.

**Recorded by**: `report-refused-removals-in-the-host-prune`, which made the condition visible; changing removal was outside a reporting change.

**Re-checked**: 2026-10-19.

## `size-platform-container-resource-limits`

No service in `platform/docker-compose.yml` declares a memory or CPU limit on a `cx33`, so one container can starve the host; `ContainerRestartingOrOOMKilled` only alerts on the consequence. Size limits from observed steady state and peak (`container_memory_usage_bytes`, on the "Container health" dashboard), not by guess: limits picked without evidence cause the outage they were meant to prevent.

**Kind**: `change`. It needs sizing decisions from measured data across every platform service.

**Waits on**: `nothing`. It waited on data; metrics have accumulated on production since `add-platform-monitoring` (2026-09-04). Staging was rebuilt on 2026-10-18, so its history is short.

**Design with**: `nothing`.

**Recorded by**: `unknown`.

**Re-checked**: 2026-10-19.

## `alert-on-swap-utilisation`

Nothing alerts when swap is being consumed, the sign that a leak is underway and the OOM killer is next. `HostMemoryPressure` reads `MemAvailable / MemTotal` (RAM only), so it still fires on a leak but cannot say the last-resort tier is draining. `node_memory_SwapFree_bytes` and `node_memory_SwapTotal_bytes` are already scraped, so the rule sits beside the others in `platform/docker-compose.yml`'s inline `prometheus_rules`. Decide level (fraction used) versus rate (consumed per unit time); with no history, pick the simpler and revisit.

**Kind**: `change`. It needs a threshold decision and owes an `iac-platform-services` alerting delta.

**Waits on**: `size-platform-container-resource-limits`; container limits change what swap absorbs, so a threshold chosen first describes a host about to change.

**Design with**: `nothing`.

**Recorded by**: `bound-host-log-growth-and-add-swap`, which added swap; this is a `platform/` change on a different pipeline, so folding it in would have needed two deploys.

**Re-checked**: 2026-10-19.

## `alert-on-the-exporter-being-unable-to-read-postgres`

`MetricsTargetDown` (`up == 0`) cannot catch postgres-exporter failing to reach the database: the exporter answers `/metrics` 200 with `pg_up 0`, and its healthcheck passes (measured against the pinned `v0.20.1`). On 2026-09-15 both hosts were found at `pg_up 0` for an unknown period (a `#` in the password broke `DATA_SOURCE_NAME`, since fixed) with nothing reporting it. The `pgexporter` role is recreated by hand after any store reset or rebuild, the step most likely to go wrong; `platform/README.md` tells the operator to check it by hand until this lands.

Owed: an alert on `pg_up == 0` for the `postgres-exporter` job in the inline `prometheus_rules` config (not `prometheus_config`, where a `groups:` block is not read), with a `for:` that rides out an instance restart, and the `platform.config-checksum` label regenerated or nothing deploys. The wider question is whether each exporter needs its own liveness signal rather than one alert per incident.

**Kind**: `change`. The rule is one line, but it needs the per-exporter liveness decision and owes an `iac-platform-services` alerting delta.

**Waits on**: `nothing`.

**Design with**: `nothing`.

**Recorded by**: `unknown` change; found 2026-09-15 while writing `platform/README.md`'s *Upgrading the PostgreSQL major version*, and kept open for the wider exporter question.

**Re-checked**: 2026-10-19.

## `alert-on-a-scheduled-units-own-output`

`prune-host-images` writes its outcome to the journal and nothing reads it. The dead-man's switch covers the unit not running, not what a successful run reported, so a prune that refuses the same image weekly, or whose `considered` count collapses, is green. The sharpest case: a runtime that stops responding mid-loop leaves the prune reporting every remaining candidate refused and still exiting zero, so the heartbeat goes green on a half-done run (signature in `ansible/roles/image_prune/README.md`, which cites this entry).

Mechanism: node-exporter's textfile collector, with rules in the inline `prometheus_rules`. The collector is not enabled (no `--collector.textfile.directory`, no mount), and the first entry taken pays for the flag, directory, ownership and mount. Decide whether the prune script writes the textfile (making metrics part of a script governed by *A Run That Cannot Determine the Keep Set Completely Removes Nothing*) or a wrapper does (a second thing that can silently stop). Shape it for every scheduled host unit, not the prune alone.

**Kind**: `change`. It needs the script-or-wrapper decision, spans a role, a collector directory and alert rules, and owes deltas to `iac-host-configuration` and `iac-platform-services`.

**Waits on**: `nothing`.

**Design with**: `notice-a-pending-reboot-and-decide-what-does-it`.

**Recorded by**: `report-refused-removals-in-the-host-prune`, which found `image_prune`'s README already citing this deferral without a record; out of a reporting change's scope.

**Re-checked**: 2026-10-19.

## `label-each-stack-s-alerts-with-the-stack-they-came-from`

Prometheus in `platform/docker-compose.yml` declares no `external_labels`, and Alertmanager routes group on labels that name no host or stack, so staging's and production's alerts are identical text. Attribution currently comes from each stack's own `PLATFORM_SLACK_WEBHOOK_URL` and `PLATFORM_DEADMANSWITCH_URL` (`docs/bootstrap-a-new-host.md` §7.3), which nothing enforces: paste one stack's webhook into the other's Environment and alerts merge silently, and `.github/tests` cannot read repository settings.

The fix is `external_labels` under Prometheus's `global:`, its value rendered at deploy time, and a regenerated `platform.config-checksum`. Settle: stack (`main-staging`) or environment (`staging`), which are different axes; whether to derive it from `PLATFORM_DEPLOY_HOST` rather than add a secret; and whether Alertmanager routes group on it.

**Kind**: `change`. It needs the stack-or-environment decision and owes an `iac-platform-deploy-pipeline` delta for the new rendered value.

**Waits on**: `nothing`.

**Design with**: `nothing`.

**Recorded by**: `deploy-the-platform-stack-per-environment`, which put the stack on a second host; parameterising the Compose file was its declared Non-Goal.

**Re-checked**: 2026-10-19.

## `quieten-the-certificate-expiry-guard-on-a-host-serving-nothing`

`CertificateExpiryNotObserved` (`absent(traefik_tls_certs_not_after{cn!=""}) or count(...{cn=""}) > 0`, from `alert-on-certificate-expiry`) fires on any host that holds no certificate because nothing is routed yet, and reaches Slack. Staging did so from 2026-09-13 until an application first reached it on 2026-09-16. Every new or rebuilt host built from `docs/bootstrap-a-new-host.md` meets it between stage 7 and stage 8, so its first alert is noise; staging was rebuilt again on 2026-10-18.

Must not: suppress it wherever no certificate exists, which also silences the case it exists for, a Traefik that served certificates and now serves none. A fix needs a series saying the host is *meant* to serve one (a router count or a per-stack expectation).

**Kind**: `change`. It needs that expectation's design and owes a delta to the certificate-expiry alerting requirement in `iac-platform-services`.

**Waits on**: `nothing`.

**Design with**: `nothing`.

**Recorded by**: the operator and a session on 2026-09-15, from the staging host; not by a change.

**Re-checked**: 2026-10-19.

## `aggregate-container-logs`

Container logs are read by `docker logs` over SSH, per container, and are lost when a container is recreated, which every deploy does; alerts say *that* a container restarted, and the reason is in the log that just went away. Traefik's access log is on (stdout), so it now also shortens Traefik's own `docker logs` history.

Loki with an Alloy (or Promtail) collector reading the Docker socket is the stack-native answer: it joins `platform_monitoring`, uses Grafana's existing datasource provisioning pattern, bounds retention as Prometheus does, and stores on the data volume under a `platform_data_volume_subdirs` entry. `bound-host-log-growth-and-add-swap` already bounded the json-file logs it would read. Low priority while a host runs few applications.

**Kind**: `change`. It adds platform services, owing an `iac-platform-services` delta and a retention decision.

**Waits on**: `nothing`.

**Design with**: `nothing`.

**Recorded by**: `unknown`.

**Re-checked**: 2026-10-19.

## `check-public-endpoints-from-outside`

Nothing checks from outside a host that a public hostname resolves and answers on 443. Two failures remain unseen: a cloud-firewall change blocking 443 made at the console (the drift workflow reports only Terraform-managed state; UFW is not in 443's path, see `say-what-the-host-firewall-actually-gates`), and DNS failures with no edit behind them, since both zones use third-party nameservers (`docs/bootstrap-a-new-host.md` §4.4). An expiring certificate is already covered by `alert-on-certificate-expiry`; a hostname served no certificate at all is not. A host-local `blackbox-exporter` cannot see the cloud firewall, since traffic to its own address never leaves the host.

What is left is an external uptime service with a check per hostname, independent of the host as the Watchdog is. healthchecks.io takes only inbound pings, so this is likely a second vendor account.

**Kind**: `change`. It needs the operator's decision on an external uptime vendor and its cost.

**Waits on**: the operator's choice of an external uptime service.

**Design with**: `nothing`.

**Recorded by**: `unknown`; narrowed on 2026-09-09 by `alert-on-certificate-expiry`, which delivered the certificate half.

**Re-checked**: 2026-10-19.

## `reconcile-the-heartbeat-checks-with-what-the-repository-prescribes`

What remains is the slug rule, stated where an operator meets it (`docs/bootstrap-a-new-host.md` §7.1 and Appendix A). Slug-addressed checks (`infrastructure-drift`, `infrastructure-pre-commit-autoupdate`, `<inventory_hostname>-prune-host-images`) are pinged as `hc-ping.com/<ping key>/<slug>?create=1` by `drift.yml`, `pre-commit-autoupdate.yml` and the `image_prune` role, so re-slugging one at the observer alone does not fail: the next ping creates a second check under the old slug and the renamed one goes quiet a period later. Their display names are free to change. The per-stack Alertmanager checks are reached by their own ping URL (`PLATFORM_DEADMANSWITCH_URL`), so renaming one costs nothing. The appendix's *Renaming a server afterwards* covers the server-rename case only; §7.1 and Appendix A do not say which field is load-bearing.

Must not: re-slug a periodic-job check to tidy the list. The prune slugs are templated from `inventory_hostname`, and changing one at the observer alone puts it permanently out of step with the host.

The rest of the original entry is done: §7.1 now prescribes `<stack>-alertmanager` checks, and Appendix A records their period 5 and grace 2 with the reason (alarm after about seven minutes of silence).

**Kind**: `fix`. Documentation only, no decision outstanding.

**Waits on**: `nothing`.

**Design with**: `nothing`.

**Recorded by**: `correct-the-documents-against-the-tree`, whose operator step looked for a check name the observer did not hold; the observer's state is outside that change's documents.

**Re-checked**: 2026-10-19.

## `verify-at-deploy-time-that-what-shipped-is-what-runs`

Nothing establishes that a deploy reporting success applied everything it shipped. After `docker compose up -d --wait`, compare each running container's `com.docker.compose.config-hash` with `docker compose config --hash='*'` and fail on a mismatch. This catches the whole class of containers not replaced, but is a backstop, not a replacement for the `platform.config-checksum` label: without the label, a configuration-only change hashes equal on both sides.

It must run on the host, where `.env` is: several platform services interpolate `${...}` from it, so a hash computed elsewhere mismatches as an artefact. It edits `app-deploy` (installed by `ansible/roles/deploy_user`), which is generic across applications, and needs a decision on what a mismatch does to a deploy that has already replaced and health-checked some services.

It does not catch a secret rotated inside an embedded config such as `alertmanager_config` (both sides hash the same unchanged value). That case is `make-a-rotated-secret-reach-its-inline-config`; a host-side digest taken after interpolation would settle both, which is the deploy-time computation `apply-shipped-config-on-deploy` rejected in its Decision 1, so the two are one decision about the mechanism.

**Kind**: `change`. It changes `app-deploy` for every application, needs the mismatch-handling decision, and owes an `iac-platform-deploy-pipeline` delta to *A Shipped Configuration Change Is Visible to the Container Runtime*.

**Waits on**: `nothing`.

**Design with**: `make-a-rotated-secret-reach-its-inline-config`.

**Recorded by**: `apply-shipped-config-on-deploy`, which deliberately stops at making a change visible; checking it applied edits generic `app-deploy` and needs its own decision. The rotated-secret half was found in that change's code review.

**Re-checked**: 2026-10-19.

## `read-the-rendered-env-back-through-the-host-s-own-parser`

`platform-deploy.yml` escapes each value written into `platform/.env` (double quotes, `\` → `\\`, `"` → `\"`, `$` → `$$`, in that order) so Compose's dotenv parser reconstructs it. That rule is a fact about a parser version (measured on Compose v5.4.0; the host ran v5.5.0 the same day), and both move under Dependabot and host package updates. A diverging parser does not fail the deploy: the service starts healthy and fails wherever it needed the credential. `.github/tests` checks only that the escaping exists and is ordered.

Close it with a deploy-time round trip on the host: render, parse back with the host's own Compose, compare digests rather than values (disclosure-free), refuse the deploy on any mismatch. `tools/env-rendering-probe/` has the harness, both consumption paths and the value corpus.

**Kind**: `change`. It adds a deploy-time refusal owing an `iac-platform-deploy-pipeline` delta to *Platform Secrets Rendered from CI at Deploy Time*.

**Waits on**: `nothing`.

**Design with**: `nothing`.

**Recorded by**: `render-the-env-file-so-a-secret-survives-it`, which measured the rule but could not arrange detection; the check belongs to the deploy path.

**Re-checked**: 2026-10-19.

## `escape-a-value-for-the-configuration-it-is-interpolated-into`

The `.env` escaping guarantees only what the dotenv parser yields. `SLACK_WEBHOOK_URL` and `DEADMANSWITCH_URL` are then interpolated unquoted into the embedded Alertmanager YAML in `platform/docker-compose.yml`, and `ACME_EMAIL` into a Traefik `command:` argument. A `: `, `#`, quote or line break would change or break those documents, and nothing escapes for either context. That today's vendor-issued values carry no such character is a property of the values, not the file, so this is owed work.

Settle: escape at render time (a second escaper per destination) or move the two URLs out of embedded configuration via Alertmanager's file reference, which removes the question. Either way, a corrected value reaches the container only when it is next replaced (*A Shipped Configuration Change Is Visible to the Container Runtime*, `openspec/specs/iac-platform-deploy-pipeline/spec.md`).

**Kind**: `change`. It needs the escape-or-file-reference decision and owes an `iac-platform-deploy-pipeline` delta.

**Waits on**: `nothing`.

**Design with**: `make-a-rotated-secret-reach-its-inline-config` (moving the URLs out of embedded config changes how a rotation reaches the container).

**Recorded by**: `render-the-env-file-so-a-secret-survives-it`, whose obligation deliberately stops at the dotenv parser.

**Re-checked**: 2026-10-19.

## `assert-no-secret-is-built-into-a-url`

postgres-exporter's `DATA_SOURCE_NAME` once interpolated a password into a URL, and a `#` in it discarded the host (see `alert-on-the-exporter-being-unable-to-read-postgres`). That is fixed (`DATA_SOURCE_URI`/`_USER`/`_PASS` in `platform/docker-compose.yml`); owed is a static check in `.github/tests` stopping the shape returning.

The rule: a secret-bearing variable inside a URL, within its own whitespace-delimited word. Offences: a scheme URL, a scheme-less `user:secret@host` authority, a query parameter, a path segment of a scheme-less authority, text concatenated onto a secret that is itself a URL. Not offences: a value that is only the secret (Alertmanager's `api_url`), a non-secret host, a secret beside an unrelated URL, a filesystem path, Compose's `$$`. The defect that recurred in three review rounds: each arm must read the quote-stripped neighbourhood, not anchor to the raw word's start, since quoting in `configs:` and `--flag=value` in `command:` are idiomatic.

Must read: secret names from `platform-deploy.yml`'s render step `env:` block, not keywords (`DEADMANSWITCH_URL` is a bearer credential); and `command:`, `entrypoint:`, `labels:`, `healthcheck.test`, `environment:` and inline `configs:` (`${ACME_EMAIL}` is only in `command:`). It must not pass having read nothing: assert a floor of interpolations found.

**Kind**: `change`. It owes a requirement stating the rule the check enforces (`iac-platform-deploy-pipeline`), and its earlier draft did not fit one review sitting.

**Waits on**: `nothing`.

**Design with**: `nothing`.

**Recorded by**: the 2026-09-15 fix to postgres-exporter's connection settings (change name not recorded), from which the check was split because its draft was wrong in three rounds of review.

**Re-checked**: 2026-10-19.

## `hold-every-platform-deploy-for-the-length-of-a-window`

`platform/README.md`'s *Upgrading the PostgreSQL major version* asks the operator to hold every other `platform/**` merge and every `platform-deploy.yml` dispatch for the length of the window. Nothing enforces it, and the failure is silent: step 2 leaves the host without the `postgres` container its Compose definition declares, so any platform deploy landing in the gap (an unrelated merge, or the rebuild dispatch in `docs/runbook-rebuild.md`) recreates it on the **old** major with an empty cluster, undoing step 2 without an error. The window's own pull request is already gated (opened as a draft, marked ready only once the store is cleared); a draft gates only itself.

The class is wider than PostgreSQL: the platform stack is deployed wholesale on every merge, so any window that leaves the host deliberately out of step with the committed definition can be undone by a deploy. `platform-deploy.yml`'s per-stack `concurrency` group serialises deploys but does not refuse one. A refusal needs state that outlives a run (a repository variable, an issue label, a file on the host, an Environment gate); the design must cover a window abandoned half-way and say what a held merge does: queue and land unwatched at release, or fail loudly and be re-run.

**Kind**: `change`. It needs operator decisions: where the lock lives, who releases it, and whether a held deploy queues or fails.

**Waits on**: `nothing`.

**Design with**: `notice-a-pending-reboot-and-decide-what-does-it`, whose automatic-reboot policy is a scheduled outage that this mechanism would keep a deploy out of.

**Recorded by**: the 2026-09-15 work that gated the window's own pull request with a draft (change name not recorded); that half was a fix, this half needs a mechanism and decisions.

**Re-checked**: 2026-10-19.

## `automate-per-application-database-provisioning`

*Single Shared PostgreSQL Instance, Per-Application Databases* (`openspec/specs/iac-platform-services/spec.md`) obliges automating how an application's database and role are provisioned in the shared instance and how the role's password reaches the application. The trigger fired on 2026-09-13 (`commerce-ops` on staging; production followed). Both were provisioned by hand from the recipe in `docs/onboard-an-application.md`, and the requirement carries a paragraph, "One divergence is stated rather than hidden, as of 2026-09-13", saying it is unmet until this lands.

A design must answer: where the password is generated and how it reaches the application's deploy without a command line, log line or file in this repository; what happens when the secret name is already taken (production's `commerce-ops` already held `POSTGRES_PASSWORD`, so the shared-instance password became `SHARED_POSTGRES_PASSWORD`); that a re-run is a rotation picked up only on the application's next deploy; re-provisioning after a rebuild or store reset; and per-host independence, so one leaked credential reaches one host.

**Kind**: `change`. It owes a MODIFIED delta on *Single Shared PostgreSQL Instance, Per-Application Databases* replacing the divergence paragraph, an update of `docs/onboard-an-application.md` and `platform/README.md`'s "Getting a database inside the instance", and a design of the credential path.

**Waits on**: `nothing`.

**Design with**: `nothing`.

**Recorded by**: `provision-commerce-ops-database-in-the-shared-instance`, which provisioned by hand because a mechanism fitted to one consumer would be discovered wrong by the next.

**Re-checked**: 2026-10-19.

## `exercise-the-volume-server-coupling-against-live-state`

`terraform/stacks/main-production/main.tf` couples the volume to the server (`count = var.volume_enabled && var.server_enabled ? 1 : 0`). *Conditional Prod Volume Creation* (`openspec/specs/iac-data-volumes/spec.md`) states two scenarios, *Volume toggle disabled creates nothing* and *Disabling the server also removes the volume*, that nothing has run against production's live state. The module tests under `terraform/modules/volume/tests/` cannot reach a stack's `count`.

Staging's half was observed on 2026-09-16 by `write-and-rehearse-the-rebuild-runbook` (`server_enabled = false` planned `0 to add, 0 to change, 3 to destroy`: server, firewall and volume; the apply destroyed the volume first). That also settled where the reads can run: the pull request's own plan job, which needs no local HCP credential (the workstation's credential belongs to another organisation). What remains is production, where no backup covers the volume: two plan-only reads (each toggle set false in turn) on a pull request that is read and closed, **never merged or applied**.

**Kind**: `fix`. No delta, no decision. It runs two existing scenarios as plans and records the result.

**Waits on**: `nothing`.

**Design with**: `decide-whether-the-data-volume-should-survive-a-server-toggle`, which would change the coupling these reads exercise.

**Recorded by**: `make-openspec-validation-a-usable-gate`, which recovered it from `add-prod-data-volume`'s unticked task 3.5 (now under that archive's `## Not performed`), where it would otherwise have been lost.

**Re-checked**: 2026-10-19.

## `say-what-a-stale-saved-plan-is-and-how-to-recover-from-it`

`apply.yml` names a clean failure for a missing or expired plan artifact. A stale saved plan only gets Terraform's raw `Error: Saved plan is stale`. That is the gate working: *Gated Production Apply Applies the Reviewed Plan* demands the exact reviewed plan. The change owes a named failure for this case: what staleness means, that no infrastructure change was lost, and that recovery is a **fresh run of the whole workflow** (re-running the failed job re-downloads the same stale artifact). It must not auto-replan, which would apply an unreviewed plan.

Observed 2026-09-12 on the merge of `rename-the-external-services` (PR #155): production's state serial moved 44 → 45 between plan and apply with no attribute changed, so a no-op operation still invalidates a saved plan. A local `terraform plan` under the read-only token was measured not to bump the serial; CI, the operator's checkout, the change's working trees and HCP health assessments were ruled out. The workspace's **States** view in HCP, which labels each version's source, is the unread avenue. Since 2026-10-11 `main-production` carries no required reviewer, so apply follows plan by seconds and the window is narrow; it widens again if a reviewer returns.

**Kind**: `change`. It needs a decision on whether the message names likely causes, and, if a permitted local operation can invalidate a pending apply, an `AGENTS.md` rule change.

**Waits on**: `nothing`.

**Design with**: `say-production-is-no-longer-reviewer-gated`, which decides whether the approval window that makes a plan perishable exists at all.

**Recorded by**: the merge of `rename-the-external-services` (PR #155), whose apply failed this way; the error-handling gap was outside that change's subject.

**Re-checked**: 2026-10-19.

## `make-a-waiting-approval-announce-itself`

Nothing tells the operator that a gated run is waiting for approval. On 2026-09-12 a production converge sat unapproved 06:26–09:56, and on 2026-09-13 one waited 6h34m. Each was found only because a later run queued behind it (`waiting on converge (main-production) … to complete`, which reads like a hung job). The Terraform apply, the host converge and the platform deploy gate on the same Environment and render indistinguishable prompts, and a pending approval stalls every later converge of that stack.

Measure first whether GitHub's *deployment review requested* notification exists and simply is not reaching the operator; if so, this is a settings change plus a sentence in `docs/bootstrap-a-new-host.md` §6.6. Otherwise, a scheduled query of `gh run list --status waiting` pushed somewhere read, repeating while the state persists. Trap: Alertmanager's `SLACK_WEBHOOK_URL` comes from `PLATFORM_SLACK_WEBHOOK_URL`, a production-Environment secret, so a notifier using it gates on the approval it announces; its credential must be ungated. It must not fire on every run.

**Kind**: `change`. It needs operator decisions on the channel and the credential source, and may add a scheduled workflow (with its heartbeat obligation).

**Waits on**: a required reviewer being restored on the `main-production` Environment. It was removed on 2026-10-11 (`say-production-is-no-longer-reviewer-gated`; `gh api …/environments` shows no protection rules), so today nothing waits.

**Design with**: `say-production-is-no-longer-reviewer-gated`.

**Recorded by**: `rename-the-external-services`, which lost three and a half hours to it and recorded only the recognition advice.

**Re-checked**: 2026-10-19.

## `factor-the-four-stack-discovery-bodies`

`pr-validation.yml`, `apply.yml` and `drift.yml` share one ~160-line stack-discovery shell body, asserted identical by `.github/tests`, which locates a body by the `terraform/stacks` path literal it contains and executes it against a scratch tree. `host-converge.yml` and `platform-deploy.yml` carry near-siblings that are deliberately not identical (`host-converge.yml` also enumerates `ansible/inventory/*.hcloud.yml` and cross-checks both sets), and both sit outside the identity assertion; `platform-deploy.yml`'s comment counts "five near-siblings".

A script under `.github/scripts/` (none exists yet) is likely simpler than a composite action: executed directly, it removes the path-literal locator. The shared parts are the flat `key: value` reader, secret-name validation, the empty-result refusal and the JSON emission; the roots and cross-checks stay parameters. Weigh it against the cost: it restructures the production apply path and replaces the identity assertion rather than retargeting it.

**Kind**: `change`. It restructures every gated workflow's discovery and replaces a test assertion, which is too large for one review sitting.

**Waits on**: `nothing`.

**Design with**: `nothing`.

**Recorded by**: `apply-host-configuration-through-a-gated-workflow`, which wrote the fourth body (`host-converge.yml`); factoring was out of scope for a change already restructuring gated workflows.

**Re-checked**: 2026-10-19.

## `two-deferred-ci-items`

Two unrelated CI improvements deferred by `close-ci-verification-gaps`:

- **The destroy-policy gate's inspection logic is inline workflow shell.** Moving it into a version-controlled script with executable fixtures would make the highest-consequence logic here testable. That change's `design.md` Decision 5 deferred it on scope, not merit; four fixtures are described in its `tasks.md` 1.1 (clean, destructive, malformed, valid-JSON-not-a-plan). `.github/tests/test_ci_configuration.py` asserts the routes are closed, not that each is reached.
- **`actionlint` is cited as a verification means, but nothing installs it** (absent from `.pre-commit-config.yaml`). Landing the hook first needs a disposition of two pre-existing, intentional `SC2016:info` findings (single-quoted markdown in `echo`, in `pr-validation.yml`'s plan-comment step and `apply.yml`'s job-summary step).

**Kind**: `change`. The first restructures the production destroy gate; the second needs an operator decision on dispositioning the two findings.

**Waits on**: `nothing`.

**Design with**: `nothing`.

**Recorded by**: `close-ci-verification-gaps`, which deferred both on scope rather than rejecting them.

**Re-checked**: 2026-10-19.

## `matrix-the-molecule-suite-over-scenarios-and-bound-each-job`

`molecule test --all` stops at a role's first failing scenario and omits the rest from the SCENARIO RECAP, so a red run under-reports while looking complete. Molecule's `--continue-on-failure` needs `--workers`, which refuses outside collection mode (observed 2026-09-07). The remedy is an `ansible-verify.yml` matrix over **scenarios** rather than roles (`molecule (${{ matrix.role }})` today), which also parallelises the longest role. It is not the shared-state hazard, which per-working-tree namespacing already closed.

The same change bounds each job. No workflow sets `timeout-minutes`, so jobs inherit 360 minutes, and `ansible-verify` is a required check: a hung scenario leaves a pull request pending six hours. `AGENTS.md`'s Molecule section describes ways a run hangs. The value must sit above the slow-but-green ceiling and below six hours, chosen against durations measured after `cache-the-apt-index-within-a-converge` and per-scenario jobs, and recorded in the proposal.

Must not undo (`openspec/specs/iac-cicd-pipeline/spec.md`): *Required Status Checks Report on Every Pull Request*, so the literal-named aggregating job stays as the registered check; and *Ansible Configuration Is Verified in Continuous Integration and Gates the Merge*, so scenarios are discovered from `ansible/roles/*/molecule/*/` and an empty result fails loudly.

**Kind**: `change`. It reshapes a required check's jobs and needs an operator decision on the timeout value.

**Waits on**: `nothing`.

**Design with**: `unify-the-workflows-own-role-discovery`, which reshapes the same discovery step in `ansible-verify.yml`.

**Recorded by**: `promote-molecule-to-a-required-check`, which named it a non-goal so that the change registering the check did not also redefine it; the timeout half was recorded 2026-09-11 beside `cache-the-apt-index-within-a-converge`.

**Re-checked**: 2026-10-19.

## `test-a-play-at-play-scope`

`ansible/playbooks/host-baseline.yml` carries a guard play that refuses when the target environment resolves to no host. Nothing tests it: Molecule's subject is a role on a host, and `.github/tests` reads only committed files (`TestEveryModuleInTheSuiteDirectoryNeedsNoPrivilegedResource` would fail a module that ran `ansible-playbook`). So a green pull request only shows the guard is present. One bypass is known and cannot be closed: `--limit` filters `localhost` out of the guard play, so `--limit <host>` against an empty group exits 0; it is stated in the play header and `docs/bootstrap-a-new-host.md`.

A play-scope harness would assert the refusal under each invocation shape, and would also cover role ordering, `when:` on role inclusion, and the deferred play-scope input validation noted above the playbook's role list.

**Kind**: `change`. It adds a fourth test command (a row in `AGENTS.md`'s test-command table) and a runner, which is an operator decision.

**Waits on**: `nothing`.

**Design with**: `nothing`.

**Recorded by**: `configure-the-staging-host` (`design.md` Decision 10), whose diff needed close reading and was no place to invent a test tier.

**Re-checked**: 2026-10-19.

## `tighten-the-refusal-scenario-s-own-filesystem-assert`

`ansible/roles/platform_data_volume/molecule/superseded-path-in-force-refused/verify.yml` asserts `platform_data_volume_blkid.rc != 0` to show the role refused before formatting. It fails open: `blkid` returns 1 on a usage error, so a probe that did not happen reads as "no filesystem". Tighten it to `rc == 2`, the only code meaning "looked, found nothing" (measured in the pinned image: unformatted 2, formatted 0, usage error 1, absent device 2), as the role's `prepare.yml` plays already were.

A second, separate hazard that tightening does not close: `prepare.yml`, `converge.yml` and `verify.yml` each redeclare `platform_data_volume_fixture_loop_minor` (`base + 4`) by hand. A drifted `verify` probes an unassociated minor, gets rc 2 and passes. Either derive the minor from one place, or have `verify` assert that its device is the one `prepare` associated; do not close one believing it closed the other.

**Kind**: `fix`. A test-only tightening with no delta or decision.

**Waits on**: `nothing`.

**Design with**: `nothing`.

**Recorded by**: `namespace-the-molecule-loop-devices`, whose code review found it in a line that change did not author.

**Re-checked**: 2026-10-19.

## `adopt-the-stubbed-runtime-rig-for-the-guards-molecule-cannot-reach`

Two guards in the `image_prune` role are unasserted: local images are enumerated before the keep set is computed, and each tag is re-resolved immediately before removal. Both are observable only when the host's images change mid-run, which a black-box Molecule scenario has no seam for, and they are the guards facing `app-deploy`, the only concurrent actor. The two abandon branches that change's review fix added are likewise unasserted (the `abandon-paths` scenario covers the design's three, not these).

That change's code review built a rig, a stubbed `docker` on `PATH` answering some calls and failing others, which showed both guards mutation-visible and reproduced the fail-open the review found. Its `test-plan.md` (archive `2026-09-08-prune-unreferenced-host-images-periodically`) invites adding a deterministic ("sized rather than slept") arrangement to `tasks.md` 2.7/2.8.

**Kind**: `fix`. Tests for behaviour already specified, with no delta or decision.

**Waits on**: `nothing`.

**Design with**: `nothing`.

**Recorded by**: `prune-unreferenced-host-images-periodically`'s code review, which built the rig only to verify, not to ship.

**Re-checked**: 2026-10-19.

## `hold-the-whole-static-suite-to-its-own-constraints`

The suite-wide half is done: `TestEveryModuleInTheSuiteDirectoryNeedsNoPrivilegedResource` in `.github/tests/test_ci_configuration.py` holds every module in the directory to the suite's no-network, no-credential, no-container, no-Terraform constraints. What remains is the absorbed `prune-the-repository-walkers-of-provisioned-content` half: repository-scope walkers read a directory, not the committed tree.

`compose_shaped_files()` (used by `TestEveryComposeFileDeclaringAServiceImageIsCovered`) walks through `walked_files()`, which prunes `.git`, `.terraform`, `__pycache__`, `node_modules`, `openspec`, the Galaxy role and the worktree directories, but not `.molecule-home/`. On a developer machine provisioned for Molecule it finds `community.docker`/`community.general` fixture Compose files there and fails, while CI never provisions Molecule and stays green; it is also a race while Molecule creates and removes `tmp/` under that directory (observed 2026-09-11). The fix is to re-point repository-scope walkers at the existing `tracked_files()` helper in the same module, not to prune one more directory. Deleting `.molecule-home/` to get green throws away provisioning.

**Kind**: `fix`. No delta; the helper already exists.

**Waits on**: `nothing`.

**Design with**: `share-the-static-suites-test-arrangement`, which gives the same suite a support module.

**Recorded by**: `alert-on-certificate-expiry` (the self-check half), and the test author deriving `cache-the-apt-index-within-a-converge`, who met the walker half as a red suite; neither change's subject was the suite's walkers.

**Re-checked**: 2026-10-19.

## `complete-the-autoupdate-workflow-s-own-checks`

`open-autoupdate-pr-with-app-token` added a section to `.github/tests/test_ci_configuration.py` that finds pull-request-opening steps and asserts their identity. Its helpers have four reading limits, each a false positive on a legitimate change: `token_inputs` reads only step-level `env:` and misses a job- or workflow-level `GH_TOKEN` (the likeliest to bite, the first time a workflow opens a PR with `gh`); `step_opens_a_pull_request` matches a POST and `/pulls` anywhere in one `run:` block; `secrets_referenced_by` scans the whole job, not the identity path (`HEARTBEAT_PING_KEY` already sits in that workflow); `readme_sections` splits at any `#` line, including inside code fences.

The section also asserts nothing about two properties of `.github/workflows/pre-commit-autoupdate.yml`: the minting step's `permission-contents: write` / `permission-pull-requests: write` down-scoping, and the restricted input set on the PR step (no `labels`/`assignees`, which need Issues). Neither is live while the App's own scope matches. They come from prose, not a scenario, so a scenario must be written before a test can be derived. The workflow header notes which claims the suite does not stand behind.

**Kind**: `change`. It owes a delta adding scenarios for the two unasserted properties, and edits tests an independent author derived.

**Waits on**: `nothing`.

**Design with**: `nothing`.

**Recorded by**: `open-autoupdate-pr-with-app-token`, whose tests were independently derived from its deltas; fixing or extending them was a change of its own.

**Re-checked**: 2026-10-19.

## `assert-every-role-has-a-mock_roles-entry`

`.ansible-lint`'s `mock_roles:` hand-lists every role referenced by name, because ansible-lint does not resolve roles through `ansible/ansible.cfg`'s `roles_path`. Nothing asserts the list is complete. A new role under `ansible/roles/` used from `ansible/playbooks/host-baseline.yml` without an entry fails ansible-lint twice (playbook and the role's own `converge.yml`) with a misleading "role not found" naming a search path, which sends the time to the wrong file (observed 2026-09-08 adding `swap`). The cost lands on whoever adds the next role. The check is a static read for `.github/tests`: role directories under `ansible/roles/` minus the gitignored external role, against `mock_roles`. It has the same shape as the "every lockfile-bearing directory is covered" check. The list is complete today.

**Kind**: `fix`. A static assertion with no delta or decision.

**Waits on**: `nothing`.

**Design with**: `nothing`.

**Recorded by**: `bound-host-log-growth-and-add-swap`, which hit the gap and added its missing entry; asserting the invariant was a different concern from that change's subject.

**Re-checked**: 2026-10-19.

## `assert-every-tfvars-assigns-its-required-variables`

Nothing checks that each stack's `terraform.tfvars` assigns every variable its `variables.tf` declares without a `default`. A gap surfaces only at plan time: `pr-validation.yml`, `apply.yml` and `drift.yml` run with `-input=false`, so the plan fails `No value for required variable`, the required check fails, and the nightly drift sweep fails every night and takes the shared heartbeat with it. Detecting it that way needs a credential, a workspace and a network. The same fact is a static read for `.github/tests`; the only real work is a small parser of `variable` blocks and `.tfvars` assignments without HCL machinery the suite does not have. `.github/tests/test_a_second_environment.py` already reads `terraform.tfvars` and can lend its approach. Both stacks currently assign `server_type`.

**Kind**: `fix`. A static assertion with no delta or decision.

**Waits on**: `nothing`.

**Design with**: `nothing`.

**Recorded by**: `add-a-staging-environment`'s code review (2026-09-10), which met the gap as that change's own in-flight state (`server_type` unassigned in `main-staging`); a check failing the tree still being assembled belonged to a later change.

**Re-checked**: 2026-10-19.

## `assert-markdown-prose-is-not-hard-wrapped`

`AGENTS.md` says "Do not hard-wrap prose. Keep each paragraph on a single line". Nothing checks it, and hard wraps re-accumulate silently: the sweep this entry was recorded beside (2026-09-11) rewrapped 72 of 211 tracked markdown files, and the wraps had appeared in every week of the project. Under the rule, any prose paragraph spanning more than one line is a violation, so no threshold is needed. The detector must exempt structural breaks: fenced and indented code, tables, YAML frontmatter, list-item continuations, and lines ending in two spaces or a backslash. Scope is markdown only; comments in `.py`/`.yml`/`.sh`/`.tf` stay wrapped (`.pre-commit-config.yaml`'s comments are the shape to preserve). It is not a formatter: Prettier's `proseWrap` would rewrite style across the tree and archived records, and there is no Node toolchain to hang it on; markdownlint has no such rule. It fits `.github/tests` as one new module.

**Kind**: `fix`. A static assertion with no delta or decision.

**Waits on**: `nothing`.

**Design with**: `nothing`.

**Recorded by**: `unknown` change; recorded 2026-09-11 beside the fix that removed the hard wraps and wrote the rule, but not its check.

**Re-checked**: 2026-10-19.

## `unify-the-workflows-own-role-discovery`

`ansible-verify.yml`'s *Discover roles carrying scenarios* step enumerates roles in shell by the directory-name heuristic (`grep -v '\.'`). `unify-the-two-role-exclusion-rules` replaced that heuristic in both Python implementations (`.github/tests/test_ci_configuration.py` and `ansible/scripts/select_molecule_roles.py`) with the `ansible/requirements.yml`-derived rule, so the repository holds two rules again. They agree on today's tree (`geerlingguy.docker` is dotted and pinned) and diverge on a second pin in `src:` form or vendored content nobody pinned. No assertion compares the workflow's enumeration with the others; `test_the_workflow_names_no_role_literally` checks only that it names no role literally.

The smaller option is taking the role list from the selector. Expect `.github/tests/test_the_matrix_runs_the_roles_a_pull_request_owes.py`'s `_discovery_steps` fixtures, which build scratch trees with no `ansible/requirements.yml`, to meet the selector's `DerivationRefused`. The same module's `test_an_external_galaxy_dependency_contributes_no_edge_and_is_not_refused` still filters with `if "." in target`; under the unified rule it must be rewritten with a new way to express "an edge to content this repository does not carry", the same question this entry asks of the workflow.

**Kind**: `change`. It changes what CI runs and needs a decision on how the workflow obtains the manifest-derived list.

**Waits on**: `nothing`.

**Design with**: `bind-the-galaxy-name-resolution-to-ansible-itself`, which works on the same resolution of external role names from the same manifest.

**Recorded by**: `unify-the-two-role-exclusion-rules` (archived 2026-09-15); nothing bound the workflow to the other two rules, and changing a workflow's discovery was no rider on a test-helper change.

**Re-checked**: 2026-10-19.

## `bind-the-galaxy-name-resolution-to-ansible-itself`

Two implementations resolve a `roles:` entry to the directory `ansible-galaxy` installs it under: `.github/tests/test_ci_configuration.py` and `ansible/scripts/select_molecule_roles.py`. A test binds them only to each other, and both were once wrong in the same two ways with every test green: they refused `- role: <name>`, and they split a `,version` qualifier before stripping `.git`, so `…/ansible-role-docker.git,8.0.0` was named `ansible-role-docker` instead of `ansible-role-docker.git`. Both were corrected by hand against Ansible 2.21.3. Nothing checks them against `RoleRequirement.role_yaml_parse`, so a future divergence goes unnoticed.

`.github/tests` cannot import `ansible-core`: *The Suite Needs No Privileged or External Resource* (`openspec/specs/iac-cicd-pipeline/spec.md`) limits it to the standard library and `.github/requirements-ci.txt` (`pre-commit`, `PyYAML`), and the suite catches even a lazy import. The check belongs where Ansible is pinned: a Molecule scenario, or an `ansible-verify.yml` step after `ansible/requirements-test.txt` is installed. Adding `ansible-core` to `requirements-ci.txt` instead changes what the static suite is.

**Kind**: `change`. It needs a decision on where the check lives; the `requirements-ci.txt` option would owe a delta on *The Suite Needs No Privileged or External Resource*.

**Waits on**: `nothing`.

**Design with**: `unify-the-workflows-own-role-discovery`.

**Recorded by**: `unify-the-two-role-exclusion-rules`, which found both copies wrong but could not write the check inside the static suite.

**Re-checked**: 2026-10-19.

## `catch-up-the-drifted-galaxy-pins`

`ansible/requirements.yml` pins `hetzner.hcloud` 7.0.0 and `geerlingguy.docker` 8.0.0 (current on 2026-09-08). Three collections are at least a major behind: `community.general` 9.5.0 (13.4.0 available then), `ansible.posix` 1.6.2 (2.2.2), `community.docker` 4.1.0 (5.3.0). Dependabot has no `ansible-galaxy` ecosystem, so nothing proposes bumps here. Used by `hardening` (`community.general.ufw`), `deploy_user` (`ansible.posix.authorized_key` `key_options`, `community.docker.docker_login`), `swap` (`ansible.posix.mount`, `ansible.posix.sysctl`) and the dynamic inventory. Molecule is the gate: run `molecule test --all` per role and read the SCENARIO RECAP, not the exit code. `ansible-core` (pinned in `ansible/requirements-test.txt` and `ansible/requirements.txt`) and these collections were verified together as a set. The "confirm it resolves" caveats were removed on 2026-09-15; the manifest header records the 2026-09-08 confirmation.

**Kind**: `change`. A multi-major migration across several collections, too large for one review sitting.

**Waits on**: `nothing`.

**Design with**: `cover-the-unwatched-manifests-and-settle-the-watcher`, since `ansible-core` and the collections are a matched set and a bot bump of one landing mid-migration would confuse which half broke.

**Recorded by**: an inventory taken while archiving `open-autoupdate-pr-with-app-token` (2026-09-08); a migration was not a rider on that archive.

**Re-checked**: 2026-10-19.

## `cover-the-unwatched-manifests-and-settle-the-watcher`

`.github/dependabot.yml` watches `terraform`, `github-actions`, `docker-compose` (`platform/` and `tools/env-rendering-probe/`) and `npm`. Nothing watches the pip manifests: `.github/requirements-ci.txt`, `ansible/requirements-test.txt` and `ansible/requirements.txt` (which also pins `ansible-core`'s dependencies). `ansible/requirements.txt`'s `ansible-core` must equal `requirements-test.txt`'s, and `.github/tests/test_host_converge_workflow.py` fails on a difference, so a bump of one alone is red on arrival: the two must move as a pair (a grouped update, or one watched and the other asserted to follow). Do not inherit the "one stanza" estimate: *Automated Dependency Updates* (`openspec/specs/iac-safety-hardening/spec.md`) enumerates ecosystems by name and the suite reads it back, so a stanza also needs a delta and its tests.

The watcher choice was settled with a recommendation: stay with Dependabot for now. Renovate covers `pre-commit` and `ansible-galaxy` natively, but hosted Renovate is a third party with write access; self-hosted Renovate could reuse the `infrastructure-autoupdate` App. Revisit when a second deployed Compose stack appears, the galaxy manifest grows, or the galaxy migration is done and small bumps start being missed. The old precondition (something notices a red scheduled run) is met by `notice-when-a-periodic-job-stops-reporting`'s heartbeat checks.

**Kind**: `change`. It owes a delta widening *Automated Dependency Updates*' ecosystem enumeration, and a decision on how the two `ansible-core` pins move together.

**Waits on**: `nothing`.

**Design with**: `catch-up-the-drifted-galaxy-pins`.

**Recorded by**: `unknown` change; the same shape as `cover-platform-images-with-dependabot` (archived 2026-09-08), which closed the image half; the watcher question was recorded 2026-09-08.

**Re-checked**: 2026-10-19.

## `rename-the-requirements-that-read-narrower-than-they-are`

Requirement names are this repository's citation form, and several still name production or "this host" alone although two environments now share them. From `make-the-pipeline-environment-agnostic`: *Gated Production Apply Applies the Reviewed Plan* (a genuine mismatch) and *Credential Scoping by Privilege* (`iac-cicd-pipeline`), and *Write Credentials Confined to the Gated Pipeline* (`iac-safety-hardening`). Second set: *Conditional Prod Server Creation* (`iac-server-lifecycle`), *Conditional Prod Volume Creation* (`iac-data-volumes`), *Data Durability for Stateful Resources* and *No Store on This Host Holds Data Requiring Backup* (`iac-safety-hardening`), *Host Joins a Private Tailnet for Non-Operator SSH Access* and *Unprivileged Operator Accounts Support Interactive Host Inspection* (`iac-host-configuration`). Staging uses the same toggles, tailnet and operator account, and staging took the platform stack on 2026-09-13, so it holds stores: `platform_postgres_data`, Traefik's certificates and Alertmanager's volume; "this host" is now wrong about which host a durability obligation binds.

Renaming sweeps every citation: comments in `apply.yml`, `drift.yml`, `pr-validation.yml`, `docs/bootstrap-a-new-host.md`, `.github/tests`. `.github/tests/test_a_retired_requirement_name_is_reported.py` makes the sweep checkable. Precedent: `add-a-staging-environment` renamed *Each Stack Has a Dedicated Hetzner Cloud Project* where it had a content change to carry it.

**Kind**: `change`. It owes RENAMED/MODIFIED deltas across four capabilities and a repository-wide citation sweep.

**Waits on**: `nothing`.

**Design with**: `sweep-the-stale-scenario-titles-and-check-them`, the same citation-sweep mechanism over scenario titles; `say-production-is-no-longer-reviewer-gated`, which owes a delta to *Gated Production Apply Applies the Reviewed Plan*.

**Recorded by**: `make-the-pipeline-environment-agnostic` (first set) and the staging changes that followed it (second set); both declined to mix a mechanical rename into diffs restructuring gated workflows or one environment directory.

**Re-checked**: 2026-10-19.

## `sweep-the-stale-scenario-titles-and-check-them`

Citations here name a requirement and often a scenario inside it (`... -- scenario "<title>"`). Both halves rot in the same rename, and `correct-the-documents-against-the-tree` corrected and checked only the requirement half, so many citations under `.github/tests` (and one in `.github/workflows/drift.yml`) name a scenario no specification under `openspec/specs/` holds (30 counted on 2026-09-13). Several titles were reworded rather than renamed, so each replacement needs a reading, not a substitution.

The `drift.yml` citation is the inverse case: it cites *"Drift in one stack does not resolve another's report"* while `openspec/specs/iac-cicd-pipeline/spec.md` still titles it *"Drift in one environment does not resolve another's report"*. `rename-terraform-environments-to-stacks` left the specification side alone because a `MODIFIED` requirement replaces its block whole and `openspec validate` reads a renamed scenario as dropped. Sweeping without deciding how a scenario is renamed would leave the tree citing a title the specification lacks.

Do the check with the sweep: `.github/tests/test_the_retired_requirement_names_are_gone.py` already reads every tracked file, flattens wrapped comments and derives its subject from committed specifications. The scenario predicate is its inverse (a cited title **not** among live scenario titles), so it needs its own reader; measure its false-positive rate first, since any quoted phrase looks like a citation.

**Kind**: `change`. It needs a decided mechanism for renaming a scenario through a `MODIFIED` delta, and the `drift.yml` case owes an `iac-cicd-pipeline` delta renaming that scenario.

**Waits on**: `nothing`.

**Design with**: `rename-the-requirements-that-read-narrower-than-they-are`.

**Recorded by**: `correct-the-documents-against-the-tree` (archived 2026-09-13), which swept requirement names; the scenario half is a different predicate over a different set and would have doubled its diff with a second unchecked sweep.

**Re-checked**: 2026-10-19.

## `separate-history-from-rationale-in-source-comments`

Source comments mix three kinds of text with no way to tell them apart: why the code is shaped this way (keep), what a past change did (git and the archive own it), and TODOs whose condition has passed (dead and misleading). A pass should leave only the first. The ratio is worst in `ansible/roles/tailscale/tasks/main.yml` (140 comment lines of 197 non-blank, up from 48 of 90), a maintenance cost rather than a cosmetic one.

**Must not undo**: load-bearing rationale such as the tailnet polarity note in `ansible/roles/tailscale/tasks/main.yml` and the `ghcr_pull_*` tolerated/not-tolerated block in `ansible/roles/deploy_user/tasks/main.yml`. The two instances this entry once named (`terraform/stacks/main-production/ssh_key.tf`'s `moved` block, `main.tf`'s `delete_protection` parenthetical) were taken as fixes on 2026-09-15; the pass needs instances of its own. The citation-form decision it used to wait on was delivered by `decide-archived-change-reference-policy` (archived 2026-09-07).

**Kind**: `change`. A repository-wide pass is too large for one review sitting, and the rule for what a comment may hold needs the operator's decision and a home in `AGENTS.md`.

**Waits on**: `nothing`.

**Design with**: `nothing`.

**Recorded by**: `unknown`; it was unblocked by `decide-archived-change-reference-policy`, which changed citation form only and deliberately left the surrounding prose alone.

**Re-checked**: 2026-10-19.

## `record-the-hostname-scheme`

Public names follow `<service>.<server>.BASE_DOMAIN` (`<app>.main-production.BASE_DOMAIN`, `<app>.main-staging.BASE_DOMAIN`), resolved by one wildcard `A` record per server, with short aliases as records of their own. The rule was decided in the `commerce-ops` repository, whose `deploy-commerce-ops-to-staging` handoff names `docs/naming-conventions.md` here as its home, but that file names servers, stacks, keys and the OS hostname and not public names. It owes: the rule, where the base domain comes from, and how it composes with the `<company>` segment and the stack name that file already rules on (a company-owned base domain is an axis `<company>` does not cover). `docs/bootstrap-a-new-host.md` §4.4 describes the wildcard shape (and now `BASE_DOMAIN`/`COMPANY_DOMAIN` record tables) and should then point at the rule rather than restate it.

**Kind**: `change`. Documentation only, but how a company-owned base domain composes with `<company>` is a naming decision the operator has not made.

**Waits on**: `nothing`.

**Design with**: `nothing`.

**Recorded by**: `expose-staging-on-the-web` (archived 2026-09-15), which wrote down the DNS the scheme produces but not the scheme.

**Re-checked**: 2026-10-19.

## `announce-a-rebuild-to-the-applications-that-hold-databases`

*The Host Carries an Operator-Declared Maintenance Window for the Shared Instance* (`openspec/specs/iac-host-configuration/spec.md`) lets applications read `window-open` from `/var/lib/platform-maintenance/shared-postgres-window` during a destructive act on the shared instance. It cannot announce a rebuild, because the declaration lives on the host the rebuild destroys: the probe gets no answer, which is exactly the state of a host that has fallen over, so an application cannot tell the two apart when it matters most.

The change owes a decision on who the audience is and where such a declaration lives: off the host (a repository variable, status page, or field the application's deploy reads) survives the rebuild but needs a second mechanism; on the host but restored early closes only part of the window; out-of-band to operators is not machine-readable. Today `docs/runbook-rebuild.md` says the alarms are expected and asks the operator to tell each application's owner by hand. Staging holds no database-bearing application since `remove-commerce-ops-from-staging` (archived 2026-10-18); `basis-api` is onboarded with a probe key for a database it will take later.

**Kind**: `change`. It needs the operator's decision on audience and location, and owes an `iac-host-configuration` delta.

**Waits on**: a second application holding a database in a shared instance (`basis-api`'s planned database is the likely one), or a rebuild performed by someone other than the operator who would otherwise send the message.

**Design with**: `nothing`.

**Recorded by**: planning `write-and-rehearse-the-rebuild-runbook` (2026-09-16), which found the gap; it was not a blocker on the runbook because a rebuild is operator-initiated and can be announced by hand.

**Re-checked**: 2026-10-19.

## `make-a-rotated-secret-reach-its-inline-config`

A secret interpolated into an inline `configs:` block in `platform/docker-compose.yml` does not reach the container on a deploy, and the deploy reports success. `platform.config-checksum` (from `apply-shipped-config-on-deploy`) is computed from committed text; a secret moves only the rendered config, so `docker compose up -d --wait` sees an identical service and leaves it running. Affected today: `DEADMANSWITCH_URL` and `SLACK_WEBHOOK_URL` in `alertmanager_config`, i.e. the dead-man's-switch and alert routing, both of which fail silently. Measured on staging 2026-09-16: Alertmanager still pinged the old URL eleven hours after a green deploy. Rotating `PLATFORM_SLACK_WEBHOOK_URL` and revoking the old one would leave alert delivery dead with every check green.

Options: force-recreate services whose configs interpolate a secret; compute the checksum over the rendered config at deploy time (ends the static check, catches both cases); or a post-deploy probe asserting the running config carries the shipped value, in the shape `make-a-shared-instance-reset-visible-to-its-applications` used. It is a property of a running container, so neither `.github/tests` nor Molecule can hold the test. Until it lands, a rotation is followed by recreating the service by hand and confirming the value arrived (the comment in `alertmanager_config` says so). A non-inline `environment:` value is recreated correctly; Grafana ignoring a delivered password is `make-a-rotated-grafana-password-reach-grafana`, not this.

**Kind**: `change`. It needs the operator to choose among the three options and owes a delta to the platform deploy requirements.

**Waits on**: `nothing`.

**Design with**: `make-a-rotated-grafana-password-reach-grafana`, `perform-the-stack-separation-check-that-was-never-run`, `verify-at-deploy-time-that-what-shipped-is-what-runs`.

**Recorded by**: found 2026-09-16 while closing `give-staging-its-own-dead-mans-switch-check`, by checking whether the fix had landed rather than reading the deploy's result; it is a separate defect in the deploy mechanism.

**Re-checked**: 2026-10-19.

## `perform-the-stack-separation-check-that-was-never-run`

`docs/bootstrap-a-new-host.md` §7.5 asks the operator to confirm the two stacks hold different per-stack secrets (two Grafana logins with different passwords, a test alert arriving in one channel only). It had never been performed; when it was (2026-09-16), production and staging shared the Slack webhook (production's alerts were landing in the staging workspace), the dead-man's-switch URL and the Grafana admin password. All three are now separated (`apply-the-per-stack-alert-routing`, PR #244, 2026-09-16; `give-each-stack-its-own-grafana-password`, 2026-09-17, rotating staging's only), and §7.5 then passed.

What remains is a repeatable check. These are GitHub Environment secrets, invisible to `.github/tests`, Molecule and review; the only defence is a runbook step read once, which is what let three values sit shared for weeks. A probe across the two running hosts is the workable shape, and it needs a home. It must compare what the hosts **accept**, not only what they hold: on 2026-09-17 Grafana held a new password and accepted the old one.

**Kind**: `change`. It needs a decision on where a cross-host probe lives and whether the separation is worth asserting repeatably, and owes a delta for it.

**Waits on**: `nothing`.

**Design with**: `make-a-rotated-secret-reach-its-inline-config`, `make-a-rotated-grafana-password-reach-grafana`, `label-each-stack-s-alerts-with-the-stack-they-came-from`.

**Recorded by**: the rebuild rehearsal's pre-state capture (2026-09-16) during `write-and-rehearse-the-rebuild-runbook`; the three values were fixed as fixes, and the repeatable check is a change of its own.

**Re-checked**: 2026-10-19.

## `decide-whether-the-data-volume-should-survive-a-server-toggle`

Each stack couples its data volume to its server (`count = var.volume_enabled && var.server_enabled ? 1 : 0`), so `server_enabled = false` discards the volume, which has no Hetzner backup; the server's backups reach the root disk only. `add-prod-data-volume`'s design accepted this deliberately. The 2026-09-16 rehearsal showed the apply destroys the volume **first**, before the server. Decoupling would give the volume its own `location` and gate it on `volume_enabled` alone; the cost is not money (tens of cents a month) but the toggle's meaning (`terraform/stacks/main-staging/variables.tf`: `server_enabled` is "the way to stop paying for staging without deleting its configuration").

It is not worth doing while *No Store on This Host Holds Data Requiring Backup* (`openspec/specs/iac-safety-hardening/spec.md`) holds: nothing on the volume is durable. **Must not undo**: when durable data lands on a host, decoupling and a real backup are owed together; decoupling alone looks like protection while protecting against nothing.

**Kind**: `change`. It owes an `iac-safety-hardening`/stack delta and the operator's decision on the toggle's meaning, delivered with a backup.

**Waits on**: durable data landing on a stack's data volume, i.e. a store there that *No Store on This Host Holds Data Requiring Backup* cannot classify as needing no backup.

**Design with**: `exercise-the-volume-server-coupling-against-live-state`.

**Recorded by**: a question during `write-and-rehearse-the-rebuild-runbook`'s rehearsal (2026-09-16), once the destroy had shown what the coupling does; deliberately deferred as not yet worth doing.

**Re-checked**: 2026-10-19.

## `make-a-rotated-grafana-password-reach-grafana`

Rotating `PLATFORM_GRAFANA_ADMIN_PASSWORD` recreates `platform-grafana-1` with the new value and leaves Grafana accepting the old one: `admin_password` is read only when Grafana's database is created, and that database lives on the data volume (`/mnt/main/grafana`). Measured on staging 2026-09-17: deploy green, container `Recreated`, new value in the environment, `/api/user` answered `401`. Every signal is green; the shape that hurts is a rotation after a leak that leaves the leaked credential working. Until it lands, the host step in `docs/bootstrap-a-new-host.md` Appendix A (`grafana cli admin reset-admin-password`) completes a rotation, and the operator confirms a login.

The change owes either a deploy that reconciles the service with the shipped value (smaller for Grafana alone; belongs where the deploy can hold a credential, `app-deploy`) or a post-deploy probe asserting the running service accepts what was shipped. The probe generalises to every credential a service stored once: `PLATFORM_POSTGRES_EXPORTER_PASSWORD` (typed into Postgres at §7.5) and `PLATFORM_POSTGRES_USER`/`_PASSWORD` (used by `initdb` at first boot). It has the same home problem as its siblings: a property of a running host.

**Kind**: `change`. It needs the operator to choose reconcile or probe, and owes a platform deploy delta.

**Waits on**: `nothing`.

**Design with**: `make-a-rotated-secret-reach-its-inline-config`, `perform-the-stack-separation-check-that-was-never-run`, `verify-at-deploy-time-that-what-shipped-is-what-runs`.

**Recorded by**: `give-each-stack-its-own-grafana-password` (2026-09-17), which rotated staging's password and checked a login; fixing the rotation mechanism was outside that fix's scope.

**Re-checked**: 2026-10-19.

## `hold-every-alert-to-naming-what-it-fires-about`

A rule that interpolates `$labels.<L>` into its notification should exclude series where `<L>` is empty. `scope-the-restart-alert-to-real-containers` fixed and asserted this for `ContainerRestartingOrOOMKilled` only (it had sent `Container  is crash-looping` eight times). In `platform/docker-compose.yml`, `ApplicationHighErrorRate` (`by (router)`) and `TLSCertificateExpiringSoon` (`by (cn)`) do not exclude the empty value, and an empty `cn` is known to occur (`CertificateExpiryNotObserved` exists to detect it).

First measure whether either can reach a notification; that decides whether this includes fixing two rules or only adds the guard against the next rule. The guard belongs in the static suite, generalising the reader in `.github/tests/test_the_container_alert_names_a_container.py`. It must decide what counts as excluding the empty value: `sum by (router)` keeps an empty `router` as its own group, so accepting `by (<L>)` as the guard would prove nothing while reading as enforced.

**Kind**: `change`. *Metrics-Based Alerting Covers Host and Service Health* (`openspec/specs/iac-platform-services/spec.md`) states the empty-label obligation for container rules only; generalising it owes a delta.

**Waits on**: `nothing`.

**Design with**: `nothing`.

**Recorded by**: `scope-the-restart-alert-to-real-containers` (archived 2026-09-17), whose subject is one rule; this is a property of all of them.

**Re-checked**: 2026-10-19.

## `check-a-decommissioned-stack-declares-no-converge`

`let-a-stack-opt-out-of-the-converge` lets a stack declare `converges_host: false` in its `pipeline.yml`, declared rather than derived from `server_enabled = false` in `terraform.tfvars` because no workflow reads a `.tfvars` file (its `design.md`, Decision 2). The cost is an interval: a server re-enabled without flipping the declaration back is converged by nothing, and nothing reports it. A `.github/tests` check reading both committed files (a stack with `server_enabled = false` declares `converges_host: false`, and one with `server_enabled = true` or absent does not) closes it statically. `.github/tests/test_a_stack_opts_out_of_the_converge.py` does not read `terraform.tfvars` today.

Decide whether it also covers `deploys_platform`, which the same decommissioning flips. From that change's code review: `platform-deploy.yml` never reads `converges_host`, so `converges_host: false` with `deploys_platform: true` is caught only by `test_the_platform_stack_deploys_per_stack`'s committed-stack assertion and would otherwise fail late against a missing host; and an excluded stack's required fields go unvalidated by requirement, so a static check of an excluded stack's declaration would surface rot before re-enabling rather than in the pull request that re-enables it.

**Kind**: `fix`. A static assertion over two committed files; whether to cover `deploys_platform` is decided within it.

**Waits on**: `nothing`.

**Design with**: `nothing`.

**Recorded by**: `let-a-stack-opt-out-of-the-converge` (archived 2026-10-11), as a separate cross-layer obligation.

**Re-checked**: 2026-10-19.

## `say-production-is-no-longer-reviewer-gated`

On 2026-10-11, at the operator's request, the `main-production` GitHub Environment's required reviewer was removed (its protection rules are empty), so Terraform apply, Host Converge and Platform Deploy run on merge without approval; the Destroy Policy Gate still applies. Committed texts still describe the reviewer as in force: *Gated Production Apply Applies the Reviewed Plan* and its scenario "Merge does not apply immediately" (`openspec/specs/iac-cicd-pipeline/spec.md`), the `github_environment` comment in `terraform/stacks/main-production/pipeline.yml` ("`main-production` requires a reviewer"), `AGENTS.md` ("Prod's apply waits for a human to approve the saved plan"), and `README.md` ("gates every apply behind manual approval"). The change owes a decision record (why an unreviewed production apply is acceptable here, and what bounds it) and the corresponding deltas, not a silent text edit. If the repository were made private on GitHub Free, Environment protection rules and branch protection would stop applying too, which bears on what "gated" can mean; it is public today.

**Kind**: `change`. It owes `iac-cicd-pipeline` deltas and a recorded operator decision.

**Waits on**: `nothing`.

**Design with**: `rename-the-requirements-that-read-narrower-than-they-are`, which renames *Gated Production Apply Applies the Reviewed Plan*.

**Recorded by**: `let-a-stack-opt-out-of-the-converge` (archived 2026-10-11), which declined to fold it in.

**Re-checked**: 2026-10-19.

## `share-the-static-suites-test-arrangement`

The `.github/tests` suite has no shared test arrangement: several modules import helpers from `test_ci_configuration.py`, a test module, so a module that is rewritten for its own reasons breaks others, and a test author has nowhere to take a builder from. Give the suite a support module the tests import from, move those helpers into it, and record its location under *Testing* in `AGENTS.md` as the suite's shared test arrangement. Molecule and `terraform test` have none either; say whether either needs one.

**Kind**: `change`. It decides the project's testing strategy (where shared arrangement lives), which is the operator's decision.

**Waits on**: `nothing`.

**Design with**: `hold-the-whole-static-suite-to-its-own-constraints`, which also changes how that suite's modules read the tree.

**Recorded by**: `sync-ai-toolkit-workflow-v10`, which recorded the shared test arrangement as none when taking ai-toolkit's development-workflow v10; creating one is not a sync.

**Re-checked**: 2026-10-19.

## `remove-commerce-ops-from-production`

`commerce-ops` belongs to the fuperia company and no longer runs on this repository's hosts (operator, 2026-10-19). `main-production` still carries it: its `deploy_apps` entry in `ansible/inventory/host_vars/main-production.yml` (so `/opt/commerce-ops`, its deploy and probe sudoers files and two `authorized_keys` lines), its database and role in the shared PostgreSQL instance, and the passages that describe it: the divergence paragraphs in *No Store on This Host Holds Data Requiring Backup* (`iac-safety-hardening`) and *Single Shared PostgreSQL Instance, Per-Application Databases* (`iac-platform-services`), `docs/runbook-rebuild.md`'s production warning, `platform/README.md` and `docs/onboard-an-application.md`. Take `remove-commerce-ops-from-staging` (archived 2026-10-18) as the shape: delete the entry, clean the host by hand once, rewrite the documents.

**It must not** drop the database before the operator confirms its data is not needed or has been copied out, and must not remove what `fuperia-it/commerce-ops` still deploys to before its own deploy stops targeting this host.

**Kind**: `change`. It owes MODIFIED deltas removing the two specification passages, and the operator's decision on the database's data.

**Waits on**: the operator's word that `commerce-ops`'s production data on this host is not needed or has been copied, and that `fuperia-it/commerce-ops` no longer deploys here.

**Design with**: `revoke-an-application-s-deploy-authorisation`, the mechanism that would make the host clean-up a converge rather than a hand edit.

**Recorded by**: `remove-obsolete-commerce-ops-entries`, which deleted `classify-commerce-ops-production-data-for-the-shared-instance` and `move-commerce-ops-durable-data-to-supabase` once the operator said `commerce-ops` will not be used here; removing it is a change, not a backlog edit.

**Re-checked**: 2026-10-19.
