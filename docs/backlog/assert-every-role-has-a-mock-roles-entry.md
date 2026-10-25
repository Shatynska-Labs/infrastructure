---
kind: fix
waits_on: []
design_with: []
recorded_by: bound-host-log-growth-and-add-swap
re_checked: 2026-10-19
---

`.ansible-lint`'s `mock_roles:` hand-lists every role referenced by name, because ansible-lint does not resolve roles through `ansible/ansible.cfg`'s `roles_path`. Nothing asserts the list is complete. A new role under `ansible/roles/` used from `ansible/playbooks/host-baseline.yml` without an entry fails ansible-lint twice (playbook and the role's own `converge.yml`) with a misleading "role not found" naming a search path, which sends the time to the wrong file (observed 2026-09-08 adding `swap`). The cost lands on whoever adds the next role. The check is a static read for `.github/tests`: role directories under `ansible/roles/` minus the gitignored external role, against `mock_roles`. It has the same shape as the "every lockfile-bearing directory is covered" check. The list is complete today.

- **Kind**: A static assertion with no delta or decision.
- **Recorded by**: `bound-host-log-growth-and-add-swap`, which hit the gap and added its missing entry; asserting the invariant was a different concern from that change's subject.
