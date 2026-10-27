---
kind: change
waits_on: []
design_with: []
re_checked: 2026-10-19
---

No service in `platform/docker-compose.yml` declares a memory or CPU limit on a `cx33`, so one container can starve the host; `ContainerRestartingOrOOMKilled` only alerts on the consequence. Size limits from observed steady state and peak (`container_memory_usage_bytes`, on the "Container health" dashboard), not by guess: limits picked without evidence cause the outage they were meant to prevent.

- **Kind**: It needs sizing decisions from measured data across every platform service.
- **Waits on**: It waited on data; metrics have accumulated on production since `add-platform-monitoring` (2026-09-04). Staging was rebuilt on 2026-10-18, so its history is short.
- **Recorded by**: `unknown`.
