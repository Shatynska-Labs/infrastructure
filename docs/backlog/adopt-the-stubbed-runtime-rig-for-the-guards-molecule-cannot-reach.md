---
kind: fix
waits_on: []
design_with: []
recorded_by: prune-unreferenced-host-images-periodically
re_checked: 2026-10-19
---

Two guards in the `image_prune` role are unasserted: local images are enumerated before the keep set is computed, and each tag is re-resolved immediately before removal. Both are observable only when the host's images change mid-run, which a black-box Molecule scenario has no seam for, and they are the guards facing `app-deploy`, the only concurrent actor. The two abandon branches that change's review fix added are likewise unasserted (the `abandon-paths` scenario covers the design's three, not these).

That change's code review built a rig, a stubbed `docker` on `PATH` answering some calls and failing others, which showed both guards mutation-visible and reproduced the fail-open the review found. Its `test-plan.md` (archive `2026-09-08-prune-unreferenced-host-images-periodically`) invites adding a deterministic ("sized rather than slept") arrangement to `tasks.md` 2.7/2.8.

- **Kind**: Tests for behaviour already specified, with no delta or decision.
- **Recorded by**: `prune-unreferenced-host-images-periodically`'s code review, which built the rig only to verify, not to ship.
