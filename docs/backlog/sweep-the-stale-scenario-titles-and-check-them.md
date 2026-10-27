---
kind: change
waits_on: []
design_with: [rename-the-requirements-that-read-narrower-than-they-are]
recorded_by: correct-the-documents-against-the-tree
re_checked: 2026-10-19
---

Citations here name a requirement and often a scenario inside it (`... -- scenario "<title>"`). Both halves rot in the same rename, and `correct-the-documents-against-the-tree` corrected and checked only the requirement half, so many citations under `.github/tests` (and one in `.github/workflows/drift.yml`) name a scenario no specification under `openspec/specs/` holds (30 counted on 2026-09-13). Several titles were reworded rather than renamed, so each replacement needs a reading, not a substitution.

The `drift.yml` citation is the inverse case: it cites *"Drift in one stack does not resolve another's report"* while `openspec/specs/iac-cicd-pipeline/spec.md` still titles it *"Drift in one environment does not resolve another's report"*. `rename-terraform-environments-to-stacks` left the specification side alone because a `MODIFIED` requirement replaces its block whole and `openspec validate` reads a renamed scenario as dropped. Sweeping without deciding how a scenario is renamed would leave the tree citing a title the specification lacks.

Do the check with the sweep: `.github/tests/test_the_retired_requirement_names_are_gone.py` already reads every tracked file, flattens wrapped comments and derives its subject from committed specifications. The scenario predicate is its inverse (a cited title **not** among live scenario titles), so it needs its own reader; measure its false-positive rate first, since any quoted phrase looks like a citation.

- **Kind**: It needs a decided mechanism for renaming a scenario through a `MODIFIED` delta, and the `drift.yml` case owes an `iac-cicd-pipeline` delta renaming that scenario.
- **Recorded by**: `correct-the-documents-against-the-tree` (archived 2026-09-13), which swept requirement names; the scenario half is a different predicate over a different set and would have doubled its diff with a second unchecked sweep.
