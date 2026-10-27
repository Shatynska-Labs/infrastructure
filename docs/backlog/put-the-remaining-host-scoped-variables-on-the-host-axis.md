---
kind: change
waits_on: []
design_with: [say-what-the-host-firewall-actually-gates]
recorded_by: bound-a-deploy-key-to-one-host-when-an-environment-holds-two-stacks
re_checked: 2026-10-19
---

*A Host-Scoped Variable Lives in the Host's Own Vars File* (`openspec/specs/iac-host-configuration/spec.md`) names three placements it is to be read as unmet in, and this entry resolves them with it: `hardening_ssh_allowed_cidrs` and `hardening_web_allowed_cidrs` (they mirror one stack's `terraform.tfvars`, so are per stack by nature) and `ops_user_accounts` (a root-equivalent login; an operator of one tenant's host is not thereby one of another's). The requirement's paragraph is replaced when those move, not before.

Each needs a decision: for the firewall pair, whether per-stack CIDRs defeat an environment-wide hardening baseline (settle `say-what-the-host-firewall-actually-gates` first); for the accounts, whether host access is per environment or per tenant. An audit of the rest of both `group_vars` files against the requirement's test is part of the entry; `ghcr_pull_token`/`ghcr_pull_username` come first, since two tenants' GHCR organisations differ. The mechanism (`ansible/inventory/host_vars/<server name>.yml`) already exists and takes precedence.

Ride-along: `.github/workflows/host-converge.yml` checks that a stack's `group_vars` file exists but not its host vars file, so a `workflow_dispatch` run lacks the guard a pull request gets from `.github/tests`. Add the host-vars half beside the existing group-vars check; it completes a pair, it does not restate a role's contract.

- **Kind**: It needs the operator's per-environment-or-per-tenant decisions and owes an `iac-host-configuration` delta to the requirement's unmet paragraph.
- **Recorded by**: `bound-a-deploy-key-to-one-host-when-an-environment-holds-two-stacks`, which moved `deploy_apps` to host vars and left these deliberately because each needs a decision it did not make; it also declined the dispatch-path check on cost.
