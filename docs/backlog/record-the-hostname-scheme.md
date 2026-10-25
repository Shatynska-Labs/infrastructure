---
kind: change
waits_on: []
design_with: []
recorded_by: expose-staging-on-the-web
re_checked: 2026-10-19
---

Public names follow `<service>.<server>.BASE_DOMAIN` (`<app>.main-production.BASE_DOMAIN`, `<app>.main-staging.BASE_DOMAIN`), resolved by one wildcard `A` record per server, with short aliases as records of their own. The rule was decided in the `commerce-ops` repository, whose `deploy-commerce-ops-to-staging` handoff names `docs/naming-conventions.md` here as its home, but that file names servers, stacks, keys and the OS hostname and not public names. It owes: the rule, where the base domain comes from, and how it composes with the `<company>` segment and the stack name that file already rules on (a company-owned base domain is an axis `<company>` does not cover). `docs/bootstrap-a-new-host.md` §4.4 describes the wildcard shape (and now `BASE_DOMAIN`/`COMPANY_DOMAIN` record tables) and should then point at the rule rather than restate it.

- **Kind**: Documentation only, but how a company-owned base domain composes with `<company>` is a naming decision the operator has not made.
- **Recorded by**: `expose-staging-on-the-web` (archived 2026-09-15), which wrote down the DNS the scheme produces but not the scheme.
