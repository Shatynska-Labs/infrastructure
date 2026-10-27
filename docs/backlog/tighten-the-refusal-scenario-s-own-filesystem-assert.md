---
kind: fix
waits_on: []
design_with: []
recorded_by: namespace-the-molecule-loop-devices
re_checked: 2026-10-19
---

`ansible/roles/platform_data_volume/molecule/superseded-path-in-force-refused/verify.yml` asserts `platform_data_volume_blkid.rc != 0` to show the role refused before formatting. It fails open: `blkid` returns 1 on a usage error, so a probe that did not happen reads as "no filesystem". Tighten it to `rc == 2`, the only code meaning "looked, found nothing" (measured in the pinned image: unformatted 2, formatted 0, usage error 1, absent device 2), as the role's `prepare.yml` plays already were.

A second, separate hazard that tightening does not close: `prepare.yml`, `converge.yml` and `verify.yml` each redeclare `platform_data_volume_fixture_loop_minor` (`base + 4`) by hand. A drifted `verify` probes an unassociated minor, gets rc 2 and passes. Either derive the minor from one place, or have `verify` assert that its device is the one `prepare` associated; do not close one believing it closed the other.

- **Kind**: A test-only tightening with no delta or decision.
- **Recorded by**: `namespace-the-molecule-loop-devices`, whose code review found it in a line that change did not author.
