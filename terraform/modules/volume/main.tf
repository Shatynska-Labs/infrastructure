locals {
  # Caller labels FIRST and the axes SECOND, so a caller cannot override an
  # axis. The same merge order modules/server uses, for the reason stated
  # there.
  labels = merge(
    var.labels,
    {
      tenant      = var.tenant
      environment = var.environment
      managed_by  = "terraform"
    }
  )
}

# `server_id` and `location` are both optional and exactly one is set (see
# variables.tf): the provider's client refuses a create naming both, and a
# volume needs one or the other to exist. A caller whose volume is coupled to
# its server passes `server_id` alone, and the volume takes the server's
# location. A caller whose volume survives its server toggle passes
# `location` only while the server is disabled, choosing on a value known at
# plan time -- see the record-basis-api-durable-store change's design.md,
# decision 3. `location` is ForceNew but Computed, so a null leaves the
# location already in state alone.
resource "hcloud_volume" "this" {
  name              = var.name
  size              = var.size
  server_id         = var.server_id
  location          = var.location
  delete_protection = var.delete_protection
  labels            = local.labels
}
