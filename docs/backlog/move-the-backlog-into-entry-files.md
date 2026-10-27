---
kind: change
waits_on: []
design_with: []
recorded_by: "ai-toolkit's one-file-per-backlog-entry"
---

Convert `docs/backlog.md` into `docs/backlog/`, one file per entry with YAML frontmatter, the shape ai-toolkit's development workflow v12 and its `backlog` skill now read, using ai-toolkit's `scripts/backlog-migrate`. The conversion itself is mechanical. What is not mechanical is the file's path, which this repository has made load-bearing: two requirements, *iac-host-configuration* and *iac-platform-services*, cite entries as "tracked in `docs/backlog.md`"; `.github/tests/` parses that phrase and reads the file (`test_the_shared_instance_has_its_first_database.py`, `test_a_deploy_key_is_bound_to_one_host.py`, and others); and the workflows, `dependabot.yml` and most `.github/tests/` modules name the path, mostly as a docs-only path filter or exemption. A first attempt that converted the file alone failed `validate`.

- **Kind**: It owes MODIFIED deltas on the two requirements that cite `docs/backlog.md`, and test updates, beside the conversion and the workflow block's move to v12.
- **Recorded by**: ai-toolkit's `one-file-per-backlog-entry`, which migrated each project's backlog after it shipped; here it closed the conversion's pull request rather than let a backlog move carry specification deltas unreviewed.
