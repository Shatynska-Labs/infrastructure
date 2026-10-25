---
kind: change
waits_on: []
design_with: [unify-the-workflows-own-role-discovery]
recorded_by: promote-molecule-to-a-required-check
re_checked: 2026-10-19
---

`molecule test --all` stops at a role's first failing scenario and omits the rest from the SCENARIO RECAP, so a red run under-reports while looking complete. Molecule's `--continue-on-failure` needs `--workers`, which refuses outside collection mode (observed 2026-09-07). The remedy is an `ansible-verify.yml` matrix over **scenarios** rather than roles (`molecule (${{ matrix.role }})` today), which also parallelises the longest role. It is not the shared-state hazard, which per-working-tree namespacing already closed.

The same change bounds each job. No workflow sets `timeout-minutes`, so jobs inherit 360 minutes, and `ansible-verify` is a required check: a hung scenario leaves a pull request pending six hours. `AGENTS.md`'s Molecule section describes ways a run hangs. The value must sit above the slow-but-green ceiling and below six hours, chosen against durations measured after `cache-the-apt-index-within-a-converge` and per-scenario jobs, and recorded in the proposal.

Must not undo (`openspec/specs/iac-cicd-pipeline/spec.md`): *Required Status Checks Report on Every Pull Request*, so the literal-named aggregating job stays as the registered check; and *Ansible Configuration Is Verified in Continuous Integration and Gates the Merge*, so scenarios are discovered from `ansible/roles/*/molecule/*/` and an empty result fails loudly.

- **Kind**: It reshapes a required check's jobs and needs an operator decision on the timeout value.
- **Design with**: `unify-the-workflows-own-role-discovery`, which reshapes the same discovery step in `ansible-verify.yml`.
- **Recorded by**: `promote-molecule-to-a-required-check`, which named it a non-goal so that the change registering the check did not also redefine it; the timeout half was recorded 2026-09-11 beside `cache-the-apt-index-within-a-converge`.
