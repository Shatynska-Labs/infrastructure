## 1. Keys

- [x] 1.1 Obtain the two public halves from the operator: `~/.ssh/shatynska-basis-api-main-staging.pub` (comment `basis-api-deploy-main-staging`) and `~/.ssh/shatynska-basis-api-probe-main-staging.pub` (comment `basis-api-probe-main-staging`), with their `ssh-keygen -lf` fingerprints. Deploy `SHA256:X1Z9HqzOGeQoJT973SR95aUMsgJoPKXIs8C32w/xBfI`, probe `SHA256:CVOuKtkSQoHwdcBmU2IfRoHyFiENzNWCa7T8Jh604e4`.

## 2. Implement

- [ ] 2.1 Add the `basis-api` entry to `deploy_apps` in `ansible/inventory/host_vars/main-staging.yml`, after `platform`, with a comment naming the application, its repository (`Shatynska-Labs/basis`) and image (`ghcr.io/shatynska-labs/basis-api`), saying that it has no database yet and that its probe key is declared for the one it will take. Leave every existing entry and comment unchanged.

## 3. Verify

- [ ] 3.1 Confirm by fingerprint that each committed key equals the fingerprint in 1.1, that the two differ, and that neither equals any other key in the file or in `main-production.yml`.
- [ ] 3.2 `openspec validate --all --strict` passes.
- [ ] 3.3 `python3 -m unittest discover --start-directory .github/tests` passes from the repository root.
- [ ] 3.4 `ansible-lint` and `ansible-playbook --syntax-check -e target_environment=syntax-check-only playbooks/host-baseline.yml` pass.
- [ ] 3.5 No Molecule scenario is owed: no role changes.

## 4. Ship

- [ ] 4.1 Open the pull request; let CI run.
- [ ] 4.2 The operator merges it; `host-converge.yml` converges `main-staging` without a gate.
- [ ] 4.3 The operator confirms the converge on `main-staging` succeeded.

## 5. Confirm the effect

- [ ] 5.1 On the host: `ls -ld /opt/basis-api` shows `deploy:deploy`, mode `0750`; `/etc/sudoers.d/app-deploy-basis-api` and `/etc/sudoers.d/app-probe-basis-api` exist and name `basis-api` with no wildcard; the deploy account's `authorized_keys` carries one `deploy-receive basis-api` line and one probe line, each on the key fingerprinted at 1.1.
- [ ] 5.2 Tell the operator that basis#21 can merge, and that its first staging deploy is also the proof the host can pull the private image.

## 6. Archive

- [ ] 6.1 Bring the branch back to the freshly fetched trunk, commit the change's record, and open its own pull request.
