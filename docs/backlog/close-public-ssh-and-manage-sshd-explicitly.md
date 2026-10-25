---
kind: change
waits_on: []
design_with: [notice-a-pending-reboot-and-decide-what-does-it]
recorded_by: unknown
re_checked: 2026-10-19
---

Port 22 is open on the cloud firewall and in UFW to one ISP `/24` (`ssh_allowed_cidrs` in each stack's `terraform.tfvars`, mirrored as `hardening_ssh_allowed_cidrs` in `group_vars`). Every non-operator path, `host-converge.yml` included, already reaches hosts over the tailnet, which `ansible/roles/hardening/tasks/main.yml` admits independently from `100.64.0.0/10` (that task's own comment calls an empty public list "safer than what prod runs"), so the public rule serves only the operator, who is on the tailnet too. Closing it means `ssh_allowed_cidrs = []`, which `terraform/modules/server/variables.tf` refuses on lockout grounds; that validation is what to revisit. The Terraform and UFW rules move together (*Host-Level Security Owned by Ansible, Cloud Firewall Owned by Terraform*), and the recovery path when the tailnet is unreachable is Hetzner's console, which the cloud firewall does not gate.

Must not break: the public address is the only path for a host's *first* converge (`docs/bootstrap-a-new-host.md` §6.3, `docs/runbook-rebuild.md`'s converge phase), since that play is what joins the tailnet. The change must say how a new or rebuilt host is bootstrapped afterwards (a temporarily widened `ssh_allowed_cidrs` through the pipeline, or the console). It must not precede a converge pipeline seen to work over more than one production run; the ISP `/24` is the fallback for a converge that wedges `tailscaled`.

Also here: `sshd_config` (no drop-in under `/etc/ssh/sshd_config.d/`; `PasswordAuthentication` unset, harmless only because no account has a password) runs on the image's defaults although `iac-host-configuration` assigns SSH hardening to Ansible. It belongs to `hardening` and can be asserted by its Molecule scenario. The `unattended-upgrades` reboot half is `notice-a-pending-reboot-and-decide-what-does-it`.

- **Kind**: It needs the operator's policy decision to close public SSH and to choose the bootstrap path, and owes deltas to the server module's lockout validation and to `hardening`'s managed `sshd_config` (`iac-host-configuration`).
- **Waits on**: It used to wait on the host converge moving into the pipeline, which `apply-host-configuration-through-a-gated-workflow` delivered.
- **Recorded by**: `unknown`; the entry predates the tailnet-based converge and was kept as a policy decision the `hardening` role anticipates.
