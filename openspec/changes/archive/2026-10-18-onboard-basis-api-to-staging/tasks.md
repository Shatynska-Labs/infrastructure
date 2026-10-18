## 1. Keys

- [x] 1.1 Obtain the two public halves from the operator: `~/.ssh/shatynska-basis-api-main-staging.pub` (comment `basis-api-deploy-main-staging`) and `~/.ssh/shatynska-basis-api-probe-main-staging.pub` (comment `basis-api-probe-main-staging`), with their `ssh-keygen -lf` fingerprints. Deploy `SHA256:X1Z9HqzOGeQoJT973SR95aUMsgJoPKXIs8C32w/xBfI`, probe `SHA256:CVOuKtkSQoHwdcBmU2IfRoHyFiENzNWCa7T8Jh604e4`.

## 2. Implement

- [x] 2.1 Add the `basis-api` entry to `deploy_apps` in `ansible/inventory/host_vars/main-staging.yml`, after `platform`, with a comment naming the application, its repository (`Shatynska-Labs/basis`) and image (`ghcr.io/shatynska-labs/basis-api`), saying that it has no database yet and that its probe key is declared for the one it will take. Leave every existing entry and comment unchanged.

## 3. Verify

- [x] 3.1 Confirm by fingerprint that each committed key equals the fingerprint in 1.1, that the two differ, and that neither equals any other key in the file or in `main-production.yml`.
- [x] 3.2 `openspec validate --all --strict` passes.
- [x] 3.3 `python3 -m unittest discover --start-directory .github/tests` passes from the repository root.
- [x] 3.4 `ansible-lint` and `ansible-playbook --syntax-check -e target_environment=syntax-check-only playbooks/host-baseline.yml` pass.
- [x] 3.5 No Molecule scenario is owed: no role changes.

## 4. Ship

- [x] 4.1 Open the pull request; let CI run. PR #277.
- [x] 4.2 The operator merges it; `host-converge.yml` converges `main-staging` without a gate. Merged as `4ce4f80` on 2026-10-18.
- [x] 4.3 The operator confirms the converge on `main-staging` succeeded. `host-converge.yml` run 39163510580, `converge (main-staging)` success; `deploy_user` reported `changed` for `item=basis-api` on all five per-application tasks.

## 5. Confirm the effect

- [x] 5.1 On the host: `ls -ld /opt/basis-api` shows `deploy:deploy`, mode `0750`; `/etc/sudoers.d/app-deploy-basis-api` and `/etc/sudoers.d/app-probe-basis-api` exist and name `basis-api` with no wildcard; the deploy account's `authorized_keys` carries one `deploy-receive basis-api` line and one probe line, each on the key fingerprinted at 1.1.

  **Observed 2026-10-18.** As `ops-claude` (`ssh shatynska-main-staging`): `drwxr-x--- 2 deploy deploy 4096 Oct 18 20:33 /opt/basis-api`, its timestamp the converge's. The root half was not read on the host; the sudoers rules and `authorized_keys` entries rest on 4.3's converge log.
- [x] 5.2 Tell the operator that basis#21 can merge, and that its first staging deploy is also the proof the host can pull the private image. Told on 2026-10-18; the deploy (basis run 39165383089) succeeded and `basis-api-api-1` was `Up (healthy)` on `main-staging`, so the private image pulled.

## 6. Archive

- [x] 6.1 Bring the branch back to the freshly fetched trunk, commit the change's record, and open its own pull request.
