# Handoff: onboard-basis-api-to-production

## Why this change was identified

`Shatynska-Labs/basis` is building its first deployable, `basis-api` — a NestJS API that today serves only `GET /health` — under its change `deploy-api-skeleton` (branch `deploy-api-skeleton` in that repository; read its `openspec/changes/deploy-api-skeleton/` proposal and design). Its deploy job follows `docs/onboard-an-application.md` §4.4, and cannot authenticate to the production host until a `basis-api` entry in `deploy_apps` has been merged and converged here (§2.2: "an application repository that is ready first waits on an infrastructure pull request — never the reverse"). This change is that entry.

## What bears on it

- **Target:** `main-production` only. Staging is switched off by the operator; no staging entry.
- **Name:** `basis-api`. Image `ghcr.io/shatynska-labs/basis-api:<sha>` — exactly two path segments, the last equal to the name (§1).
- **Host file:** `ansible/inventory/host_vars/main-production.yml`, never `group_vars/production.yml` (§2.2).
- **Keys:** the operator generates them on their workstation, into `~/.ssh/`, never into a checkout (§2.1): deploy key comment `basis-api-deploy-main-production`; a probe key, comment `basis-api-probe-main-production`, declared as `portfolio`'s and `shatynskyj`'s are although the application has no database yet — Basis will take a database in the shared instance later (below), and declaring it now saves a second converge. The public halves are not known to the session that opened this; ask the operator for them.
- **Hostname:** `api.basis.shatynska.com`, outside the server wildcard, so a DNS `A` record of its own (§5), created by the operator at the registrar.
- **No store today:** the Compose file (`deploy/api/docker-compose.yml` in `basis`) persists nothing — no volume, no writable bind mount, `read_only: true` — so *No Store on This Host Holds Data Requiring Backup* has nothing to classify in this change.
- **Database later, and its classification:** the operator decided on 2026-10-17 that, until Basis decides where its durable data lives (`basis` `docs/backlog.md` `choose-durable-data-storage`), Basis takes a database in production's shared PostgreSQL instance and treats everything it holds there as data whose loss is tolerable. That is **not** part of this change: the change here that provisions Basis's database records that classification, as §3.1 requires. Mention it only so this change does not imply otherwise.

## What it must not undo

- The existing `deploy_apps` entries and their comments, including `platform`'s deliberate probe key.
- The host-axis placement of application keys (*A Host-Scoped Variable Lives in the Host's Own Vars File*).
- On merge, `host-converge.yml` runs and production's converge waits for the operator's approval; nothing announces that it is waiting.
