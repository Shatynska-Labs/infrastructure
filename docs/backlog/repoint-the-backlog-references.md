---
kind: fix
waits_on: [move-the-backlog-into-entry-files]
design_with: []
recorded_by: move-the-backlog-into-entry-files
re_checked: 2026-10-27
---

About a hundred committed files outside the backlog and the change records still point at `docs/backlog.md`, which `move-the-backlog-into-entry-files` replaced with `docs/backlog/`: documents under `docs/`, role READMEs and task comments, `platform/`, workflow and `dependabot.yml` comments, and test docstrings under `.github/tests/`. Each pointer still names its entry, so nothing is lost, but the path no longer exists. Repoint each to `docs/backlog/`, keeping the entry's name, and leave fixture strings that name `docs/backlog.md` as a path inside a synthetic tree as they are.

- **Kind**: no specification delta and no decision; a mechanical sweep, though wide.
- **Recorded by**: `move-the-backlog-into-entry-files` repointed only the files it edited, so that its diff stayed about the move.
