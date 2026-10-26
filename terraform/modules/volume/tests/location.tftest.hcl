# modules/volume's optional `location`, and the exactly-one rule between it and
# `server_id`.
#
# Derived from the delta specs of the OpenSpec change
# `record-basis-api-durable-store`, before any implementation of it existed. The
# path those deltas sit at is not written here (this repository cites a change
# and its artifact by name, in prose). See that change's `test-plan.md` for the
# scenario-to-test mapping, the recorded baseline, and the per-assertion
# classification.
#
# Requirements traced:
#   - *Volume Attached to Prod Server at Creation*
#     (openspec/specs/iac-data-volumes/spec.md): "a volume created with its
#     server enabled takes its location from that server, and one created
#     without takes the declared value"; "Hetzner's client refuses a volume
#     created with both".
#   - *Conditional Prod Volume Creation* (same file), scenario "Disabling the
#     server keeps the production volume".
#
# WHAT THIS FILE CANNOT REACH, stated so its green is not over-read: the
# stack's `count` and its choice of `location` on `server_enabled` live in
# terraform/stacks/main-production/, outside this test-path glob, and are
# asserted statically by `.github/tests/test_basis_api_durable_store.py`. Nor
# can it assert that `server_id`/`location` is NULL on the resource when the
# module was given null: both are `Optional, Computed` in the hcloud provider,
# so under `mock_provider` a null input plans as an unknown value, and an
# assertion over it cannot be evaluated. What is asserted is what the module
# forwards when it is given a value, and what it refuses.
#
# mock_provider avoids any real Hetzner API call -- see creation.tftest.hcl for
# the shared rationale. `command = plan` throughout.

mock_provider "hcloud" {}

variables {
  environment = "production"
  name        = "main"
  size        = 10
  tenant      = "main"
}

# SPECIFIED -- "one created without [a server] takes the declared value", and
# scenario "Volume shares the server's location": "taken from the stack's one
# location variable when a surviving volume is created with no server".
# `fsn1` rather than `hel1`, so a location the module hardcoded to the value
# production uses could not pass.
run "plan_forwards_the_declared_location_when_no_server_is_given" {
  command = plan

  variables {
    server_id = null
    location  = "fsn1"
  }

  assert {
    condition     = hcloud_volume.this.location == "fsn1"
    error_message = "hcloud_volume.this.location was not set from var.location while no server_id was given -- a volume kept with its server disabled would have no location to exist in"
  }
}

# SPECIFIED -- scenario "Volume is created already attached", with `location`
# now an input the module accepts: given a server and an explicitly null
# location, the server reference is still forwarded.
run "plan_forwards_server_id_when_location_is_null" {
  command = plan

  variables {
    server_id = "12345"
    location  = null
  }

  assert {
    condition     = hcloud_volume.this.server_id == 12345
    error_message = "hcloud_volume.this.server_id was not set from var.server_id when location was null -- the volume would not be attached to its server at creation"
  }
}

# DERIVED -- design.md decision 3 ("validates that exactly one is non-null")
# and tasks.md 1.1, grounded in the requirement's "Hetzner's client refuses a
# volume created with both". The failure is expected on `var.server_id`
# because tasks.md 1.1 REPLACES server_id's existing validation with this one;
# see test-plan.md's unresolved questions for that assumption.
run "plan_rejects_both_server_id_and_location" {
  command = plan

  variables {
    server_id = "12345"
    location  = "fsn1"
  }

  expect_failures = [
    var.server_id,
  ]
}

# DERIVED -- the other half of "exactly one": a volume given neither has no
# location Hetzner can create it in. Same attachment assumption as above.
run "plan_rejects_neither_server_id_nor_location" {
  command = plan

  variables {
    server_id = null
    location  = null
  }

  expect_failures = [
    var.server_id,
  ]
}

# DERIVED -- tasks.md 1.1, "rejecting an empty string for either". An empty
# location is non-null, so the exactly-one count alone would accept it. Same
# attachment assumption as above (the single validation tasks.md 1.1 puts on
# server_id).
run "plan_rejects_an_empty_location" {
  command = plan

  variables {
    server_id = null
    location  = ""
  }

  expect_failures = [
    var.server_id,
  ]
}
