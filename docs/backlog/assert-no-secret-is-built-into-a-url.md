---
kind: change
waits_on: []
design_with: []
recorded_by: "the 2026-09-15 fix to postgres-exporter's connection settings"
re_checked: 2026-10-19
---

postgres-exporter's `DATA_SOURCE_NAME` once interpolated a password into a URL, and a `#` in it discarded the host (see `alert-on-the-exporter-being-unable-to-read-postgres`). That is fixed (`DATA_SOURCE_URI`/`_USER`/`_PASS` in `platform/docker-compose.yml`); owed is a static check in `.github/tests` stopping the shape returning.

The rule: a secret-bearing variable inside a URL, within its own whitespace-delimited word. Offences: a scheme URL, a scheme-less `user:secret@host` authority, a query parameter, a path segment of a scheme-less authority, text concatenated onto a secret that is itself a URL. Not offences: a value that is only the secret (Alertmanager's `api_url`), a non-secret host, a secret beside an unrelated URL, a filesystem path, Compose's `$$`. The defect that recurred in three review rounds: each arm must read the quote-stripped neighbourhood, not anchor to the raw word's start, since quoting in `configs:` and `--flag=value` in `command:` are idiomatic.

Must read: secret names from `platform-deploy.yml`'s render step `env:` block, not keywords (`DEADMANSWITCH_URL` is a bearer credential); and `command:`, `entrypoint:`, `labels:`, `healthcheck.test`, `environment:` and inline `configs:` (`${ACME_EMAIL}` is only in `command:`). It must not pass having read nothing: assert a floor of interpolations found.

- **Kind**: It owes a requirement stating the rule the check enforces (`iac-platform-deploy-pipeline`), and its earlier draft did not fit one review sitting.
- **Recorded by**: the 2026-09-15 fix to postgres-exporter's connection settings (change name not recorded), from which the check was split because its draft was wrong in three rounds of review.
