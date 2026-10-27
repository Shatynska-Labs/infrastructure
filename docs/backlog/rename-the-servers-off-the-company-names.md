---
kind: change
waits_on: []
waits_for: "the operator's word on whether the server rename is still wanted, since its branch was deleted unmerged"
design_with: []
recorded_by: "the 2026-10-27 check, after move-the-backlog-into-entry-files, that found the branch deleted unmerged"
re_checked: 2026-10-27
---

The operator's personal tailnet also holds Fuperia's servers, whose tailnet machine names are `main-production` and `main-staging`, the same names this repository gives its own servers. CI reaches a host by its server name: the hcloud inventory makes it `inventory_hostname`, the `tailscale` role reports it as the tailnet name, and `host-converge.yml` resolves it with `tailscale ip -4 <name>`. While both companies' machines carry these names, a converge here can be aimed at the other company's host.

The work was done on 2026-10-14 as one commit, `8e9b895`, on the branch `rename-the-servers-off-the-company-names`. It names each server for its environment (`production`, `staging`) and leaves every stack name as it is, renames the two `host_vars` files, re-points two `.github/tests` assertions, and updates the documents. It carries a change directory with a proposal, a design and tasks, including the operator steps outside the repository (the Tailscale console rename, `PLATFORM_DEPLOY_HOST`, the heartbeat check). The branch was never pushed and had no pull request. By 2026-10-27 it had been deleted along with its working tree, so it was restored from the commit and pushed. It sits on a trunk two weeks old and edits `docs/backlog.md`, which no longer exists, so taking it up means bringing the trunk in and moving its backlog edit into an entry file. That edit records `restate-the-naming-rule-for-a-tailnet-shared-between-companies`, the rationale of *The Host's Own Name Is Set by the Converge* (`openspec/specs/iac-host-configuration/spec.md`) that still says the tailnet belongs to one company.

- **Kind**: it renames servers through the pipeline (an in-place `hcloud_server` update) and needs operator steps outside the repository, and whether it is still wanted is the operator's decision: the branch may have been deleted on purpose.
- **Recorded by**: found while checking the branches in flight that `move-the-backlog-into-entry-files` named; not a change of its own.
