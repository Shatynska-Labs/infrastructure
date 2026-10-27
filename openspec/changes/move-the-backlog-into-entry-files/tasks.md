## 1. Convert the backlog

- [ ] 1.1 In a commit holding nothing else but 1.2's values (design D7), run ai-toolkit's `scripts/backlog-migrate` from its merged `main` against this tree. Verify it reports `Outcome: SUCCESS` and as many entries as `docs/backlog.md` had headings, that `docs/backlog.md` is gone, and that every entry's frontmatter parses as YAML.
- [ ] 1.2 Set the `recorded_by` values the converter left out or mis-set, as design D5 directs. Verify that each entry carrying `recorded_by` names a change or a quoted text its body's **Recorded by** line supports.
- [ ] 1.3 In a commit of its own, add the backlog fix `repoint-the-backlog-references` (design D6).

## 2. Move the workflow block to v12

- [ ] 2.1 Replace `AGENTS.md`'s development-workflow block with ai-toolkit's v12 fragment, marker `v12`, and seed `docs/workstreams/README.md` with `project-init` (design D4). Verify the block matches the fragment's body exactly.
- [ ] 2.2 Repoint the two `docs/backlog.md` pointers in `AGENTS.md`'s project conventions to `docs/backlog/` (design D6).

## 3. Cite the backlog's new location

- [ ] 3.1 Apply the two MODIFIED deltas to the requirements' citations (design D1); they are applied to the main specifications on archive.
- [ ] 3.2 Update `test_the_shared_instance_has_its_first_database.py`, `test_a_deploy_key_is_bound_to_one_host.py` and `test_basis_api_durable_store.py` so that each reads the entry's own file (design D2), and repoint the `docs/backlog.md` pointers in the constants, messages and docstrings this edits (design D6), alongside the tests the derivation adds.
- [ ] 3.3 Point `test_the_shared_instance_store_moved.py`'s line exemption at the entry file now holding that line (design D3), with its comment's pointers.
- [ ] 3.4 Add a static test, unless the derivation already carries it, that fails where a requirement in `openspec/specs/` or a live delta cites `docs/backlog.md`, reading a requirement a live MODIFIED delta shadows from that delta, and that fails while `docs/backlog.md` exists (design Risks).

## 4. Verify

- [ ] 4.1 Run `python3 -m unittest discover --start-directory .github/tests` with every new file staged, since several sweeps read tracked files only. Verify it passes with the same skips as the baseline.
- [ ] 4.2 Run `openspec validate --all` and `pre-commit run --all-files`, including `gitleaks` over the new entry files.

## 5. Ship

- [ ] 5.1 Regenerate the conversion on the freshly fetched trunk (design D7): drop the conversion commit, rebase onto the trunk, re-run 1.1 and 1.2 as a new commit over whatever has merged since, and give any requirement a merged branch brought into the main specifications citing `docs/backlog.md` a MODIFIED delta of its own; a citation inside another live change's delta is corrected in that delta. Then 4.1 and 4.2.
- [ ] 5.2 Open the pull request, with the converter's report and D7's notice to the branches in flight. Nothing in it reaches a host, so `confirm` is to be waived as a change with no observation to make, on the operator's word, and the waiver recorded here.
- [ ] 5.3 Archive the change: delete the backlog entry `move-the-backlog-into-entry-files`, run `openspec archive move-the-backlog-into-entry-files --yes`, and open the record's pull request.
