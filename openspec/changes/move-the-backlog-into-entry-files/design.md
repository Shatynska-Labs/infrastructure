## Context

The backlog moves from one file to a directory of entry files, the shape ai-toolkit v12 and its `backlog` skill read. The conversion itself is mechanical and done by ai-toolkit's `scripts/backlog-migrate`. `Fuperia-IT/infrastructure` made the same move as `move-the-backlog-into-entry-files`, and this design follows its decisions; what differs here is named where it differs.

A trial conversion of today's trunk (`3343bab`), staged, makes the static suite fail exactly five tests and nothing else:

- `iac-platform-services` *Single Shared PostgreSQL Instance, Per-Application Databases* says its mechanism "is tracked in `docs/backlog.md` as `automate-per-application-database-provisioning`", and `test_the_shared_instance_has_its_first_database.py` parses that phrase with a pattern fixed to `docs/backlog\.md` and searches the file for the name.
- `iac-host-configuration` *A Host-Scoped Variable Lives in the Host's Own Vars File* says its three placements "are tracked in `docs/backlog.md` as `put-the-remaining-host-scoped-variables-on-the-host-axis`", and `test_a_deploy_key_is_bound_to_one_host.py` searches the file for the name.
- `test_basis_api_durable_store.py`, derived for `record-basis-api-durable-store`, reads `docs/backlog.md` for the follow-up entry `finish-basis-api-s-move-to-its-own-database`. Fuperia has no counterpart.
- `test_the_shared_instance_store_moved.py` exempts one line of `docs/backlog.md`, a dated observation naming the superseded store, and asserts the exemption still matches a line (two failures).

Fuperia's fourth site, the tailnet sweep's whole-file exclusion, does not exist here: this repository has not retired Tailscale. Every other mention of `docs/backlog.md` in the tree is a prose pointer or a fixture string. The workflows and `dependabot.yml` name it in comments only, and no path filter names it.

## Goals / Non-Goals

**Goals:**

- The backlog is in the shape ai-toolkit's workflow and skill read, with every entry carried over.
- Each requirement that cites a backlog entry still cites one that exists, and a test still confirms it.
- The sweep exempts what it exempted before, no more and no less.

**Non-Goals:**

- Repointing every prose pointer to `docs/backlog.md` across the tree (D6).
- Opening a workstream. The directory is seeded empty.
- Revising any entry's content beyond the values the conversion could not set.

## Decisions

### D1: A requirement cites an entry as "tracked in `docs/backlog/` as `<entry>`"

The citation names the directory and the entry's name, not the entry file's path. The backlog README says to refer to an entry only by its name, and the name is the entry's only identifier. This also keeps the citation from being a backticked Markdown path. `test_the_requirement_names_where_the_recipe_lives.py` reads backticked `.md` paths in *Single Shared PostgreSQL Instance, Per-Application Databases* as candidate recipe documents, and `docs/backlog/automate-per-application-database-provisioning.md` would be one more path for that scoping to keep out.

Alternative: cite `docs/backlog/<entry>.md`. Rejected for the two reasons above, and because the requirement's own sentence already says why the obligation is stated in the specification as well: the entry is deleted when its change is archived. A path makes that deletion look like a broken link, where a name reads as what it is.

Each delta is the requirement's current text with that one phrase changed, so every other test that reads either requirement, from a live delta or the main specification, reads the same text it reads today.

### D2: An entry is confirmed by its own file

The tests that confirm an entry exists check that `docs/backlog/<entry>.md` is a file, rather than that the backlog's text contains the name. `test_the_shared_instance_has_its_first_database.py` currently calls its check "a necessary condition only: this establishes that the backlog names the entry, not that it is an entry rather than a mention inside another one". With one file per entry, a file of that name is the entry, so the check becomes sufficient. The phrase pattern that extracts the entry name from the requirement follows D1's wording.

`test_basis_api_durable_store.py` belongs to `record-basis-api-durable-store`, whose implementation is on the trunk and whose record is in review (#294). Its follow-up check is changed the same way, and only that check: its assertion stays "the backlog carries `finish-basis-api-s-move-to-its-own-database`", read from where the backlog now keeps an entry.

### D3: The line exemption follows its line

`test_the_shared_instance_store_moved.py` exempts one *line*, and says why a file-wide exemption was refused: the file named the store twice, and only one of the two was a dated observation. That line now sits in `docs/backlog/rename-the-requirements-that-read-narrower-than-they-are.md`. The exemption keeps its marker and reason and names that file. The sweep's existing assertion that each exemption still matches a line keeps it from outliving the line.

Fixture strings that name `docs/backlog.md` as a path inside a synthetic tree, in this and other modules, are inputs to a path check and stay as they are.

### D4: The workflow block moves to v12 as an unedited copy

This repository's block is an unedited v10 copy: its body differs from v10's fragment in nothing. So it takes the v12 fragment whole. That brings v11's workstreams with it: the status line gains a workstream field, `draft` names a workstream, and `archive` re-reads one. `project-init` seeds `docs/workstreams/README.md`, which those sentences need. No workstream is opened.

Alternative: take only the backlog-path edits and leave the marker at v10. Rejected: the marker would then describe text the block does not hold, and the next sync would bring v11 anyway.

### D5: Recorded-by values are set by hand where the converter could not set them

The converter writes `recorded_by` only where it finds a known change name. Thirteen entries came out without one in the trial. Where the body names the change that recorded it, that name is set. Where the body names an occasion and no change, a double-quoted text is set from it. Where the body says the recorder is unknown, the field is left out. A value the converter did set is checked against the body as well, since Fuperia's run set one entry's field to a change the body said *unblocked* it. Each entry's body keeps its **Recorded by** line as written.

### D6: Pointers are repointed only in files this change edits

The tree outside the backlog and the change records mentions `docs/backlog.md` 118 times, most of them prose pointers in documents, role READMEs, workflow and Ansible comments, and test docstrings. Each still names its entry, so nothing is lost, but the path no longer exists. This change repoints the two in `AGENTS.md`'s project conventions, a file it edits for the workflow block, and the ones inside the constants, messages and docstrings it changes in the four test modules. The rest are recorded as the backlog fix `repoint-the-backlog-references`, as Fuperia recorded its own, so that this change's diff stays about the move.

### D7: The conversion is run against the trunk the pull request merges into

Three branches in flight edit `docs/backlog.md`: `record-basis-api-durable-store`'s record (#294, open), `assert-every-tfvars-assigns-its-required-variables` and `rename-the-servers-off-the-company-names` (no pull request yet). A conversion made now and merged later would silently drop whichever of their edits landed in between, since the converter deletes `docs/backlog.md`.

So the conversion is not hand-merged: the converter's output and D5's values are one commit, kept apart from every other commit of this change. Before the pull request is opened, that commit is dropped, the branch is rebased onto the freshly fetched trunk, the converter is run again and D5's values re-applied as a new commit. The entry `repoint-the-backlog-references` (D6) is added in a commit of its own, after the conversion, and survives the rebase as any other commit does. Whatever has merged by then is converted with everything else. A branch merging after this change brings the trunk in and re-expresses its backlog edits as entry files; a merge of `docs/backlog.md` against its deletion conflicts, so that cannot pass unnoticed. Each such branch is told so in this change's pull request.

Alternative: wait for all three to merge. Rejected: two have no pull request and no date, and the conflict they meet is loud.

## Risks / Trade-offs

- **[A new citation of the old form passes unnoticed]** → After this change, a requirement written as "tracked in `docs/backlog.md` as …" would match neither test's pattern, and D7 admits branches that may carry one. A static test therefore fails on any requirement, in `openspec/specs/` or a live delta under `openspec/changes/` (the archive excluded, since it is history), that names `docs/backlog.md` at all, rather than only reading the new phrase. A requirement a live MODIFIED delta shadows is read from that delta, as D1's other tests read it, so the two citations this change corrects pass before archive. A citation a merged branch brings into the main specifications before this change merges gets a MODIFIED delta of its own in this change; one inside another live change's delta is corrected in that delta.
- **[A branch in flight resurrects `docs/backlog.md`]** → A branch that resolves its conflict by keeping the file would bring a second backlog back. D7's notice names the resolution, and a static test fails while `docs/backlog.md` exists.
- **[The converted entries drift from the old file's content]** → The converter keeps any text it cannot map in the entry's body and reports it. Its report for the final run is in the pull request description.
