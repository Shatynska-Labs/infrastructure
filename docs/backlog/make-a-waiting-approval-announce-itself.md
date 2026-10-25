---
kind: change
waits_on: [say-production-is-no-longer-reviewer-gated]
waits_for: "a required reviewer being restored on the `main-production` Environment. It was removed on 2026-10-11 (`say-production-is-no-longer-reviewer-gated`; `gh api …/environments` shows no protection rules), so today nothing waits."
design_with: [say-production-is-no-longer-reviewer-gated]
recorded_by: rename-the-external-services
re_checked: 2026-10-19
---

Nothing tells the operator that a gated run is waiting for approval. On 2026-09-12 a production converge sat unapproved 06:26–09:56, and on 2026-09-13 one waited 6h34m. Each was found only because a later run queued behind it (`waiting on converge (main-production) … to complete`, which reads like a hung job). The Terraform apply, the host converge and the platform deploy gate on the same Environment and render indistinguishable prompts, and a pending approval stalls every later converge of that stack.

Measure first whether GitHub's *deployment review requested* notification exists and simply is not reaching the operator; if so, this is a settings change plus a sentence in `docs/bootstrap-a-new-host.md` §6.6. Otherwise, a scheduled query of `gh run list --status waiting` pushed somewhere read, repeating while the state persists. Trap: Alertmanager's `SLACK_WEBHOOK_URL` comes from `PLATFORM_SLACK_WEBHOOK_URL`, a production-Environment secret, so a notifier using it gates on the approval it announces; its credential must be ungated. It must not fire on every run.

- **Kind**: It needs operator decisions on the channel and the credential source, and may add a scheduled workflow (with its heartbeat obligation).
- **Recorded by**: `rename-the-external-services`, which lost three and a half hours to it and recorded only the recognition advice.
