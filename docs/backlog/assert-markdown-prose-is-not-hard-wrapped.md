---
kind: fix
waits_on: []
design_with: []
recorded_by: "the 2026-09-11 fix that removed the hard wraps"
re_checked: 2026-10-19
---

`AGENTS.md` says "Do not hard-wrap prose. Keep each paragraph on a single line". Nothing checks it, and hard wraps re-accumulate silently: the sweep this entry was recorded beside (2026-09-11) rewrapped 72 of 211 tracked markdown files, and the wraps had appeared in every week of the project. Under the rule, any prose paragraph spanning more than one line is a violation, so no threshold is needed. The detector must exempt structural breaks: fenced and indented code, tables, YAML frontmatter, list-item continuations, and lines ending in two spaces or a backslash. Scope is markdown only; comments in `.py`/`.yml`/`.sh`/`.tf` stay wrapped (`.pre-commit-config.yaml`'s comments are the shape to preserve). It is not a formatter: Prettier's `proseWrap` would rewrite style across the tree and archived records, and there is no Node toolchain to hang it on; markdownlint has no such rule. It fits `.github/tests` as one new module.

- **Kind**: A static assertion with no delta or decision.
- **Recorded by**: `unknown` change; recorded 2026-09-11 beside the fix that removed the hard wraps and wrote the rule, but not its check.
