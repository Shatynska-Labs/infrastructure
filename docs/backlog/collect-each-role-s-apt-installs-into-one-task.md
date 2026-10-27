---
kind: change
waits_on: []
design_with: []
recorded_by: cache-the-apt-index-within-a-converge
re_checked: 2026-10-19
---

`hardening` installs `ufw` and `fail2ban` as two `apt` tasks where `ansible.builtin.apt` takes a list. Collapsing them reaches the case `cache-the-apt-index-within-a-converge`'s staleness bound does not: a production host with a maintained `update-success-stamp`, where `cache.update()` never advances what `get_cache_mtime()` reads, so every bounded task fetches again. It saves little in CI, where the first fetch is owed either way.

It moves things readers depend on: which task a failure surfaces under, what the scenarios assert (they observe `ufw` and `fail2ban` separately), and the install-then-configure ordering. Measure the production saving before proposing it.

- **Kind**: It needs a measured decision that the production saving justifies changing two roles' task structure and their scenario assertions.
- **Recorded by**: `cache-the-apt-index-within-a-converge` (its Non-Goals); a larger refactor of two roles than that bound.
