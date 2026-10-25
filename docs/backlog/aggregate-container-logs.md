---
kind: change
waits_on: []
design_with: []
recorded_by: unknown
re_checked: 2026-10-19
---

Container logs are read by `docker logs` over SSH, per container, and are lost when a container is recreated, which every deploy does; alerts say *that* a container restarted, and the reason is in the log that just went away. Traefik's access log is on (stdout), so it now also shortens Traefik's own `docker logs` history.

Loki with an Alloy (or Promtail) collector reading the Docker socket is the stack-native answer: it joins `platform_monitoring`, uses Grafana's existing datasource provisioning pattern, bounds retention as Prometheus does, and stores on the data volume under a `platform_data_volume_subdirs` entry. `bound-host-log-growth-and-add-swap` already bounded the json-file logs it would read. Low priority while a host runs few applications.

- **Kind**: It adds platform services, owing an `iac-platform-services` delta and a retention decision.
- **Recorded by**: `unknown`.
