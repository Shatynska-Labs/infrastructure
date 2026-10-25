---
kind: change
waits_on: []
design_with: []
recorded_by: rename-terraform-environments-to-stacks
re_checked: 2026-10-19
---

`host-converge.yml` triggers on any merge touching `ansible/**`, so comment-only and test-fixture changes converge both hosts (`changed=0`), three times observed: PR #148 (2026-09-12), PR #161 (2026-09-13, Molecule fixtures only, which held a production approval open 6h34m), and PR #210 (2026-09-15, a comment-only `requirements.yml`/`requirements.txt` diff). A converge changes the firewall, logins and container runtime; relying on idempotency is weaker than not running.

It is not a copy of `narrow-the-molecule-trigger-to-what-it-reads`: the exclusion sets are near inverses. A converge reads the inventory, `group_vars`, `host_vars`, the playbooks and every role's `tasks/`, `defaults/`, `handlers/`, `templates/`, `meta/`, so all of those stay. The safe exclusions are roughly documentation (`**/README.md`), `.envrc*`, and Molecule scenario directories plus `ansible/scripts/run-molecule`.

Must not: let a host silently not converge. Getting this filter wrong reports green while a host keeps its old firewall. Keep the exclusion list conservative, use the `some-with-excludes` discipline `ansible-verify.yml` documents, and add a `.github/tests` assertion that every path a converge reads is not excluded. A reviewer may legitimately keep the coarse trigger because the failure mode is silent.

- **Kind**: It owes an `iac-cicd-pipeline` delta for the converge trigger and needs a decision that narrowing is worth the silent-failure risk.
- **Recorded by**: the session that merged `rename-terraform-environments-to-stacks` (PR #148) on 2026-09-12; outside that change's subject.
