## MODIFIED Requirements

### Requirement: A Host-Scoped Variable Lives in the Host's Own Vars File
A variable SHALL be supplied from a host's own vars file, named for the Hetzner server name that host carries, wherever a second host of a different tenant in the same environment would require a different value or none at all. Such a variable SHALL NOT be supplied from an environment's `group_vars`. An environment's `group_vars` file SHALL carry only what is true of every host in that environment whichever tenant owns it — which is what an environment-wide baseline across tenants *is*, and is what makes it safe for two stacks to read one file.

**The test is the variable's blast radius, not the number of hosts that happen to exist.** Where a repository has one stack per environment the two files are interchangeable and a variable placed in either resolves identically, so a misplacement is wrong before it is observably wrong. It becomes observably wrong at the moment a second tenant's stack declares the same environment, and it does so by silently widening what an existing entry reaches rather than by failing — which is why the placement is obliged here rather than left to be corrected when it starts to matter.

**The deploy-key authorisations a host grants are such a variable, and the invariant behind them is stated rather than left implied: one leaked private half SHALL reach one host.** A deploy key's public half therefore sits in the vars file of the one host it authorises, the shared platform stack's included. Where one application deploys to two hosts it SHALL do so with two keypairs, one enumerated in each host's file, and no single entry SHALL authorise a deploy to more than one host.

**The placements this requirement's own change examined and did not correct are named here rather than left to be discovered, and this requirement SHALL be read as unmet in those respects.** They are three, and three is what was assessed rather than what exists: no audit of the remaining variables in any environment's `group_vars` has been performed, and this list SHALL NOT be read as one. `hardening_ssh_allowed_cidrs` and `hardening_web_allowed_cidrs` mirror one *stack's* committed Terraform variables, and two tenants' stacks in one environment may open different ports to different places; `ops_user_accounts` grants an interactive login, and an operator of one tenant's host is not thereby an operator of another's. All three sit in an environment's `group_vars` today. Each needs a decision this requirement does not make — whether a per-stack firewall pair defeats the point of an environment-wide hardening baseline, and whether operator access is per environment or per tenant — and they are tracked in `docs/backlog/` as `put-the-remaining-host-scoped-variables-on-the-host-axis`, which covers the audit as well as the three. The obligation is stated here as well as there, because a backlog entry is deleted when its change is archived. **This paragraph is replaced when those three move, and not before**, and a further variable placed in an environment's `group_vars` on the strength of it is a breach rather than a precedent.

A host vars file carries no vaulted content today, and the labelling of one is outside this requirement. Where a secret-bearing variable first lands in a host's own file, the `--vault-id` label it is encrypted under follows the *run* — which is the environment, per *Host Configuration Names the Environment It Targets* — and not the file it sits in.

This requirement governs where a value is written, not what any role does with it. A role consumes a host variable without regard to which file supplied it, so nothing here obliges a role to change, and a role's own refusal when a required input is absent is *A Role's Absent Required Input Is Reported by Name* rather than this.

#### Scenario: Two stacks share an environment
- **WHEN** two stacks of different tenants declare the same Ansible group, and one application is deployed to both of their hosts
- **THEN** each host's deploy-key authorisation SHALL be enumerated in that host's own vars file, each naming a keypair of its own
- **AND** neither SHALL be enumerated in the environment's `group_vars` file, where one entry would authorise both hosts

#### Scenario: A value that is a property of the environment
- **WHEN** a variable's value is a property of the environment rather than of a host — a baseline every host in that environment receives, whichever stack provisions it
- **THEN** it SHALL be supplied from that environment's `group_vars` file
- **AND** it SHALL NOT be repeated in each host's vars file, which would make an environment-wide correction a per-host edit that nothing enumerates

#### Scenario: A stack whose declared server has no vars file is reported
- **WHEN** a stack's committed Terraform configuration declares a server name for which no committed host vars file exists
- **THEN** that SHALL be reported as a failure on the pull request, naming the stack and the file expected of it, rather than left to surface as a role refusing a required input part-way through a converge

#### Scenario: A host vars file is keyed on the name Terraform declares
- **WHEN** a stack renames the server it provisions without renaming the host vars file that carries that host's variables
- **THEN** the mismatch SHALL be reported rather than resolved, so that the converge cannot proceed against a host whose variables no committed file supplies
