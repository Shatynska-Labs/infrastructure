variable "tenant" {
  description = "Tenant this volume belongs to (e.g. \"main\"). Applied as the `tenant` label. An input rather than a literal, so a second tenant can consume this module unchanged."
  type        = string

  validation {
    condition     = length(trimspace(var.tenant)) > 0
    error_message = "tenant must not be empty."
  }
}

variable "environment" {
  description = "Environment name this volume belongs to, spelled in full (e.g. \"production\"). Applied as the `environment` label."
  type        = string

  validation {
    condition     = length(trimspace(var.environment)) > 0
    error_message = "environment must not be empty."
  }
}

variable "name" {
  description = "Name of the volume. A volume never leaves its Hetzner project, so it is named on the rank axis (\"main\") rather than for what consumes it. The on-host mount path is derived from the volume's id (`/dev/disk/by-id/scsi-0HC_Volume_<id>`) and not from this name, so renaming a volume does not disturb an existing mount."
  type        = string
}

variable "size" {
  description = "Size of the volume in GB."
  type        = number
}

variable "server_id" {
  description = "ID of the hcloud_server this volume attaches to, or null. Exactly one of server_id and location is set: the provider refuses a create naming both. A volume created with server_id is attached at creation and takes that server's location."
  type        = string
  default     = null

  validation {
    condition     = var.server_id == null ? true : length(trimspace(var.server_id)) > 0
    error_message = "server_id must not be empty -- pass null instead when the volume has no server."
  }

  # Declared on server_id because a cross-variable condition must name the
  # variable it is attached to. It also refuses an empty location, which
  # would otherwise reach the provider as a location named "".
  validation {
    condition     = var.server_id == null ? (var.location == null ? false : length(trimspace(var.location)) > 0) : var.location == null
    error_message = "Exactly one of server_id and location must be set, and neither may be empty: the provider refuses a volume created with both, and a volume with neither has nowhere to exist."
  }
}

variable "location" {
  description = "Hetzner location to create this volume in, or null. Set only when server_id is null -- a volume kept while its server is disabled. A caller choosing between the two SHALL choose on a value known at plan time, since an unknown location on this ForceNew attribute plans the volume's replacement."
  type        = string
  default     = null
}

variable "delete_protection" {
  description = "Whether to enable Hetzner's server-side delete protection on this volume. Parameterized (not a literal lifecycle.prevent_destroy) so this module stays reusable by environments that must remain destroyable, e.g. a future staging environment."
  type        = bool
  default     = true
}

variable "labels" {
  description = "Additional labels to merge onto the volume, in addition to the environment and managed_by labels applied automatically."
  type        = map(string)
  default     = {}
}
