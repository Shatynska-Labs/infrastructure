---
kind: change
waits_on: []
design_with: [say-production-is-no-longer-reviewer-gated]
recorded_by: rename-the-external-services
re_checked: 2026-10-19
---

`apply.yml` names a clean failure for a missing or expired plan artifact. A stale saved plan only gets Terraform's raw `Error: Saved plan is stale`. That is the gate working: *Gated Production Apply Applies the Reviewed Plan* demands the exact reviewed plan. The change owes a named failure for this case: what staleness means, that no infrastructure change was lost, and that recovery is a **fresh run of the whole workflow** (re-running the failed job re-downloads the same stale artifact). It must not auto-replan, which would apply an unreviewed plan.

Observed 2026-09-12 on the merge of `rename-the-external-services` (PR #155): production's state serial moved 44 → 45 between plan and apply with no attribute changed, so a no-op operation still invalidates a saved plan. A local `terraform plan` under the read-only token was measured not to bump the serial; CI, the operator's checkout, the change's working trees and HCP health assessments were ruled out. The workspace's **States** view in HCP, which labels each version's source, is the unread avenue. Since 2026-10-11 `main-production` carries no required reviewer, so apply follows plan by seconds and the window is narrow; it widens again if a reviewer returns.

- **Kind**: It needs a decision on whether the message names likely causes, and, if a permitted local operation can invalidate a pending apply, an `AGENTS.md` rule change.
- **Design with**: `say-production-is-no-longer-reviewer-gated`, which decides whether the approval window that makes a plan perishable exists at all.
- **Recorded by**: the merge of `rename-the-external-services` (PR #155), whose apply failed this way; the error-handling gap was outside that change's subject.
