---
kind: change
waits_on: []
design_with: []
recorded_by: provision-commerce-ops-database-in-the-shared-instance
re_checked: 2026-10-19
---

*Single Shared PostgreSQL Instance, Per-Application Databases* (`openspec/specs/iac-platform-services/spec.md`) obliges automating how an application's database and role are provisioned in the shared instance and how the role's password reaches the application. The trigger fired on 2026-09-13 (`commerce-ops` on staging; production followed). Both were provisioned by hand from the recipe in `docs/onboard-an-application.md`, and the requirement carries a paragraph, "One divergence is stated rather than hidden, as of 2026-09-13", saying it is unmet until this lands.

A design must answer: where the password is generated and how it reaches the application's deploy without a command line, log line or file in this repository; what happens when the secret name is already taken (production's `commerce-ops` already held `POSTGRES_PASSWORD`, so the shared-instance password became `SHARED_POSTGRES_PASSWORD`); that a re-run is a rotation picked up only on the application's next deploy; re-provisioning after a rebuild or store reset; and per-host independence, so one leaked credential reaches one host.

- **Kind**: It owes a MODIFIED delta on *Single Shared PostgreSQL Instance, Per-Application Databases* replacing the divergence paragraph, an update of `docs/onboard-an-application.md` and `platform/README.md`'s "Getting a database inside the instance", and a design of the credential path.
- **Recorded by**: `provision-commerce-ops-database-in-the-shared-instance`, which provisioned by hand because a mechanism fitted to one consumer would be discovered wrong by the next.
