---
kind: change
waits_on: []
waits_for: "a second application holding a database in a shared instance (`basis-api` holds the only one today), or a rebuild performed by someone other than the operator who would otherwise send the message."
design_with: []
recorded_by: write-and-rehearse-the-rebuild-runbook
re_checked: 2026-10-27
---

*The Host Carries an Operator-Declared Maintenance Window for the Shared Instance* (`openspec/specs/iac-host-configuration/spec.md`) lets applications read `window-open` from `/var/lib/platform-maintenance/shared-postgres-window` during a destructive act on the shared instance. It cannot announce a rebuild, because the declaration lives on the host the rebuild destroys: the probe gets no answer, which is exactly the state of a host that has fallen over, so an application cannot tell the two apart when it matters most.

The change owes a decision on who the audience is and where such a declaration lives: off the host (a repository variable, status page, or field the application's deploy reads) survives the rebuild but needs a second mechanism; on the host but restored early closes only part of the window; out-of-band to operators is not machine-readable. Today `docs/runbook-rebuild.md` says the alarms are expected and asks the operator to tell each application's owner by hand. Staging holds no database-bearing application since `remove-commerce-ops-from-staging` (archived 2026-10-18); `basis-api` holds each host's only shared-instance database, probed through its `probe_public_key`; production's moves to `basis-api`'s own container on the data volume (`record-basis-api-durable-store`, then Basis's `move-to-durable-data-storage`), after which `finish-basis-api-s-move-to-its-own-database` retires production's shared-instance database and probe key.

- **Kind**: It needs the operator's decision on audience and location, and owes an `iac-host-configuration` delta.
- **Recorded by**: planning `write-and-rehearse-the-rebuild-runbook` (2026-09-16), which found the gap; it was not a blocker on the runbook because a rebuild is operator-initiated and can be announced by hand.
