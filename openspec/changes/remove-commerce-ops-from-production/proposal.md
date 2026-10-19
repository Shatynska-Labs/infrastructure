## Why

`commerce-ops` belongs to the fuperia company and will no longer run on this repository's hosts (the operator, 2026-10-19). Its own repository deploys to fuperia's servers: `Fuperia-IT`'s `MAIN_PRODUCTION_DEPLOY_HOST` is a different address from this organisation's. `remove-commerce-ops-from-staging` took it off `main-staging` on 2026-10-18 and deliberately left `main-production` alone.

Read from `main-production` as `ops-claude` on 2026-10-19, nothing of the application is running: no `commerce-ops` container, no volume, and no `commerce-ops` database or role in the shared PostgreSQL instance, whose databases are `platform_admin`, `postgres` and the templates and whose roles are `platform_admin` and `pgexporter`. The host still authorises it, though. Its `deploy_apps` entry in `ansible/inventory/host_vars/main-production.yml` keeps `/opt/commerce-ops`, `/etc/sudoers.d/app-deploy-commerce-ops`, `/etc/sudoers.d/app-probe-commerce-ops` and two `authorized_keys` lines on the `deploy` account, for keys whose private halves sit in another company's GitHub Environment.

The repository also still describes a store that no longer exists. *No Store on This Host Holds Data Requiring Backup* records `commerce-ops`'s own PostgreSQL on production as an unmet divergence, and the rebuild runbook, the onboarding guide and `platform/README.md` repeat it as a warning, or describe a production database reserved for a cutover.

## What Changes

- **The `commerce-ops` entry is deleted from `ansible/inventory/host_vars/main-production.yml`**, with the comments that describe it.
- **The host is cleaned by hand, once, after the merge's converge**, as `remove-commerce-ops-from-staging` did: the two sudoers files, `/opt/commerce-ops` and the two `authorized_keys` lines. `deploy_user` removes nothing for an entry that is gone. There is no container, volume or database to remove.
- **The divergence is deleted from *No Store on This Host Holds Data Requiring Backup***. The scenario that stopped it being read as a precedent keeps its title and states the rule without naming an application. The requirement then describes every store this host holds.
- **The documents stop describing `commerce-ops` on production.**
  - `docs/runbook-rebuild.md` loses its production warning.
  - Its phase 14 no longer says production carries `commerce-ops`.
  - Its phase 15's workflow-trigger aside and its `/health` example name no application.
  - `docs/onboard-an-application.md` loses its production-divergence paragraph.
  - `platform/README.md` no longer describes a database reserved for a cutover.
  - `docs/bootstrap-a-new-host.md` no longer says both `host_vars` files carry a `commerce-ops` entry.
- **`.github/tests/test_the_rebuild_runbook_records_its_rehearsal.py` stops requiring the runbook to name `commerce-ops`.** It hard-codes the requirement's one unmet store; after this change the requirement records none.
- **`docs/backlog.md`**: `revoke-an-application-s-deploy-authorisation` records a second hand clean-up, and `remove-commerce-ops-from-production` is deleted at the archive.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `iac-safety-hardening`: *No Store on This Host Holds Data Requiring Backup* loses its stated divergence, and its scenario *The stated divergence is not a precedent* no longer names `commerce-ops`.

## Non-Goals

- **A revocation mechanism for `deploy_apps`.** It stays `revoke-an-application-s-deploy-authorisation`. One more hand clean-up on a host holding no data of the application's is the same judgement `remove-commerce-ops-from-staging` made.
- **The divergence in *Single Shared PostgreSQL Instance, Per-Application Databases*** (`iac-platform-services`). It records that manual provisioning is owed automation, which is still true. It names `commerce-ops` as the application that fired the trigger on 2026-09-13, which is history, and a test requires it.
- **`commerce-ops` as the onboarding guide's worked example**, and other historical sentences naming it. They describe what happened or use it as an example name.
- **`Fuperia-IT/commerce-ops` and its GitHub Environments.** That repository's to change; its deploys already target another host.

## Impact

- `ansible/inventory/host_vars/main-production.yml`. The converge on merge leaves the host as it was, since `deploy_user` removes nothing; the hand clean-up follows.
- `openspec/specs/iac-safety-hardening/spec.md`, through the delta.
- `docs/runbook-rebuild.md`, `docs/onboard-an-application.md`, `docs/bootstrap-a-new-host.md`, `platform/README.md`, `docs/backlog.md`.
- `.github/tests/test_the_rebuild_runbook_records_its_rehearsal.py`.
