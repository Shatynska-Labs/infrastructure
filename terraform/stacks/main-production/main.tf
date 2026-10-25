module "server" {
  count = var.server_enabled ? 1 : 0

  source = "../../modules/server"

  # The two axes this stack is identified on, each carried as a label of its
  # own rather than as a segment of a name -- see Consistent Resource Labeling
  # (openspec/specs/iac-safety-hardening/spec.md). `production` is spelled in
  # full: `prod` and `preprod` share a prefix, and this value is read by prefix
  # in more places than it is read whole.
  tenant      = "main"
  environment = "production"

  # `main`, on the rank axis. A firewall never leaves its Hetzner project, so a
  # second one here would be the extra one and would be named beside this. It is
  # passed rather than derived: the module used to build
  # "<environment>-<name>", which would now read `production-main-production`.
  firewall_name = "main"

  name        = var.name
  server_type = var.server_type
  image       = var.image
  location    = var.location

  ssh_key_id        = hcloud_ssh_key.this.id
  ssh_allowed_cidrs = var.ssh_allowed_cidrs
  web_allowed_cidrs = var.web_allowed_cidrs

  # delete_protection = true is a prod-specific choice, not the module
  # default consumers should inherit blindly. See design.md Decision 7.
  delete_protection = true
  backups           = true
}

module "volume" {
  # The volume survives the server toggle: it holds basis-api's store,
  # admitted under *No Store on This Host Holds Data Requiring Backup*
  # (openspec/specs/iac-safety-hardening/spec.md), and a toggle that
  # destroyed it would discard what that store's backups exist to recover.
  # So its count reads volume_enabled alone, and with the server disabled it
  # is kept, detached, in the stack's own location. See the
  # record-basis-api-durable-store change's design.md, decision 3.
  count = var.volume_enabled ? 1 : 0

  source = "../../modules/volume"

  tenant      = "main"
  environment = "production"

  name      = var.volume_name
  size      = var.volume_size
  server_id = one(module.server[*].id)

  # Chosen on server_enabled, never on server_id: re-enabling the server
  # leaves its id unknown until apply, and an unknown location on this
  # ForceNew attribute would plan the volume's replacement. The provider
  # refuses a create naming both, so the location is passed only while no
  # server exists; null leaves the location already in state alone.
  location = var.server_enabled ? null : var.location

  delete_protection = true
}
