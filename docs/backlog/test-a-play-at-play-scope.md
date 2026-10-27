---
kind: change
waits_on: []
design_with: []
recorded_by: configure-the-staging-host
re_checked: 2026-10-19
---

`ansible/playbooks/host-baseline.yml` carries a guard play that refuses when the target environment resolves to no host. Nothing tests it: Molecule's subject is a role on a host, and `.github/tests` reads only committed files (`TestEveryModuleInTheSuiteDirectoryNeedsNoPrivilegedResource` would fail a module that ran `ansible-playbook`). So a green pull request only shows the guard is present. One bypass is known and cannot be closed: `--limit` filters `localhost` out of the guard play, so `--limit <host>` against an empty group exits 0; it is stated in the play header and `docs/bootstrap-a-new-host.md`.

A play-scope harness would assert the refusal under each invocation shape, and would also cover role ordering, `when:` on role inclusion, and the deferred play-scope input validation noted above the playbook's role list.

- **Kind**: It adds a fourth test command (a row in `AGENTS.md`'s test-command table) and a runner, which is an operator decision.
- **Recorded by**: `configure-the-staging-host` (`design.md` Decision 10), whose diff needed close reading and was no place to invent a test tier.
