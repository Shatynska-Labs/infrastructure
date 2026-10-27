---
kind: change
waits_on: []
design_with: []
recorded_by: rename-the-external-services
re_checked: 2026-10-19
---

The Galaxy install (`ansible-galaxy collection install` then `role install`, from `ansible/requirements.yml`) runs with no retry, cache or fallback in `host-converge.yml`, `ansible-verify.yml` and `pr-validation.yml`. It failed transiently twice on 2026-09-12: a production converge after PR #155 (a cache-shaped "Missing expected 'results'" error) and a Molecule job on PR #161 (connection reset fetching `hetzner.hcloud`). Neighbouring identical installs passed and re-runs went green. On the gated production path the cost is a spent approval and a host left unconverged.

Must not: a blind retry would hide a genuine pin failure. `ansible/requirements.yml` pins exact versions, so "could not reach the server" must be distinguished from "this version does not exist", and only the first retried. Options in rising cost: bounded retry with backoff; `--no-cache`/`--clear-response-cache`; caching resolved collections between runs (interacts with pinning); vendoring the collections. The fix belongs to every workflow that installs Galaxy content.

- **Kind**: It needs a decision among the options and spans three workflows.
- **Recorded by**: the session that merged `rename-the-external-services` (PR #155), whose gated production converge failed on it; outside that change's subject.
