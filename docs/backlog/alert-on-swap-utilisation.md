---
kind: change
waits_on: [size-platform-container-resource-limits]
waits_for: "`size-platform-container-resource-limits`; container limits change what swap absorbs, so a threshold chosen first describes a host about to change."
design_with: []
recorded_by: bound-host-log-growth-and-add-swap
re_checked: 2026-10-19
---

Nothing alerts when swap is being consumed, the sign that a leak is underway and the OOM killer is next. `HostMemoryPressure` reads `MemAvailable / MemTotal` (RAM only), so it still fires on a leak but cannot say the last-resort tier is draining. `node_memory_SwapFree_bytes` and `node_memory_SwapTotal_bytes` are already scraped, so the rule sits beside the others in `platform/docker-compose.yml`'s inline `prometheus_rules`. Decide level (fraction used) versus rate (consumed per unit time); with no history, pick the simpler and revisit.

- **Kind**: It needs a threshold decision and owes an `iac-platform-services` alerting delta.
- **Recorded by**: `bound-host-log-growth-and-add-swap`, which added swap; this is a `platform/` change on a different pipeline, so folding it in would have needed two deploys.
