---
kind: change
waits_on: []
design_with: [notice-a-pending-reboot-and-decide-what-does-it]
re_checked: 2026-10-19
---

`platform/README.md`'s *Upgrading the PostgreSQL major version* asks the operator to hold every other `platform/**` merge and every `platform-deploy.yml` dispatch for the length of the window. Nothing enforces it, and the failure is silent: step 2 leaves the host without the `postgres` container its Compose definition declares, so any platform deploy landing in the gap (an unrelated merge, or the rebuild dispatch in `docs/runbook-rebuild.md`) recreates it on the **old** major with an empty cluster, undoing step 2 without an error. The window's own pull request is already gated (opened as a draft, marked ready only once the store is cleared); a draft gates only itself.

The class is wider than PostgreSQL: the platform stack is deployed wholesale on every merge, so any window that leaves the host deliberately out of step with the committed definition can be undone by a deploy. `platform-deploy.yml`'s per-stack `concurrency` group serialises deploys but does not refuse one. A refusal needs state that outlives a run (a repository variable, an issue label, a file on the host, an Environment gate); the design must cover a window abandoned half-way and say what a held merge does: queue and land unwatched at release, or fail loudly and be re-run.

- **Kind**: It needs operator decisions: where the lock lives, who releases it, and whether a held deploy queues or fails.
- **Design with**: `notice-a-pending-reboot-and-decide-what-does-it`, whose automatic-reboot policy is a scheduled outage that this mechanism would keep a deploy out of.
- **Recorded by**: the 2026-09-15 work that gated the window's own pull request with a draft (change name not recorded); that half was a fix, this half needs a mechanism and decisions.
