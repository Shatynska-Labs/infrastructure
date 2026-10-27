---
kind: change
waits_on: []
design_with: [cover-the-unwatched-manifests-and-settle-the-watcher]
recorded_by: open-autoupdate-pr-with-app-token
re_checked: 2026-10-19
---

`ansible/requirements.yml` pins `hetzner.hcloud` 7.0.0 and `geerlingguy.docker` 8.0.0 (current on 2026-09-08). Three collections are at least a major behind: `community.general` 9.5.0 (13.4.0 available then), `ansible.posix` 1.6.2 (2.2.2), `community.docker` 4.1.0 (5.3.0). Dependabot has no `ansible-galaxy` ecosystem, so nothing proposes bumps here. Used by `hardening` (`community.general.ufw`), `deploy_user` (`ansible.posix.authorized_key` `key_options`, `community.docker.docker_login`), `swap` (`ansible.posix.mount`, `ansible.posix.sysctl`) and the dynamic inventory. Molecule is the gate: run `molecule test --all` per role and read the SCENARIO RECAP, not the exit code. `ansible-core` (pinned in `ansible/requirements-test.txt` and `ansible/requirements.txt`) and these collections were verified together as a set. The "confirm it resolves" caveats were removed on 2026-09-15; the manifest header records the 2026-09-08 confirmation.

- **Kind**: A multi-major migration across several collections, too large for one review sitting.
- **Design with**: `cover-the-unwatched-manifests-and-settle-the-watcher`, since `ansible-core` and the collections are a matched set and a bot bump of one landing mid-migration would confuse which half broke.
- **Recorded by**: an inventory taken while archiving `open-autoupdate-pr-with-app-token` (2026-09-08); a migration was not a rider on that archive.
