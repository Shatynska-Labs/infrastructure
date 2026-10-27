---
kind: change
waits_on: []
design_with: []
recorded_by: render-the-env-file-so-a-secret-survives-it
re_checked: 2026-10-19
---

`platform-deploy.yml` escapes each value written into `platform/.env` (double quotes, `\` → `\\`, `"` → `\"`, `$` → `$$`, in that order) so Compose's dotenv parser reconstructs it. That rule is a fact about a parser version (measured on Compose v5.4.0; the host ran v5.5.0 the same day), and both move under Dependabot and host package updates. A diverging parser does not fail the deploy: the service starts healthy and fails wherever it needed the credential. `.github/tests` checks only that the escaping exists and is ordered.

Close it with a deploy-time round trip on the host: render, parse back with the host's own Compose, compare digests rather than values (disclosure-free), refuse the deploy on any mismatch. `tools/env-rendering-probe/` has the harness, both consumption paths and the value corpus.

- **Kind**: It adds a deploy-time refusal owing an `iac-platform-deploy-pipeline` delta to *Platform Secrets Rendered from CI at Deploy Time*.
- **Recorded by**: `render-the-env-file-so-a-secret-survives-it`, which measured the rule but could not arrange detection; the check belongs to the deploy path.
