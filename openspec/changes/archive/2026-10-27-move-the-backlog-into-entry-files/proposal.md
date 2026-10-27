## Why

ai-toolkit's development workflow v12 and its `backlog` skill read the backlog as `docs/backlog/`, one file per entry with its values as YAML frontmatter (ai-toolkit's `one-file-per-backlog-entry`). This repository still keeps it as one file, `docs/backlog.md`, and its workflow block is v10, so the skill cannot read the backlog and the block names a path the toolkit no longer seeds. `Fuperia-IT/infrastructure`, which shares this repository's lineage, made the same move as `move-the-backlog-into-entry-files` (Fuperia-IT/infrastructure#74); this change follows it, adjusted to what differs here. It cannot be a record-only fix: two requirements cite entries as "tracked in `docs/backlog.md` as `<entry>`", three test modules read that file to confirm an entry exists, and one sweep exempts a line of it by path. The backlog entry `move-the-backlog-into-entry-files` records this.

## What Changes

- **The conversion.** `docs/backlog.md` becomes `docs/backlog/README.md` (the README ai-toolkit seeds) plus one `docs/backlog/<name>.md` per entry, produced by ai-toolkit's `scripts/backlog-migrate` (58 entries on today's trunk). The `recorded_by` values the converter could not map are set by hand from each entry's own text (design D5).
- **The workflow block** moves from v10 to v12 as an unedited copy of the fragment: v11 adds workstreams, v12 names `docs/backlog/`. `docs/workstreams/README.md` is seeded by `project-init`, with no workstream opened (design D4).
- **The two requirements that cite the backlog** cite it as "tracked in `docs/backlog/` as `<entry>`", by the entry's name, and say nothing else new (design D1).
- **The three tests that confirm an entry exists** read the entry's own file, `docs/backlog/<entry>.md`, rather than searching one file's text for the name (design D2). Two confirm a requirement's citation; the third, in `test_basis_api_durable_store.py`, confirms the follow-up `record-basis-api-durable-store` recorded.
- **The sweep that exempts a line of `docs/backlog.md`** names the entry file that now holds the line (design D3).
- **A guard against the old path.** A static test fails where a requirement, in the main specifications or a live delta, cites `docs/backlog.md`, and where `docs/backlog.md` exists again (design Risks).
- **Pointers to `docs/backlog.md`** are repointed in `AGENTS.md`'s project conventions and inside the constants, messages and docstrings of the four test modules this change edits. Pointers elsewhere are recorded as the fix `repoint-the-backlog-references` (design D6).

## Capabilities

### New Capabilities

None.

### Modified Capabilities

- `iac-platform-services`: *Single Shared PostgreSQL Instance, Per-Application Databases* cites its backlog entry in `docs/backlog/`.
- `iac-host-configuration`: *A Host-Scoped Variable Lives in the Host's Own Vars File* cites its backlog entry in `docs/backlog/`.

Neither requirement's obligations change: the delta is the citation's location, word for word otherwise.

## Workstream

This change advances no workstream. None is open; this change seeds the directory that would hold one.

## Impact

- `docs/backlog.md` (removed), `docs/backlog/` (new), `docs/workstreams/README.md` (new), `AGENTS.md` (the workflow block and two pointers in the project conventions).
- `openspec/specs/iac-platform-services/spec.md` and `openspec/specs/iac-host-configuration/spec.md`, on archive.
- `.github/tests/`: `test_the_shared_instance_has_its_first_database.py`, `test_a_deploy_key_is_bound_to_one_host.py`, `test_basis_api_durable_store.py`, `test_the_shared_instance_store_moved.py`, and whatever tests the derivation adds.
- Branches in flight that edit `docs/backlog.md` (design D7).
- No change to Terraform, Ansible, the platform stack, any workflow's behaviour or any host. The workflows and `dependabot.yml` name `docs/backlog.md` in comments only, and no path filter names it.
