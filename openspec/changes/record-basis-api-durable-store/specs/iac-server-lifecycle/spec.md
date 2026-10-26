## MODIFIED Requirements

### Requirement: Conditional Prod Server Creation
The `main-production` stack SHALL expose a boolean variable that controls whether the server module creates any resources, independent of the rest of that server's configuration (sizing, image, location, network CIDRs).

Configuration values SHALL remain declared in the stack's variables and non-secret tfvars regardless of the toggle's current value, so re-enabling the server requires changing only the toggle, not restoring deleted configuration.

Other resources MAY be coupled to a stack's server toggle where their own configuration makes them unable to exist without the server — `main-staging`'s `main` volume, coupled to `main-staging`'s toggle, has no location of its own and therefore exists only while its server does. `main-production` has no such resource today. A resource holding a store admitted under *No Store on This Host Holds Data Requiring Backup* (`openspec/specs/iac-safety-hardening/spec.md`) SHALL NOT be coupled to it: `main-production`'s `main` volume declares its own location and is detached, not destroyed, when the server is disabled (`iac-data-volumes`, *Conditional Prod Volume Creation*).

#### Scenario: Toggle enabled creates the server
- **WHEN** the `main-production` stack's server-enabled variable is `true`
- **THEN** `terraform plan` SHALL show the server, its firewall, and their configuration exactly as declared

#### Scenario: Toggle disabled creates nothing
- **WHEN** the `main-production` stack's server-enabled variable is `false`
- **THEN** `terraform plan` SHALL show no server or firewall resources, and any previously-created ones SHALL be planned for destruction

#### Scenario: Toggle disabled also removes resources coupled to the server
- **WHEN** the `main-production` stack's server-enabled variable is `false`
- **THEN** `terraform plan` SHALL also show any resource that has no independent location or existence apart from the server planned for destruction, not left dangling or erroring for want of the server it depends on — a scenario with no subject in `main-production` while it has no such resource

#### Scenario: Toggle disabled keeps the production volume
- **WHEN** the `main-production` stack's server-enabled variable is `false` and its volume-enabled variable is `true`
- **THEN** `terraform plan` SHALL plan the server's destruction and SHALL NOT plan the `main` volume's destruction or replacement

#### Scenario: Re-enabling requires no lost configuration
- **WHEN** the server-enabled variable is changed back from `false` to `true`
- **THEN** the server SHALL be planned for creation using the same sizing, image, location, network configuration, and SSH key already present in the stack, with no additional values needing to be reconstructed and no additional resources needing to be re-imported, and a kept volume SHALL be planned for attachment to it
