---
kind: fix
waits_on: []
design_with: []
recorded_by: correct-the-documents-against-the-tree
re_checked: 2026-10-19
---

What remains is the slug rule, stated where an operator meets it (`docs/bootstrap-a-new-host.md` §7.1 and Appendix A). Slug-addressed checks (`infrastructure-drift`, `infrastructure-pre-commit-autoupdate`, `<inventory_hostname>-prune-host-images`) are pinged as `hc-ping.com/<ping key>/<slug>?create=1` by `drift.yml`, `pre-commit-autoupdate.yml` and the `image_prune` role, so re-slugging one at the observer alone does not fail: the next ping creates a second check under the old slug and the renamed one goes quiet a period later. Their display names are free to change. The per-stack Alertmanager checks are reached by their own ping URL (`PLATFORM_DEADMANSWITCH_URL`), so renaming one costs nothing. The appendix's *Renaming a server afterwards* covers the server-rename case only; §7.1 and Appendix A do not say which field is load-bearing.

Must not: re-slug a periodic-job check to tidy the list. The prune slugs are templated from `inventory_hostname`, and changing one at the observer alone puts it permanently out of step with the host.

The rest of the original entry is done: §7.1 now prescribes `<stack>-alertmanager` checks, and Appendix A records their period 5 and grace 2 with the reason (alarm after about seven minutes of silence).

- **Kind**: Documentation only, no decision outstanding.
- **Recorded by**: `correct-the-documents-against-the-tree`, whose operator step looked for a check name the observer did not hold; the observer's state is outside that change's documents.
