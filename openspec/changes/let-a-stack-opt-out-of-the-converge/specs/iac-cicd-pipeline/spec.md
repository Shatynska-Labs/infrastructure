## MODIFIED Requirements

### Requirement: Host Configuration Is Applied by a Gated Workflow
Host configuration SHALL reach a host through a workflow triggered by a merge to the default branch. A converge changes the host firewall, the accounts that may log in and the container runtime, so the path by which it reaches a host SHALL be gated in the same way the Terraform apply and the platform deploy are.

**One converge is exempt, and only one: a host's first.** Before that run the host is on no private network the workflow can reach it over and holds no credential the workflow can authenticate with, so the first converge is necessarily an operator's, from a workstation, over the host's public address. Every converge after it SHALL reach the host through the workflow. The exemption is bounded by the host's own bootstrap and SHALL NOT be read as permitting a workstation converge of a host already configured.

The workflow SHALL separate publishing from converging, in a single run. A job that holds **no** credential capable of reaching a host SHALL publish, for a human to read, what the merge changes under the host-configuration directory. A converge job **per stack** SHALL declare that stack's own GitHub Environment, taken from that stack's committed pipeline declaration, and SHALL be the only job holding the credentials a converge needs.

The publishing job is **not** obliged to be per stack, and this requirement deliberately does not make it one. What it publishes is the committed diff, which is the same document whatever stack reads it — a copy per stack would be identical in every row, and would put the number of jobs a merge starts in proportion to something the diff does not depend on. What SHALL be per stack is the credential and the gate.

This layer has no saved-plan artifact and SHALL NOT pretend to one. A check-mode run is not one: it skips `command` tasks, it swallows failures in roles that ignore errors under check mode, and it must authenticate to the host — so it could only run in the job the gate exists to withhold the credential from. What the pre-approval job publishes is the committed diff, which for this layer is complete: every input a converge applies is committed, so there is no value computed elsewhere that the diff omits.

The workflow SHALL name no stack. Which stacks exist, which GitHub Environment gates each, and which repository secret holds each one's read-only credential SHALL come from discovery over committed files, and adding a stack SHALL require no change to any file under `.github/workflows/`.

Discovery SHALL fail closed, with a message naming the stack and what was wrong, rather than omitting a stack from the run. A stack that can be provisioned but not converged, and one that can be converged but is gated by nothing, are both states this discovery SHALL refuse rather than pass over: a stack whose host is converged by no job is indistinguishable from a stack that has nothing to converge.

**A stack whose own committed declaration excludes it from the converge is not omitted in that sense**, and the difference SHALL be visible in every run rather than inferred from an absence. The workflow SHALL name each such stack as excluded by its own declaration before it emits the matrix, SHALL converge it in no row, and SHALL fail a run requested by hand that names it, saying that it is excluded rather than that it was not found. A run in which every discovered stack is excluded SHALL fail as discovery finding nothing does, because a converge that converges no host and reports success is the outcome this requirement exists to prevent. A stack excluded by its own declaration SHALL NOT be refused for the absence or invalidity of a field only its converge would consume — its declared Ansible group, that group's variables file or its read-only secret name — because switching a stack off SHALL NOT be harder than switching it on; the check that its inventory source and its pipeline declaration exist for each other SHALL still apply to it, being a property of the tree rather than of a converge.

A converge job SHALL establish that the credentials it holds are usable — that the stack's secrets decrypt and that its inventory resolves — **before** any task acts on the host. Those inputs are decrypted at the moment they are first used, which is several roles into the play, so a run that starts with a wrong secret would otherwise leave a partially-converged host for a reason that had nothing to do with the host.

A converge job SHALL install the toolchain and the external content the play needs before running it, from this repository's own pinned manifests, and SHALL run from the directory whose configuration governs the run. A continuous-integration runner carries neither, and a run that reaches a missing plugin or a missing external role fails inside a mechanism, reading as a broken mechanism rather than as an unprovisioned machine. Running from the wrong directory is worse than failing: the configuration that makes a rejected credential fail the run is not loaded, so the run continues and reports a rejected credential as a stack whose server does not exist.

The version of Ansible a converge runs SHALL be the version the role-verification suite runs. A converge applying roles under a different Ansible than the one they were verified under is verified by nothing, and the agreement SHALL be asserted rather than intended, being a static read of two committed files.

A converge SHALL NOT be cancelled in favour of a later one. Runs against one stack SHALL be serialised, and an in-flight converge SHALL be allowed to finish: interrupting a play mid-run leaves the host partially converged, which is recoverable as an exception and not as a normal case.

One stack's converge failing SHALL NOT prevent another stack's from running and reporting.

#### Scenario: A merge to the host configuration converges without a workstation
- **WHEN** a merge to the default branch changes the host-configuration directory
- **THEN** each already-configured stack's host, other than one excluded by its own declaration, SHALL be converged by the workflow, and no step of that converge SHALL require a command run from an operator's machine

#### Scenario: A host's first converge is the operator's
- **WHEN** a host has not been converged before, so it is on no private network the workflow can reach it over and holds no credential the workflow can authenticate with
- **THEN** that one converge MAY be run from a workstation over the host's public address, and every converge of that host afterwards SHALL reach it through the workflow

#### Scenario: The pre-approval job holds no converge credential
- **WHEN** the job that publishes what the merge changes runs
- **THEN** it SHALL declare no GitHub Environment and SHALL consume no credential capable of reaching a host

#### Scenario: The converge job is gated on the environment's own GitHub Environment
- **WHEN** a converge job runs for a stack
- **THEN** it SHALL declare the GitHub Environment named by that stack's own pipeline declaration, so that its protection rules and its secrets are the ones that apply

#### Scenario: An environment that cannot be converged fails the workflow
- **WHEN** discovery finds a stack declaring a pipeline configuration but carrying no host-configuration inventory source, or an inventory source whose stack declares no pipeline configuration
- **THEN** the workflow SHALL fail with a message naming that stack and which side is missing, rather than converging the stacks it could resolve

#### Scenario: Discovery finding no environment fails rather than reporting success
- **WHEN** discovery over the host-configuration inventory sources yields an empty set
- **THEN** the workflow SHALL fail with a message identifying discovery as the cause, and SHALL NOT allow a dependent job to be skipped and reported as successful

#### Scenario: A run is requested for an environment that does not exist
- **WHEN** a converge is requested by hand naming a stack discovery did not find
- **THEN** the run SHALL fail naming the stacks that were found, rather than converging none and reporting success

#### Scenario: A stack excluded by its own declaration is named and not converged
- **WHEN** a stack's pipeline declaration states that its host is not converged
- **THEN** the workflow SHALL name that stack as excluded by its own declaration, SHALL run no converge job for it, and SHALL converge every other discovered stack as before

#### Scenario: An excluded stack is not refused for a field only its converge would consume
- **WHEN** a stack's pipeline declaration excludes it from the converge and declares no Ansible group, or one whose variables file does not exist
- **THEN** discovery SHALL accept the tree, name the stack as excluded, and converge every other stack, rather than refusing the stack for a field no converge of it will read

#### Scenario: An excluded stack still needs its inventory source
- **WHEN** a stack's pipeline declaration excludes it from the converge but no inventory source exists for that stack
- **THEN** discovery SHALL fail naming that stack and the missing side, exactly as it does for a stack that is not excluded

#### Scenario: A run requested for an excluded stack fails naming the exclusion
- **WHEN** a converge is requested by hand naming a stack whose declaration excludes it from the converge
- **THEN** the run SHALL fail saying that the stack is excluded by its own declaration, rather than converging nothing and reporting success, or reporting the stack as not found

#### Scenario: Every stack excluded fails rather than reporting success
- **WHEN** every stack discovery finds is excluded from the converge by its own declaration
- **THEN** the workflow SHALL fail naming the excluded stacks, and SHALL NOT allow a dependent job to be skipped and reported as successful

#### Scenario: A wrong secret stops the run before the host is touched
- **WHEN** a converge job holds a credential that does not decrypt that stack's committed secrets, or a credential its inventory source rejects
- **THEN** the run SHALL fail before the first role acts on the host, rather than partway through the play

#### Scenario: The converge job supplies what the run needs
- **WHEN** a converge job runs on a continuous-integration runner, which carries no external content of its own
- **THEN** it SHALL have installed the toolchain and the external content the play needs from this repository's pinned manifests, and SHALL run from the directory whose configuration governs the run

#### Scenario: The converge runs the Ansible the roles were verified under
- **WHEN** the version the converge job installs is compared with the version the role-verification suite installs
- **THEN** the two SHALL be the same, and a difference SHALL fail the required status check

#### Scenario: One environment's failure does not silence another's
- **WHEN** a converge fails for one stack in a run covering several
- **THEN** every other stack's converge SHALL still run and report its own outcome

### Requirement: Each Stack Declares Its Own Pipeline Configuration
Every directory under `terraform/stacks/` SHALL carry a committed, machine-readable file declaring the pipeline configuration for that stack. Three fields are **required**: the name of the GitHub Environment its apply job attaches to, the name of the repository secret holding its read-only Hetzner token, and the name of the Ansible group its host-configuration converge targets. Three are **optional**: whether the Destroy Policy Gate applies to it, which defaults to applying when absent (see the Destroy Policy Gate requirement, whose scenario "An environment declaring nothing is gated" is the case this default serves); whether the shared platform stack is deployed to it, which defaults to **not** being deployed when absent; and whether the host-configuration workflow converges its host, which defaults to the host **being** converged when absent.

**The declared Ansible group SHALL NOT be derived from the stack's name.** A stack is a *(tenant, environment)* pair and the group it converges is the environment alone, so the two are equal only where a repository has one tenant. Parsing one out of the other is a rule that holds on the names a repository happens to have and fails silently on the next one — as a group that does not exist, reported several steps after the run began. It is declared for the same reason the GitHub Environment's name is: the pipeline reads it rather than computing it.

**Unlike the other two required fields, the declared Ansible group carries no uniqueness obligation**, and the difference is not an oversight. Two stacks naming one GitHub Environment share its write token and its protection rules; two naming one read-only secret share one credential. Two stacks naming one Ansible group share a set of host variables, which is what an environment-wide baseline across tenants *is*. Distinctness SHALL NOT be required of it.

Each optional field SHALL name what happens when it is **true**, rather than its inverse — the value states whether the gate applies, or whether the platform stack is deployed, or whether the host is converged, rather than whether the stack is disposable, excluded or dormant. A field whose polarity has to be inferred from its name is one a reader can invert without noticing, and inverting any of these silently removes a guard: the first, the strongest guard on an apply; the second, the guard against a stack receiving an application stack nobody decided to give it; the third, the guard against a host whose firewall, SSH configuration and operator accounts silently stop being applied.

**Each optional field's default SHALL be the value that is safe when the field was forgotten**, and the defaults differ for that one reason. A stack whose declaration says nothing about the destroy-policy gate is gated, because the mistake to protect against is an ungated destructive apply. A stack whose declaration says nothing about the platform stack does not receive it, because a stack directory is committed before its GitHub Environment holds any platform secret, and the mistake to protect against is a deploy attempted under credentials that do not yet exist, to a host that may not yet authorise the key. A stack whose declaration says nothing about the converge is converged, because the mistake to protect against is a host whose firewall, SSH configuration and operator accounts silently stop being applied — a host left out of the converge by a forgotten field drifts from its baseline with nothing reporting it.

**Excluding a stack from the converge is a declaration about the pipeline, not about the host, and SHALL NOT be derived from the stack's Terraform configuration.** A stack whose server has been decommissioned has no host to converge, and the declaration is how it says so; reading the same fact out of a Terraform variable would couple the host-configuration workflow to the provisioning layer's file format, which no workflow in this repository reads. The two are independent facts and MAY disagree for an interval — a server re-enabled before its declaration is flipped back is converged by nothing until it is — and that interval is the operator's to close, in the same pull request that re-enables the server.

**A stack declaring that the platform stack is deployed to it SHALL also authorise that deploy on the host**, by enumerating the platform application among the deploy-key authorisations in the **host vars file of the host that stack provisions** — see *A Host-Scoped Variable Lives in the Host's Own Vars File* (`openspec/specs/iac-host-configuration/spec.md`). It SHALL NOT be the `group_vars` file of the declared Ansible group, and the difference is not cosmetic: a group is an environment, an environment may hold two stacks, and an authorisation written there would answer both stacks' opt-ins with one entry while authorising one deploy key on two hosts. The two are separate facts about separate layers and SHALL NOT be derived one from the other — a host may authorise the key before the pipeline is pointed at it, and that interval is a deliberate state rather than an error. The implication holds in one direction only, and a declaration opting in without the corresponding authorisation SHALL fail the required status check on the pull request, naming both files. **Each stack's opt-in SHALL be answered by its own host's authorisation**, so two stacks sharing an environment carry two obligations rather than one between them. Left to the deploy, the same disagreement surfaces as an authentication failure after the tailnet join and after any approval, with a cause that has to be inferred.

Adding a stack SHALL therefore require **no change to any file under `.github/workflows/`**. Workflows SHALL NOT enumerate stacks, name them in a condition, or map a stack to its secrets, its Environment name or its Ansible group in workflow text. A pipeline that must be edited to add a stack is the defect this requirement exists to prevent, and it is the state the README already described as absent.

That claim is about workflow files and nothing wider. A stack still needs its own state workspace, its own GitHub Environment and secrets, an inventory source of its own, the `group_vars` file of the environment it declares — which another stack may already have created — a host vars file of its own for the host-configuration workflow to converge it, and an entry in the Dependabot configuration for the lockfile `terraform init` creates in its directory — which the Automated Dependency Updates requirement (iac-safety-hardening) already obliges, and which this requirement does not relax.

Each stack's declared read-only secret name SHALL be distinct from every other stack's, and so SHALL its declared GitHub Environment name. Two stacks naming the same read-only secret share one token; two naming the same GitHub Environment share its **write** token and its protection rules, so a stack intended to be ungated would hold the reviewed stack's write credential — contradicting the Write Credentials Confined to the Gated Pipeline requirement (iac-safety-hardening), which places each stack's Read & Write token in that stack's own GitHub Environment. Both are the defect a per-stack declaration exists to prevent, reached through committed data rather than through workflow text and therefore invisible to any check that reads only the workflows.

**No stack's declared read-only secret name SHALL be a name its own GitHub Environment also defines, and `HCLOUD_TOKEN` is such a name for every stack.** Credential Scoping by Privilege requires each stack's GitHub Environment to define `HCLOUD_TOKEN` as that stack's Read & Write token, and GitHub resolves an Environment-scoped secret ahead of a repository-scoped one of the same name. A declaration naming `HCLOUD_TOKEN` as its read-only secret is therefore correct only for a job that declares no `environment:`; read from a job that declares one, the same name yields the **write** token, silently and with no error. The declared name is read by gated jobs as well as ungated ones, so the name SHALL be one no Environment shadows.

Discovery SHALL fail closed. A stack directory whose declaration is absent, unparseable, or missing a **required** field SHALL fail the workflow with a message naming the directory and the missing field, and SHALL NOT be silently skipped. A field is required of the discovery that reads it: a workflow that runs no converge SHALL NOT refuse a stack for the absence of a field only a converge consumes, since failing a Terraform-only pull request for a host-configuration reason names a cause the change does not have. An absent optional field is not a missing field: it takes its default and discovery proceeds. A skipped stack is one that is planned by nothing, applied by nothing and drift-checked by nothing, which is indistinguishable from the stack not existing and is exactly the condition this capability is meant to make impossible.

A stack excluded by an optional field it declares is not a skipped stack in that sense, and the difference SHALL be visible rather than inferred. It is excluded by its own committed declaration from one workflow's matrix, remains covered by every workflow that does not read that field, and SHALL be reported as excluded by the workflow that read it.

#### Scenario: A new stack needs no workflow edit
- **WHEN** a directory is added under `terraform/stacks/` carrying a valid pipeline declaration
- **THEN** the validation, plan, apply, drift and host-converge workflows SHALL each cover it on their next run, with no change to any file under `.github/workflows/`

#### Scenario: A converge reads its Ansible group from the declaration, not from the stack's name
- **WHEN** a stack whose name differs from the Ansible group its host belongs to is converged
- **THEN** the play's target group, the vault-id label and the `group_vars` file SHALL be taken from the declared field, and nothing SHALL parse them out of the stack's directory name

#### Scenario: Two stacks declaring the same read-only secret are refused
- **WHEN** two stack declarations name the same repository secret as their read-only token
- **THEN** the pipeline SHALL fail, naming both stacks, rather than running two stacks' plans under one credential

#### Scenario: Two stacks declaring the same GitHub Environment are refused
- **WHEN** two stack declarations name the same GitHub Environment
- **THEN** the pipeline SHALL fail, naming both stacks, rather than applying two stacks under one write token and one set of protection rules

#### Scenario: Two stacks declaring the same Ansible group are accepted
- **WHEN** two stack declarations name the same Ansible group, each with an inventory source reaching its own Hetzner project
- **THEN** discovery SHALL accept both, because a shared group is a shared set of host variables rather than a shared credential

#### Scenario: A declaration naming the write token's own name is refused
- **WHEN** a stack declaration names as its read-only secret a name that every GitHub Environment defines for its Read & Write token
- **THEN** the required status check SHALL fail, naming that stack, rather than leaving a gated job to resolve a write credential from a field that says read-only

#### Scenario: A stack declaring nothing about the converge is converged
- **WHEN** a stack's pipeline declaration does not state whether its host is converged
- **THEN** the host-configuration workflow SHALL converge that stack's host, exactly as if the declaration had stated that it is

#### Scenario: An unrecognised converge value is refused
- **WHEN** a stack's pipeline declaration states a value for whether its host is converged that is neither true nor false
- **THEN** host-configuration discovery SHALL fail naming that stack and the value, rather than reading the value as either answer

#### Scenario: A stack missing its declaration fails the pipeline
- **WHEN** a directory under `terraform/stacks/` has no pipeline declaration, or one lacking a field the running workflow requires
- **THEN** discovery SHALL fail the workflow with a message naming that directory and the missing field, rather than omitting the stack from the matrix

#### Scenario: Discovery finding no stack fails rather than reporting success
- **WHEN** discovery over `terraform/stacks/` yields an empty set
- **THEN** the workflow SHALL fail with a message identifying discovery as the cause, and SHALL NOT allow a dependent job to be skipped and reported as successful

#### Scenario: A stack declaring nothing about the platform stack does not receive it
- **WHEN** a stack directory is added carrying a declaration that says nothing about whether the shared platform stack is deployed to it
- **THEN** no platform deploy SHALL be attempted for that stack, and every other workflow SHALL cover it as usual

#### Scenario: A stack opting in without authorising the deploy on its host is refused
- **WHEN** a stack's declaration states that the shared platform stack is deployed to it, and the host vars file of the host it provisions does not enumerate the platform application among that host's deploy-key authorisations
- **THEN** the required status check SHALL fail on the pull request, naming both files, rather than leaving the deploy to fail authenticating with a key the host does not authorise

#### Scenario: A host authorising the deploy key before the pipeline is pointed at it is accepted
- **WHEN** a host vars file enumerates the platform application among that host's deploy-key authorisations and that stack's declaration does not opt in to the platform deploy
- **THEN** discovery and the required status check SHALL both accept the tree, that interval being the deliberate state of a host prepared before its deploy path exists

#### Scenario: Two stacks in one environment each owe their own authorisation
- **WHEN** two stacks declare the same Ansible group and both opt in to the platform deploy, and only one of the two hosts enumerates the platform application among its deploy-key authorisations
- **THEN** the required status check SHALL fail for the stack whose host does not, naming that stack and the host vars file expected of it
- **AND** the authorisation present on the other host SHALL NOT be read as satisfying it
