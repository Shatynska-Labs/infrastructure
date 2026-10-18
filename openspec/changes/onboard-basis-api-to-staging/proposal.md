## Why

`Shatynska-Labs/basis` is moving its API deploys to staging-first with operator promotion, in its change `move-api-deploys-to-staging-with-promotion` (pull request Shatynska-Labs/basis#21). Its staging deploy job reaches `deploy@<MAIN_STAGING_DEPLOY_HOST>` over the tailnet as `tag:ci` and cannot authenticate until a `basis-api` entry in `deploy_apps` is merged and converged on `main-staging`. Per `docs/onboard-an-application.md` §2.2 the application repository waits on this pull request, never the reverse, so basis#21 is held unmerged until this lands. This is the staging counterpart of the archived change `onboard-basis-api-to-production`.

## What Changes

- Add a `basis-api` entry to `deploy_apps` in `ansible/inventory/host_vars/main-staging.yml`, after `platform`, with a comment in the shape production's `basis-api` entry carries: what the application is, its repository and its image, and that it has no database yet.
  - `public_key`: the deploy key, comment `basis-api-deploy-main-staging`, fingerprint `SHA256:X1Z9HqzOGeQoJT973SR95aUMsgJoPKXIs8C32w/xBfI`; private half at `~/.ssh/shatynska-basis-api-main-staging` on the operator's workstation.
  - `probe_public_key`: the probe key, comment `basis-api-probe-main-staging`, fingerprint `SHA256:CVOuKtkSQoHwdcBmU2IfRoHyFiENzNWCa7T8Jh604e4`; private half at `~/.ssh/shatynska-basis-api-probe-main-staging`. Declared although Basis has no database yet, because `.github/tests/test_a_shared_instance_reset_is_visible.py` fails any `deploy_apps` entry without one, and Basis will take a database later.
- Staging's own keypairs, not production's. The other entries are left as they are.

No role, playbook, template, workflow or document changes.

## Capabilities

### New Capabilities

None.

### Modified Capabilities

None — `skip_specs: true`. The mechanism that turns a `deploy_apps` entry into `/opt/<name>`, a forced-command `authorized_keys` line and a `sudoers` rule is already specified as *Restricted Deploy Account Supports Per-Application Forced-Command Deploys* (`openspec/specs/iac-host-configuration/spec.md`); this change gives it one more input.

## What the application will deliver, for whoever reads the host later

Basis's staging deploy job sends the forced command the same gzip tar as production's: `docker-compose.yml` and an `.env` holding `IMAGE_DIGEST` and `ROUTER_RULE`. The image is pinned by digest, `ghcr.io/shatynska-labs/basis-api@sha256:…` — two path segments, the last equal to the entry's name, as §1 requires for image reclamation. Traefik routes `basis-api.main-staging.<BASE_DOMAIN>` on `platform_edge`, port 3000, under staging's server wildcard, so no DNS record of its own is needed.

## GHCR pull

`ghcr_pull_username: shatynska` and a vault-encrypted `ghcr_pull_token` are set in `ansible/inventory/group_vars/staging.yml`, and production's `group_vars/production.yml` carries the same username with its own token. `staging.yml` says the token is "the same account production uses", `read:packages` against the same packages. A classic personal access token follows the account's access, so if production's pulls the private `basis-api` package, staging's should. That cannot be proven from the repository: the tokens are vault-encrypted and the converge stays green whichever way it goes (`ansible/roles/deploy_user/README.md`, *GHCR pull authentication*). The first staging deploy is the proof; if it is denied, the operator must grant the `shatynska` account read access to the `basis-api` package (§2.3).

## Operator steps outside this repository

- Merge, then approve nothing: staging's GitHub Environment requires no reviewer, so `host-converge.yml` converges `main-staging` without a gate.
- Basis#21's Environment secrets (the private deploy key, `MAIN_STAGING_DEPLOY_HOST`) are set in that repository.

## Impact

- `ansible/inventory/host_vars/main-staging.yml`: one entry and its comment.
- On merge, `host-converge.yml` runs on `ansible/**` and creates `/opt/basis-api`, the deploy and probe `authorized_keys` lines and the `sudoers` rules for `basis-api` on `main-staging`.
- After the converge succeeds, basis#21 can merge.
