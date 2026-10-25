## MODIFIED Requirements

### Requirement: Conditional Prod Volume Creation
The `main-production` stack SHALL expose a boolean variable that controls whether the volume module creates any resources, independent of the rest of the volume's configuration (size, name).

**The `main-production` volume's existence SHALL depend on the volume-enabled variable alone, not on the server's own toggle.** The volume declares a location of its own (see Requirement: Volume Attached to Prod Server at Creation), so it can exist while no server does. With the server disabled the volume SHALL be kept, detached, and with the server re-enabled it SHALL be attached to the new server. This is required because `main-production`'s volume holds a store admitted under *No Store on This Host Holds Data Requiring Backup* (`openspec/specs/iac-safety-hardening/spec.md`), and a volume destroyed by the toggle would discard the data that store's backups exist to recover, on an act meant only to stop a server.

**`main-staging`'s volume remains coupled to its server**, its effective existence depending on both toggles together, because it holds no store needing a backup and its server toggle exists to stop paying for staging without deleting its configuration. A stack whose volume comes to hold such a store SHALL be decoupled in the same change that admits it.

Configuration values SHALL remain declared in the stack's variables and non-secret tfvars regardless of either toggle's current value, so re-enabling the volume requires changing only the toggle(s), not restoring deleted configuration.

**The volume's name SHALL NOT carry the role of the server it is attached to.** A volume is project-local, so it is distinguished from a second volume in the same stack by rank rather than by what uses it; a name describing the consumer is one that becomes wrong when a second consumer appears, and a name is not what any consumer resolves. The on-host mount path is derived from the volume's **id** (`/dev/disk/by-id/scsi-0HC_Volume_<id>`), not from its name, so renaming the volume SHALL NOT disturb an existing mount.

#### Scenario: Toggle enabled creates the volume
- **WHEN** the `main-production` stack's volume-enabled variable is `true` and its server is also enabled
- **THEN** `terraform plan` SHALL show the `main` volume and its configuration exactly as declared, attached to that server

#### Scenario: Volume toggle disabled creates nothing
- **WHEN** the `main-production` stack's volume-enabled variable is `false`
- **THEN** `terraform plan` SHALL show no volume resource, and any previously-created volume SHALL be planned for destruction

#### Scenario: Disabling the server keeps the production volume
- **WHEN** the `main-production` stack's server toggle is `false` and its volume-enabled variable is `true`
- **THEN** `terraform plan` SHALL NOT plan the volume's destruction or replacement, and the volume SHALL carry no server reference in configuration

#### Scenario: Disabling the server also removes the volume
- **WHEN** the `main-staging` stack's server toggle is `false`, regardless of its volume-enabled variable's value — staging only, its volume being coupled to its server
- **THEN** `terraform plan` SHALL show no volume resource for that stack, and any previously-created volume SHALL be planned for destruction

#### Scenario: Re-enabling requires no lost configuration
- **WHEN** the volume-enabled variable and the server's own toggle are both changed back to `true`
- **THEN** the volume SHALL be planned for creation, or, where it was kept, for attachment to the new server, using the same size and name already present in the stack, with no additional values needing to be reconstructed

### Requirement: Volume Attached to Prod Server at Creation
Where the stack's server exists when the volume is created, the volume SHALL be attached to it at creation by setting the volume's server reference, rather than created unattached and attached in a separate step.

The volume and its server SHALL share one location, since Hetzner requires it. A stack whose volume is coupled to its server (`main-staging`) SHALL let the volume take its location from that server rather than declaring one. A stack whose volume survives the server toggle (`main-production`) SHALL declare the volume's location from **the same variable** the server's location is taken from, so that the two cannot diverge; a separately specified value is not permitted. That declared location SHALL be passed to the volume only while the stack's server toggle is false, because Hetzner's client refuses a volume created with both: a volume created with its server enabled takes its location from that server, and one created without takes the declared value. **The choice SHALL turn on a value known at plan time** — the toggle, not the server reference — because a server being re-created has no id until apply, and an unknown location plans the volume's replacement.

Adopting a declared location for a volume that already exists SHALL NOT replace it: the location declared SHALL be the one the volume already has.

#### Scenario: Volume is created already attached
- **WHEN** the `main` volume is created with its stack's server enabled
- **THEN** the volume SHALL be attached to that server, with no separate attachment step required after creation

#### Scenario: Volume shares the server's location
- **WHEN** the `main` volume is created
- **THEN** its location SHALL match its stack's server's location — derived from the attachment whenever the server is enabled, or taken from the stack's one location variable when a surviving volume is created with no server

#### Scenario: Declaring the existing volume's location changes nothing
- **WHEN** the `main-production` stack first declares its existing volume's location
- **THEN** `terraform plan` SHALL show no change to that volume

#### Scenario: Re-enabling the server does not replace the kept volume
- **WHEN** `main-production`'s server toggle changes from `false` to `true` with its volume kept
- **THEN** `terraform plan` SHALL plan the volume's attachment to the new server in place, and SHALL NOT plan its replacement
