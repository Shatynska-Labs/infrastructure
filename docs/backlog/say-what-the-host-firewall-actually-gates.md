---
kind: change
waits_on: []
design_with: [put-the-remaining-host-scoped-variables-on-the-host-axis]
recorded_by: onboard-commerce-ops-to-staging
re_checked: 2026-10-19
---

A container-published port is not filtered by UFW on any interface: Docker DNATs it in `nat/PREROUTING` and accepts it in `FORWARD`, and UFW's rules hang off `INPUT`. So `hardening_web_allowed_cidrs` gates nothing for Traefik's `80`/`443` (published on all addresses), and the Hetzner cloud firewall alone refuses public traffic (measured on staging 2026-09-13 with UFW active and both CIDR lists empty: 301 and 404 over the tailnet). Nothing in `ansible/roles/` touches `DOCKER-USER` or `after.rules`.

This falsifies the two-layer statement where it is still made unqualified: `AGENTS.md`'s *Firewall split*, the requirement *Host-Level Security Owned by Ansible, Cloud Firewall Owned by Terraform* ("exactly one layer SHALL be the documented access gate"), and `ansible/roles/hardening/README.md` (its sync and *Tailnet-scoped rules* sections). Each must say which ports it is true of. `docs/bootstrap-a-new-host.md`, `docs/onboard-an-application.md` and `check-public-endpoints-from-outside` already say it correctly. The `terraform.tfvars`/`group_vars` mirror obligation still holds for every port UFW does gate.

Settle first: `add-grafana-tailnet-ufw-rule` (archived) added a UFW allow for 3000 because Grafana was unreachable from the tailnet, and `hardening/README.md` still says that rule "is what actually lets tailnet peers reach it", yet Grafana is a container-published port (`${GRAFANA_BIND_ADDRESS}:3000`), which UFW should never filter. Either that diagnosis was wrong or something distinguishes the case. This is a documentation defect, not an exposure; whether to close container ports at the host layer too (`DOCKER-USER`, or publishing to `127.0.0.1`) is a separate change this one does not prejudge.

- **Kind**: It owes an `iac-host-configuration` delta to *Host-Level Security Owned by Ansible, Cloud Firewall Owned by Terraform* saying which layer gates a container-published port, and an investigation of the Grafana case before the rule is written.
- **Design with**: `put-the-remaining-host-scoped-variables-on-the-host-axis` (its firewall-pair decision depends on which ports UFW gates).
- **Recorded by**: `onboard-commerce-ops-to-staging`, whose code review probed the host and caught documents asserting the opposite; that change corrected only `group_vars/staging.yml`'s comment, which it was already editing.
