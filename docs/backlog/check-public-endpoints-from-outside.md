---
kind: change
waits_on: []
waits_for: "the operator's choice of an external uptime service."
design_with: []
recorded_by: alert-on-certificate-expiry
re_checked: 2026-10-19
---

Nothing checks from outside a host that a public hostname resolves and answers on 443. Two failures remain unseen: a cloud-firewall change blocking 443 made at the console (the drift workflow reports only Terraform-managed state; UFW is not in 443's path, see `say-what-the-host-firewall-actually-gates`), and DNS failures with no edit behind them, since both zones use third-party nameservers (`docs/bootstrap-a-new-host.md` §4.4). An expiring certificate is already covered by `alert-on-certificate-expiry`; a hostname served no certificate at all is not. A host-local `blackbox-exporter` cannot see the cloud firewall, since traffic to its own address never leaves the host.

What is left is an external uptime service with a check per hostname, independent of the host as the Watchdog is. healthchecks.io takes only inbound pings, so this is likely a second vendor account.

- **Kind**: It needs the operator's decision on an external uptime vendor and its cost.
- **Recorded by**: `unknown`; narrowed on 2026-09-09 by `alert-on-certificate-expiry`, which delivered the certificate half.
