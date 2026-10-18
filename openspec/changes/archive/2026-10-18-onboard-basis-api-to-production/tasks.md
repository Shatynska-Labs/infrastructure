## 1. Keys

- [x] 1.1 Obtain the two public halves from the operator: `~/.ssh/shatynska-basis-api-main-production.pub` (comment `basis-api-deploy-main-production`) and `~/.ssh/shatynska-basis-api-probe-main-production.pub` (comment `basis-api-probe-main-production`), with their `ssh-keygen -lf` fingerprints. Deploy `SHA256:5Fa1AlbDvEujxc93OXrrdXIvpJ2INvR6YCVbZVrM0jE`, probe `SHA256:rmfPSo2axnkzkbNgwSoQFnoc5UNuUz5Q1bi9hxFzajk`.

## 2. Implement

- [x] 2.1 Add the `basis-api` entry to `deploy_apps` in `ansible/inventory/host_vars/main-production.yml`, after `portfolio`, with a comment naming the application, its repository (`Shatynska-Labs/basis`) and image (`ghcr.io/shatynska-labs/basis-api`), saying that it has no database yet and that its probe key is declared for the one it will take in the shared instance. Leave every existing entry and comment unchanged.

## 3. Verify

- [x] 3.1 Confirm by fingerprint that each committed key equals the operator-supplied fingerprint, that the two differ, and that neither equals any other key in the file. Done: both match, and all ten keys in the file are distinct.
- [x] 3.2 `openspec validate --all --strict` passes.
- [x] 3.3 `python3 -m unittest discover --start-directory .github/tests` passes from the repository root — 1600 tests, OK.
- [x] 3.4 `ansible-lint` and `ansible-playbook --syntax-check -e target_environment=syntax-check-only playbooks/host-baseline.yml` pass — the syntax check from `ansible/`, ansible-lint as the pinned `pre-commit` hook (v26.9.0) with `--all-files` from the repository root.
- [x] 3.5 No Molecule scenario is owed: no role changes.

## 4. Ship

- [x] 4.1 Open the pull request; let CI run. PR #271; `validate`, `ansible-verify` and both `discover` jobs passed, `plan` and `molecule` skipped — the narrow triggers, correct for a diff touching no role and no Terraform.
- [x] 4.2 The operator merges it and approves production's converge in `host-converge.yml`, which waits without announcing it. Merged as `987e7e0` on 2026-10-18.
- [x] 4.3 The operator confirms the converge on `main-production` succeeded. `host-converge.yml` run 39126844523, `converge (main-production)` success; `deploy_user` reported `changed` for `item=basis-api` on all five per-application tasks — the `/opt/<name>` directory, the `app-deploy` and `app-probe` sudoers rules, and the deploy and probe `authorized_keys` entries.

## 5. Confirm the effect

- [x] 5.1 On the host, in two logins, because `ops-claude` has no `sudo` (`ansible/roles/ops_user/README.md`). As `ops-claude` (`ssh shatynska-main-production`): `ls -ld /opt/basis-api` shows the directory, `deploy:deploy`, mode `0750`. As the operator, with root: `/etc/sudoers.d/app-deploy-basis-api` and `/etc/sudoers.d/app-probe-basis-api` exist and name `basis-api` with no wildcard, and the deploy account's `authorized_keys` carries one `deploy-receive basis-api` line and one probe line, each on the key fingerprinted at 3.1. The converge log from 4.3 is the same evidence read from CI.

  **Observed 2026-10-18.** As `ops-claude`: `drwxr-x--- 2 deploy deploy 4096 Oct 18 12:23 /opt/basis-api`, its timestamp the converge's. The root half was not read on the host; the sudoers rules and `authorized_keys` entries rest on 4.3's converge log, which this task names as the same evidence.
- [x] 5.2 Tell the operator that basis PR #17 can merge. Told on 2026-10-18, after 5.1.

## 6. Archive

- [x] 6.1 Bring the branch back to the freshly fetched trunk, commit the change's record, and open its own pull request.
