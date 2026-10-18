## Context

`deploy_user` renders `/opt/<name>`, `/etc/sudoers.d/app-deploy-<name>`, `/etc/sudoers.d/app-probe-<name>` and two `authorized_keys` lines per `deploy_apps` entry, and removes none of them for an entry that is gone (`docs/backlog.md` `revoke-an-application-s-deploy-authorisation`).

## Decisions

### 1. Clean the host by hand; build no revocation mechanism

The backlog entry offers two routes: the removal plus on-host cleanup, or a revocation mechanism first. The mechanism is a `state: absent` model for `deploy_user` with an `exclusive`-vs-per-entry decision about `authorized_keys`, Molecule scenarios, and a decision the entry itself says is shaped like `manage-root-authorized-keys-from-a-role`. It would buy one revocation on a host with no database, no deployed container and no data to lose. The cost of the manual route is that the cleanup is an edit no converge notices; that is accepted for a single, one-off removal, and the follow-up is verified by reading the host (tasks 3.2). The mechanism stays an entry, and gains a use.

Rejected: leaving the keys. The deploy key's private half is outside this repository, in a company's GitHub Environment the operator does not want authorised here.

### 2. The cleanup is the operator's, after the entry is removed

The `ops-claude` account holds no sudo, and the removed files are root-owned. The operator runs one command block; this session reads what that account can see and asks the operator to paste the rest. Removal follows the merge so that the converge that applies the entry's deletion cannot be read as having done the cleanup.

The block matches `commerce-ops`'s `authorized_keys` lines by their forced-command text alone, so `platform`'s lines cannot match, and it keeps a backup of the file until the result is read:

```sh
sudo cp -p /opt/platform/.ssh/authorized_keys /root/authorized_keys.pre-commerce-ops-removal
sudo sed -i -e '\|command="/usr/local/bin/deploy-receive commerce-ops"|d' -e '\|command="/usr/local/bin/deploy-probe commerce-ops"|d' /opt/platform/.ssh/authorized_keys
sudo rm -f /etc/sudoers.d/app-deploy-commerce-ops /etc/sudoers.d/app-probe-commerce-ops
sudo rm -rf /opt/commerce-ops
sudo visudo -c
```

Verification is by the operator pasting `sudo grep -c commerce-ops /opt/platform/.ssh/authorized_keys` (expect `0`), `sudo grep -c . /opt/platform/.ssh/authorized_keys` (expect `platform`'s two lines), and `ls /etc/sudoers.d /opt`. Anything this session cannot read itself is recorded under `## Not performed` with its reason rather than ticked.

### 3. The runbook is rewritten, not annotated

Phases 1, 14, 15 and 16 name `commerce-ops` as staging's application. After this change that is false, and the same phases remain correct for `main-production`. They are reworded to enumerate the applications from `deploy_apps` and to carry the application-specific probe only where an application exists, without a migration narrative.
