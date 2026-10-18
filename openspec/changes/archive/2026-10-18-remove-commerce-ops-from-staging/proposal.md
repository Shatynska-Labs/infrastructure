## Why

`main-staging` was re-enabled on 2026-10-18 for a project other than `commerce-ops`, which belongs to the fuperia company. The rebuilt host was nevertheless converged with `ansible/inventory/host_vars/main-staging.yml`'s `commerce-ops` entry in `deploy_apps`, so it carries that application's `/opt/commerce-ops`, its `/etc/sudoers.d/app-deploy-commerce-ops` and `/etc/sudoers.d/app-probe-commerce-ops`, and two `authorized_keys` lines on the `deploy` account — one for its deploy key and one for its probe key. Its database was deliberately not re-provisioned and its deploy was not re-run, so nothing else of it exists on the host.

## What Changes

- **The `commerce-ops` entry is deleted from `ansible/inventory/host_vars/main-staging.yml`**, with the comments that describe it. `platform` is then the host's one application.
- **The host is cleaned by hand, once.** `deploy_user` removes nothing for an entry that is gone, so the three artefacts above stay. The operator removes them over SSH; `design.md` Decision 1 gives why no revocation mechanism is built for it.
- **`docs/runbook-rebuild.md` stops assuming `commerce-ops` is staging's application.** The `commerce-ops` probes in phases 1 and 16, the database and deploy steps naming it in phases 14 and 15, and the phase 9 sentence naming its `staging` Environment are rewritten to describe a host whose applications are enumerated from `deploy_apps`, and phase 14 says that staging currently holds no database-bearing application.
- **`docs/onboard-an-application.md` stops citing staging's `commerce-ops` entry as a committed one** (the comment-convention paragraph and the staging statements in the cell and database sections); its worked-example role is unchanged.
- **The backlog entry `remove-commerce-ops-from-staging` is deleted** in this change's archive commit, as `docs/backlog.md` prescribes for an entry that has been taken up.

## Non-Goals

- **A revocation mechanism for `deploy_apps`.** It is the backlog entry `revoke-an-application-s-deploy-authorisation`, stays there, and is not a prerequisite — `design.md` Decision 1.
- **`commerce-ops` on `main-production`.** Untouched; its entry, runbook warning and specification passages stay.
- **`fuperia-it/commerce-ops`'s `staging` Environment and Deploy workflow target.** That repository's to change. Its `DEPLOY_HOST` already names a decommissioned address, so its staging deploy fails at the tailnet connection today; this change records the follow-up and cannot make it.
- **Historical passages** in `openspec/specs/` and the archive that name `commerce-ops` on staging as the first shared-instance database. They record what happened.

No specification delta: nothing a requirement states changes, only which application one host's inventory enumerates.

The branch and working tree are removed after this record's own pull request merges, which is after the commit that writes `tasks.md`, so those steps are recorded here in prose rather than as tasks.
