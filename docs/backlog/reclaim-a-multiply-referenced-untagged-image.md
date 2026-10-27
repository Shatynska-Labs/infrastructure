---
kind: change
waits_on: []
design_with: []
recorded_by: report-refused-removals-in-the-host-prune
re_checked: 2026-10-19
---

An untagged image with more than one repository reference (pulled by digest from a registry and its mirror) cannot be removed by identity unforced: the runtime refuses with "referenced in multiple repositories", so the host prune (`ansible/roles/image_prune`) offers and refuses it every run, now counted under `refused` and pointed here from the role's README.

Must not: force removal; *Unreferenced Host Images Are Pruned on a Schedule* forbids it because the unforced refusal backstops a defective keep set. The likely shape is removing through each repository reference in turn, as tags are, but that makes a digest reference something the run drops and has no counterpart to the pre-removal re-check that guards a re-pointed tag. Neither host is known to carry such an image.

- **Kind**: It changes what the run removes, owing a delta to *Unreferenced Host Images Are Pruned on a Schedule*.
- **Recorded by**: `report-refused-removals-in-the-host-prune`, which made the condition visible; changing removal was outside a reporting change.
