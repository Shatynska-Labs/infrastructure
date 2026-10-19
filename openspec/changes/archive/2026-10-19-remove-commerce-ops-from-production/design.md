## Context

`remove-commerce-ops-from-staging` (archived 2026-10-18) is the shape this follows. Two things differ on production:

- **A specification records the application.** *No Store on This Host Holds Data Requiring Backup* names its own PostgreSQL as this host's one unmet store.
- **There may have been data.** The backlog entry this change takes waited on the operator's word that `commerce-ops`'s production data on this host is not needed. Before this change was drafted, the host was read as `ops-claude` on 2026-10-19: `docker ps -a` lists no `commerce-ops` container, `docker volume ls` no `commerce-ops` volume, and the shared instance's `pg_database` holds only `platform_admin`, `postgres` and the templates. Its `pg_roles` holds only `platform_admin` and `pgexporter`, besides the built-in roles. Neither holds any data of the application's. One path was not read: `/opt/commerce-ops` is `deploy:deploy` mode `750`, which `ops-claude` cannot open, and a bind mount under it would be a store none of those reads reaches. The operator confirmed the removal the same day, in answer to this session's statement that it waited on their word that `commerce-ops`'s production data on this host is not needed and that `Fuperia-IT/commerce-ops` no longer deploys here. Decision 2 still reads the directory before deleting it.

## Decisions

### 1. Clean the host by hand; build no revocation mechanism

This is the same judgement `remove-commerce-ops-from-staging` Decision 1 made, on the same grounds: one revocation, on a host holding nothing of the application but its authorisation. The mechanism stays `revoke-an-application-s-deploy-authorisation`, and its entry records the second hand clean-up so the next session weighing it sees two uses.

### 2. The clean-up is the operator's, after the merge's converge

`ops-claude` holds no sudo, and the files are root-owned. Removal follows the converge the merge triggers, so that the converge cannot be read as having done it. The block reads the directory first and stops if it holds anything `deploy_user` does not render. The rest is staging's block, matching `commerce-ops`'s `authorized_keys` lines by their forced-command text alone, so no other application's lines can match, and keeping a backup until the result is read:

```sh
sudo ls -laR /opt/commerce-ops | head -50
sudo du -sh /opt/commerce-ops
```

The operator pastes that output, and the removal goes ahead only if `/opt/commerce-ops` is empty or holds only what `deploy_user` and a Compose deploy write there: a `.env` and a compose file. Anything else (a data directory, a database file, anything larger than a few kilobytes) stops the change and goes back to the operator. Then:

```sh
sudo cp -p /opt/platform/.ssh/authorized_keys /root/authorized_keys.pre-commerce-ops-removal
sudo sed -i -e '\|command="/usr/local/bin/deploy-receive commerce-ops"|d' -e '\|command="/usr/local/bin/deploy-probe commerce-ops"|d' /opt/platform/.ssh/authorized_keys
sudo rm -f /etc/sudoers.d/app-deploy-commerce-ops /etc/sudoers.d/app-probe-commerce-ops
sudo rm -rf /opt/commerce-ops
sudo visudo -c
```

To verify, the operator pastes `sudo grep -c commerce-ops /opt/platform/.ssh/authorized_keys`, expecting `0`. They also paste `sudo grep -c . /opt/platform/.ssh/authorized_keys`, expecting `8`, a deploy line and a probe line for each of `platform`, `shatynskyj`, `portfolio` and `basis-api`, and `ls /etc/sudoers.d`. This session reads `/opt` itself. What it cannot read is recorded as the operator's pasted output, not ticked on its own word.

### 3. The divergence is deleted, not rewritten as resolved

So is the requirement's sentence introducing it ("One further store, an application's own, does not satisfy it and is named below"), which would otherwise announce an unmet store and name none.

The paragraph says that resolving it takes two steps: the migration, in that application's own repository, and "the deletion of this paragraph". The application has left the host, and its data with it, which settles the first step another way. A sentence saying the divergence was resolved would be history inside a requirement, which describes the host as it is. History belongs in this change's record. The scenario *The stated divergence is not a precedent* is rewritten rather than removed. Its WHEN named `commerce-ops`. It now covers any application's store, and any divergence this requirement states later, and still says that neither is permission. It keeps its title because a MODIFIED block must carry every scenario the current requirement has, by name: OpenSpec refuses to drop one, and refuses a REMOVED and an ADDED of the same requirement in one delta.

### 4. The runbook test requires no unmet store; it names no application

`test_the_rebuild_runbook_records_its_rehearsal.py` pins `UNMET_STORE = "commerce-ops"` because the requirement recorded exactly one. *A Host's Rebuild Procedure Is Recorded, and Its Rehearsal State With It* (`openspec/specs/iac-server-lifecycle/spec.md`) obliges the runbook to "name any store that requirement records as unmet", which with none recorded obliges nothing. The test changes so that the set of stores it requires the runbook to name is an empty literal, with a comment saying the requirement records none since this change; it does not parse the requirement. Its negative case keeps showing that a store the requirement does record must be named. The `test-plan.md`'s obsolete-test entry for it is where that judgement is recorded. The edit changes which store is expected, never what the runbook must say about one.

### 5. Which sentences change

A sentence stating a present fact about `commerce-ops` on production changes. A sentence recording what happened, or using `commerce-ops` as an example name, stays. Rewritten or deleted:

- the runbook's "On `main-production` there is a third" paragraph;
- its phase 14 sentence "`main-production` carries `commerce-ops`";
- its phase 15 aside about `commerce-ops`'s `Deploy` trigger, rewritten without naming an application;
- its `/health` example, rewritten without naming an application;
- the onboarding guide's production-divergence paragraph;
- `platform/README.md`'s sentence about a production database reserved for a cutover, and its sentence that `commerce-ops-postgres-1` and `commerce-ops_commerce_ops_pgdata` on the production host are not this instance;
- `docs/onboard-an-application.md`'s comment-convention paragraph, which cites `commerce-ops-deploy` in `main-production.yml` as a committed entry;
- `docs/bootstrap-a-new-host.md`'s statement that both `host_vars` files carry a `commerce-ops` entry, which has been false of staging since 2026-10-18;
- the comments in `main-production.yml` that name `commerce-ops`, compare its keys with `main-staging.yml`'s, or count "the two deploy keys here".
