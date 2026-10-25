---
kind: change
waits_on: []
design_with: []
recorded_by: decide-archived-change-reference-policy
re_checked: 2026-10-19
---

Source comments mix three kinds of text with no way to tell them apart: why the code is shaped this way (keep), what a past change did (git and the archive own it), and TODOs whose condition has passed (dead and misleading). A pass should leave only the first. The ratio is worst in `ansible/roles/tailscale/tasks/main.yml` (140 comment lines of 197 non-blank, up from 48 of 90), a maintenance cost rather than a cosmetic one.

- **Must not undo**: load-bearing rationale such as the tailnet polarity note in `ansible/roles/tailscale/tasks/main.yml` and the `ghcr_pull_*` tolerated/not-tolerated block in `ansible/roles/deploy_user/tasks/main.yml`. The two instances this entry once named (`terraform/stacks/main-production/ssh_key.tf`'s `moved` block, `main.tf`'s `delete_protection` parenthetical) were taken as fixes on 2026-09-15; the pass needs instances of its own. The citation-form decision it used to wait on was delivered by `decide-archived-change-reference-policy` (archived 2026-09-07).
- **Kind**: A repository-wide pass is too large for one review sitting, and the rule for what a comment may hold needs the operator's decision and a home in `AGENTS.md`.
- **Recorded by**: `unknown`; it was unblocked by `decide-archived-change-reference-policy`, which changed citation form only and deliberately left the surrounding prose alone.
