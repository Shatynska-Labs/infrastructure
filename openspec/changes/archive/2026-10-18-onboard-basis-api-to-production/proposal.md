## Why

`Shatynska-Labs/basis` has its first deployable application, `basis-api` — a NestJS API serving only `GET /health` today — in its pull request #17 (change `deploy-api-skeleton`), CI green. Its deploy follows `docs/onboard-an-application.md` §4.4 and cannot authenticate to the production host until a `basis-api` entry in `deploy_apps` is merged and converged here. Per §2.2 the application repository waits on this pull request, never the reverse, so basis PR #17 is held unmerged until this lands.

## What Changes

- Add a `basis-api` entry to `deploy_apps` in `ansible/inventory/host_vars/main-production.yml`, after `portfolio`, with a comment in the shape the `portfolio` entry carries: what the application is, its repository and its image, and that it has no database yet.
  - `public_key`: the deploy key, comment `basis-api-deploy-main-production`; private half at `~/.ssh/shatynska-basis-api-main-production` on the operator's workstation.
  - `probe_public_key`: the probe key, comment `basis-api-probe-main-production`; private half at `~/.ssh/shatynska-basis-api-probe-main-production`. Declared although Basis has no database yet, because Basis will take one in the shared instance later — the role and database `basis-api`, named after the application as `docs/onboard-an-application.md` §3.2 requires, which is what this probe reads — and declaring it now saves a second converge. `.github/tests/test_a_shared_instance_reset_is_visible.py` also fails any `deploy_apps` entry without a `probe_public_key`, so the entry needs one regardless. Until then it can only answer `absent`, as `portfolio`'s and `shatynskyj`'s do. Basis's workflow does not call the probe yet.
- **`main-production` only.** Staging is switched off by the operator, so `main-staging.yml` gets no entry.
- **Not `group_vars/production.yml`** — *A Host-Scoped Variable Lives in the Host's Own Vars File* (`openspec/specs/iac-host-configuration/spec.md`).

No role, playbook, template, workflow or document changes. The existing entries and their comments, including `platform`'s deliberate probe key, are left as they are.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

None — `skip_specs: true`. The mechanism that turns a `deploy_apps` entry into `/opt/<name>`, a forced-command `authorized_keys` line and a `sudoers` rule is already specified as *Restricted Deploy Account Supports Per-Application Forced-Command Deploys* (`openspec/specs/iac-host-configuration/spec.md`) and implemented by `deploy_user`; this change gives it one more input. An enumerated application that has not yet deployed is already covered by *Unreferenced Host Images Are Pruned on a Schedule* in the same file.

## What the application will deliver, for whoever reads the host later

basis's `deploy.yml` sends the forced command a gzip tar holding `docker-compose.yml` and an `.env` holding only `IMAGE_TAG`, as `deploy@$DEPLOY_HOST` over the tailnet from a runner tagged `tag:ci`. `app-deploy` then runs `docker compose pull && docker compose up -d --wait` in `/opt/basis-api`. The Compose file defines one service, `api`, on the external `platform_edge` network, routed by Traefik as `basis-api` on ``Host(`api.basis.shatynska.com`)`` to port 3000 with TLS from the `websecure` default; a healthcheck on `/health`; `read_only: true`, `cap_drop: [ALL]`, `no-new-privileges`, `mem_limit: 512m`, `init: true`; no volume and no bind mount. The container is expected as `basis-api-api-1`. The image is `ghcr.io/shatynska-labs/basis-api:<commit sha>` — two path segments, the last equal to the entry's name, as §1 requires for image reclamation. No `latest` tag is pushed.

## The store, which this change does not bring

*No Store on This Host Holds Data Requiring Backup* (`openspec/specs/iac-safety-hardening/spec.md`) has nothing to classify here: the application persists nothing on the host.

On 2026-10-17 the operator decided that, until Basis decides where its durable data lives (`basis` `docs/backlog.md` `choose-durable-data-storage`), Basis takes a database in production's shared PostgreSQL instance and treats everything it holds there as data whose loss is tolerable. That database is **not** part of this change. The later change that provisions it records the classification, as `docs/onboard-an-application.md` §3.1 requires. The probe key declared here does not imply that a database exists.

## Operator steps outside this repository

- **DNS.** `api.basis.shatynska.com` is outside every server wildcard, so it needs an `A` record of its own pointing at main-production's address (§5), created by the operator at the registrar. Nothing in this repository depends on it before the application deploys. Until it exists the deploy is still reachable over the tailnet (§6).
- **GHCR.** The `basis-api` package is created by the application's first push, and organisation packages may start private. If the first `docker compose pull` on the host is denied, make the package readable by the GHCR user the host authenticates as (§2.3).

## Impact

- `ansible/inventory/host_vars/main-production.yml`: one entry and its comment.
- On merge, `host-converge.yml` runs on `ansible/**`. Production's converge waits for the operator's approval and **nothing announces that it is waiting**. It creates `/opt/basis-api`, the deploy and probe `authorized_keys` lines, and the `sudoers` rules for `basis-api`.
- After the converge succeeds, basis PR #17 can merge.
