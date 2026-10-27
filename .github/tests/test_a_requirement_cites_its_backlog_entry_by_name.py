"""Static-assertion tests for the backlog moving into one file per entry.

Derived from the OpenSpec change `move-the-backlog-into-entry-files` -- its two
MODIFIED delta specifications, its `design.md` and its `tasks.md` -- at commit
`728c0df`, the commit holding the approved plan, before any implementation of
that change existed. The path the change sits at is not written here: a change's
artifacts move when it is archived, and this repository's citation convention is
to name the change and the artifact in prose instead. See that change's
`test-plan.md` for the scenario accounting, the baseline, the assertions'
classification and the obsolete-test candidates.

The two deltas change one phrase each. *Single Shared PostgreSQL Instance,
Per-Application Databases* (`openspec/specs/iac-platform-services/spec.md`) and
*A Host-Scoped Variable Lives in the Host's Own Vars File*
(`openspec/specs/iac-host-configuration/spec.md`) cite their backlog entry as
"tracked in `docs/backlog/` as `<entry>`" where they cited `docs/backlog.md`.
No scenario of either requirement changes, so every assertion here traces to
that changed sentence of the requirement's body (SPECIFIED), or to the design
and task list (DERIVED, with the decision or task named).

Which text of a requirement is read
-----------------------------------
The deltas reach the main specification only on archive, after the
implementation has merged. So a requirement is read as it is about to stand: the
`### Requirement:` block of every live change's delta carrying it, and the main
specification only where no live delta does. The archive is never read: its
deltas are already merged, and it is history. The guard against the old path
reads the same way (design, Risks): every requirement of the main specification
except those a live MODIFIED delta shadows, plus every requirement of every live
delta.

Runner
------
    python3 -m unittest discover --start-directory .github/tests

    # a single test, selectable by name through discovery:
    python3 -m unittest discover --start-directory .github/tests -k \\
        test_a_requirement_cites_its_backlog_entry_by_name.TestNoRequirementCitesTheOldBacklogPath

Run from the repository root.

Every check here is a static read, so a check whose target already carries the
property passes having shown nothing about whether it can fail. Each detector is
therefore also run over material this file supplies -- the `...DetectorFires`
classes. This module imports only the standard library and no sibling module,
declares its arrangement locally, spawns no subprocess, and needs no network
call, credential, container runtime or Terraform binary.
"""

from __future__ import annotations

import os
import re
import tempfile
import unittest
from pathlib import Path


# --------------------------------------------------------------------------
# Local arrangement (this suite has no shared test arrangement; see AGENTS.md
# "Testing")
# --------------------------------------------------------------------------


def _repo_root() -> Path:
    """The repository root: `REPO_ROOT` if set, else the nearest ancestor
    holding `openspec/config.yaml`. Declared locally rather than imported from a
    sibling test module."""
    override = os.environ.get("REPO_ROOT")
    if override:
        return Path(override).resolve()
    here = Path(__file__).resolve()
    for candidate in (here, *here.parents):
        if (candidate / "openspec" / "config.yaml").is_file():
            return candidate
    raise RuntimeError(
        f"could not locate the repository root: no ancestor of {here} contains "
        "openspec/config.yaml, and REPO_ROOT is unset"
    )


ROOT = _repo_root()

# The archive directory's name under the changes directory, held as a value so
# that no literal change-shaped path segment appears in this file.
ARCHIVE_SEGMENT = "archive"


def _tree(test: unittest.TestCase, files: dict[str, str]) -> Path:
    """A scratch repository tree holding `files`, removed after the test."""
    scratch = tempfile.TemporaryDirectory()
    test.addCleanup(scratch.cleanup)
    root = Path(scratch.name)
    for relative, content in files.items():
        path = root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")
    return root


# --------------------------------------------------------------------------
# What is read
# --------------------------------------------------------------------------

# (capability, requirement, the entry the MODIFIED delta cites). SPECIFIED --
# each delta's body names the entry: "tracked in `docs/backlog/` as `<entry>`".
CITING_REQUIREMENTS: tuple[tuple[str, str, str], ...] = (
    (
        "iac-platform-services",
        "Single Shared PostgreSQL Instance, Per-Application Databases",
        "automate-per-application-database-provisioning",
    ),
    (
        "iac-host-configuration",
        "A Host-Scoped Variable Lives in the Host's Own Vars File",
        "put-the-remaining-host-scoped-variables-on-the-host-axis",
    ),
)

# DERIVED -- design D2: `test_basis_api_durable_store.py`'s follow-up check
# keeps its assertion, "the backlog carries
# `finish-basis-api-s-move-to-its-own-database`", read from where the backlog
# now keeps an entry.
BASIS_API_FOLLOW_UP = "finish-basis-api-s-move-to-its-own-database"

OLD_BACKLOG = "docs/backlog.md"
BACKLOG_DIR = "docs/backlog"

# SPECIFIED -- the delta's phrase, "tracked in `docs/backlog/` as `<entry>`".
# Whitespace between words may be a line break.
NEW_CITATION = re.compile(
    r"tracked\s+in\s+`docs/backlog/`\s+as\s+`(?P<entry>[a-z0-9]+(?:-[a-z0-9]+)*)`"
)

# DERIVED -- design D1: the citation names the directory and the entry's name,
# never the entry file's path.
ENTRY_FILE_PATH = re.compile(r"docs/backlog/[A-Za-z0-9._-]+\.md")

REQUIREMENT_HEADING = re.compile(r"^###\s+Requirement:\s*(?P<name>.+?)\s*$")
DELTA_SECTION = re.compile(r"^##\s+(?P<operation>[A-Z]+)\s+Requirements\s*$")
# A heading at level three or above ends a requirement block; a scenario (level
# four) does not.
BLOCK_END = re.compile(r"^#{1,3}\s")


def requirement_blocks(spec_text: str) -> list[tuple[str | None, str, str]]:
    """Every `### Requirement:` block in `spec_text`, heading included, as
    `(operation, name, block)`. `operation` is the enclosing delta section's
    operation (`MODIFIED`, `ADDED`, ...) or None where there is none, as in a
    main specification."""
    lines = spec_text.splitlines()
    found: list[tuple[str | None, str, str]] = []
    operation: str | None = None
    index = 0
    while index < len(lines):
        section = DELTA_SECTION.match(lines[index])
        if section is not None:
            operation = section.group("operation")
            index += 1
            continue
        if re.match(r"^##\s", lines[index]):
            operation = None
        heading = REQUIREMENT_HEADING.match(lines[index])
        if heading is None:
            index += 1
            continue
        end = index + 1
        while end < len(lines) and not BLOCK_END.match(lines[end]):
            end += 1
        found.append((operation, heading.group("name"), "\n".join(lines[index:end])))
        index = end
    return found


def _live_change_directories(root: Path) -> list[Path]:
    changes = root / "openspec" / "changes"
    if not changes.is_dir():
        return []
    return [
        directory
        for directory in sorted(changes.iterdir())
        if directory.is_dir() and directory.name != ARCHIVE_SEGMENT
    ]


def requirement_sources(capability: str, name: str, root: Path = ROOT) -> list[tuple[str, str]]:
    """The requirement as it is about to stand, as `(relative path, block)`:
    every live delta carrying it, or -- only where none does -- the main
    specification."""
    live: list[tuple[str, str]] = []
    for directory in _live_change_directories(root):
        delta = directory / "specs" / capability / "spec.md"
        if not delta.is_file():
            continue
        for _operation, found, block in requirement_blocks(delta.read_text(encoding="utf-8")):
            if found == name:
                live.append((delta.relative_to(root).as_posix(), block))
    if live:
        return live
    main = root / "openspec" / "specs" / capability / "spec.md"
    if main.is_file():
        for _operation, found, block in requirement_blocks(main.read_text(encoding="utf-8")):
            if found == name:
                return [(main.relative_to(root).as_posix(), block)]
    return []


def requirements_as_they_stand(root: Path = ROOT) -> list[tuple[str, str, str]]:
    """Every requirement a reader of the specifications meets, as
    `(relative path, name, block)`: every block of every live delta, and every
    block of the main specifications except one a live MODIFIED delta of the
    same capability shadows (design, Risks)."""
    read: list[tuple[str, str, str]] = []
    shadowed: set[tuple[str, str]] = set()
    for directory in _live_change_directories(root):
        specs = directory / "specs"
        if not specs.is_dir():
            continue
        for delta in sorted(specs.glob("*/spec.md")):
            capability = delta.parent.name
            relative = delta.relative_to(root).as_posix()
            for operation, name, block in requirement_blocks(delta.read_text(encoding="utf-8")):
                read.append((relative, name, block))
                if operation == "MODIFIED":
                    shadowed.add((capability, name))
    main_specs = root / "openspec" / "specs"
    if main_specs.is_dir():
        for main in sorted(main_specs.glob("*/spec.md")):
            capability = main.parent.name
            relative = main.relative_to(root).as_posix()
            for _operation, name, block in requirement_blocks(main.read_text(encoding="utf-8")):
                if (capability, name) not in shadowed:
                    read.append((relative, name, block))
    return read


def old_path_citations(root: Path = ROOT) -> list[str]:
    """Each requirement, read as it stands, that names `docs/backlog.md`."""
    return [
        f"{source}: {name}"
        for source, name, block in requirements_as_they_stand(root)
        if OLD_BACKLOG in block
    ]


def cited_entry(block: str) -> str | None:
    match = NEW_CITATION.search(block)
    return None if match is None else match.group("entry")


def entry_file(entry: str, root: Path = ROOT) -> Path:
    return root / BACKLOG_DIR / f"{entry}.md"


def citation_offences(block: str, expected: str, root: Path = ROOT) -> list[str]:
    """What is wrong with one requirement block's citation of its entry."""
    entry = cited_entry(block)
    if entry is None:
        return ["cites no entry as \"tracked in `docs/backlog/` as `<entry>`\""]
    offences = []
    if entry != expected:
        offences.append(f"cites `{entry}` where `{expected}` is the entry it names")
    if not entry_file(entry, root).is_file():
        offences.append(f"cites `{entry}` and {BACKLOG_DIR}/{entry}.md is not a file")
    return offences


def project_conventions(agents_text: str) -> str:
    """`AGENTS.md`'s project-conventions section: from its `## Project
    conventions` heading to the next level-two heading or the end."""
    match = re.search(r"^## Project conventions\s*$", agents_text, re.MULTILINE)
    if match is None:
        return ""
    rest = agents_text[match.end():]
    following = re.search(r"^## ", rest, re.MULTILINE)
    return rest if following is None else rest[: following.start()]


WORKFLOW_MARKER = re.compile(r"<!--\s*ai-toolkit:development-workflow\s+v(?P<version>\d+)\s*-->")


# --------------------------------------------------------------------------
# Design D1/D2, task 3.2: each requirement cites its entry by name, and the
# entry is a file
# --------------------------------------------------------------------------


class TestEachRequirementCitesItsEntryInTheBacklogDirectory(unittest.TestCase):
    """SPECIFIED -- each MODIFIED delta's body: "... tracked in `docs/backlog/`
    as `<entry>`". Design D2: with one file per entry, a file of the entry's
    name is the entry, so `docs/backlog/<entry>.md` being a file is sufficient
    where searching one file's text for the name was necessary only."""

    def _sources(self, capability: str, name: str) -> list[tuple[str, str]]:
        found = requirement_sources(capability, name)
        self.assertTrue(
            found,
            f"*{name}* was found neither in a live delta for `{capability}` nor in "
            "its main specification, so every assertion over it would pass having "
            "read nothing",
        )
        return found

    def test_each_requirement_cites_its_entry_in_the_new_form(self) -> None:
        """SPECIFIED -- the phrase and the entry name, as the class docstring."""
        for capability, name, expected in CITING_REQUIREMENTS:
            for source, block in self._sources(capability, name):
                with self.subTest(source=source, requirement=name):
                    self.assertEqual(
                        expected,
                        cited_entry(block),
                        f"*{name}* in {source} does not say it is tracked in "
                        f"`docs/backlog/` as `{expected}`",
                    )

    def test_each_cited_entry_is_a_file_in_the_backlog_directory(self) -> None:
        """SPECIFIED (the citation) with DERIVED sufficiency (design D2): the
        entry the requirement names is `docs/backlog/<entry>.md`, a file."""
        for capability, name, _expected in CITING_REQUIREMENTS:
            for source, block in self._sources(capability, name):
                entry = cited_entry(block)
                if entry is None:
                    continue  # reported by the test above
                with self.subTest(source=source, entry=entry):
                    self.assertTrue(
                        entry_file(entry).is_file(),
                        f"*{name}* in {source} cites `{entry}`, and "
                        f"{BACKLOG_DIR}/{entry}.md is not a file",
                    )

    def test_no_citing_requirement_names_an_entry_files_path(self) -> None:
        """DERIVED -- design D1: the citation names the directory and the
        entry's name, not the entry file's path, which would also become one
        more backticked Markdown path for the recipe-document scoping to keep
        out."""
        for capability, name, _expected in CITING_REQUIREMENTS:
            for source, block in self._sources(capability, name):
                with self.subTest(source=source, requirement=name):
                    self.assertEqual(
                        [],
                        ENTRY_FILE_PATH.findall(block),
                        f"*{name}* in {source} cites an entry file's path; cite the "
                        "entry by name",
                    )


class TestTheBasisApiFollowUpIsAnEntryFile(unittest.TestCase):
    """DERIVED -- design D2 and task 3.2: the follow-up
    `record-basis-api-durable-store` recorded is confirmed by its own file."""

    def test_the_follow_up_entry_is_a_file(self) -> None:
        self.assertTrue(
            entry_file(BASIS_API_FOLLOW_UP).is_file(),
            f"{BACKLOG_DIR}/{BASIS_API_FOLLOW_UP}.md is not a file",
        )


# --------------------------------------------------------------------------
# Design Risks, task 3.4: the old path is guarded against
# --------------------------------------------------------------------------


class TestNoRequirementCitesTheOldBacklogPath(unittest.TestCase):
    """DERIVED -- design, Risks "[A new citation of the old form passes
    unnoticed]" and task 3.4: a static test fails where any requirement in
    `openspec/specs/` or a live delta (the archive excluded) names
    `docs/backlog.md` at all, reading a requirement a live MODIFIED delta
    shadows from that delta."""

    def test_the_guard_reads_requirements_at_all(self) -> None:
        """DERIVED -- precondition: a guard that read nothing passes."""
        self.assertGreater(
            len(requirements_as_they_stand()),
            10,
            "the guard read (almost) no requirement; it would pass having checked nothing",
        )

    def test_no_requirement_names_the_old_backlog_path(self) -> None:
        offences = old_path_citations()
        self.assertEqual(
            [],
            offences,
            f"these requirements name `{OLD_BACKLOG}`, which no longer exists: "
            f"{offences}. Cite the entry as \"tracked in `docs/backlog/` as "
            "`<entry>`\"; a main-specification requirement gets a MODIFIED delta, "
            "and one in another live change's delta is corrected there",
        )


class TestTheOldBacklogFileIsGone(unittest.TestCase):
    """DERIVED -- design, Risks "[A branch in flight resurrects
    `docs/backlog.md`]" and task 3.4: a static test fails while
    `docs/backlog.md` exists."""

    def test_the_old_backlog_file_does_not_exist(self) -> None:
        self.assertFalse(
            (ROOT / OLD_BACKLOG).exists(),
            f"{OLD_BACKLOG} exists; the backlog is one file per entry under "
            f"{BACKLOG_DIR}/, and a second backlog is the resolution design D7 warns of",
        )


# --------------------------------------------------------------------------
# Design D4/D6, tasks 2.1 and 2.2
# --------------------------------------------------------------------------


class TestTheWorkflowBlockAndConventionsFollowTheMove(unittest.TestCase):
    """DERIVED -- design D4 and D6, tasks 2.1 and 2.2."""

    def test_the_workflow_block_is_marked_v12(self) -> None:
        """DERIVED -- task 2.1: marker `v12`. Establishes the marker only, not
        that the body is an unedited copy of the fragment, which lives outside
        this repository. At least v12 rather than exactly, so a later sync is
        not a regression of this change."""
        match = WORKFLOW_MARKER.search((ROOT / "AGENTS.md").read_text(encoding="utf-8"))
        self.assertIsNotNone(match, "AGENTS.md carries no development-workflow marker")
        self.assertGreaterEqual(int(match.group("version")), 12)

    def test_the_workstreams_readme_is_seeded(self) -> None:
        """DERIVED -- design D4, task 2.1: `docs/workstreams/README.md`."""
        self.assertTrue((ROOT / "docs" / "workstreams" / "README.md").is_file())

    def test_the_project_conventions_do_not_name_the_old_backlog(self) -> None:
        """DERIVED -- task 2.2, design D6: the two pointers in `AGENTS.md`'s
        project conventions are repointed to `docs/backlog/`."""
        section = project_conventions((ROOT / "AGENTS.md").read_text(encoding="utf-8"))
        self.assertTrue(section, "AGENTS.md has no `## Project conventions` section")
        self.assertFalse(
            OLD_BACKLOG in section,
            f"AGENTS.md's project conventions name `{OLD_BACKLOG}` "
            f"{section.count(OLD_BACKLOG)} time(s); point them at `{BACKLOG_DIR}/`",
        )


# --------------------------------------------------------------------------
# Fixture-driven discriminators
# --------------------------------------------------------------------------

PLATFORM = CITING_REQUIREMENTS[0]
NEW_FORM_BLOCK = f"""\
### Requirement: {PLATFORM[1]}
The platform stack SHALL run one shared PostgreSQL instance.

The mechanism is tracked in `docs/backlog/` as `{PLATFORM[2]}`; the obligation is stated here as well.

#### Scenario: A new application requests a database
- **WHEN** an application needs one
- **THEN** a database SHALL be provisioned
"""
OLD_FORM_BLOCK = NEW_FORM_BLOCK.replace("`docs/backlog/`", "`docs/backlog.md`")
PATH_FORM_BLOCK = NEW_FORM_BLOCK.replace(
    f"tracked in `docs/backlog/` as `{PLATFORM[2]}`",
    f"tracked in `docs/backlog/{PLATFORM[2]}.md`",
)

# Assembled from parts: a literal change-shaped segment after the changes
# directory is what this repository's citation sweep forbids.
CHANGES = "openspec/" + "changes/"
LIVE_CHANGE = "some" + "-change"
OTHER_LIVE_CHANGE = "other" + "-change"
MAIN_SPEC = f"openspec/specs/{PLATFORM[0]}/spec.md"
LIVE_DELTA = CHANGES + LIVE_CHANGE + f"/specs/{PLATFORM[0]}/spec.md"
OTHER_LIVE_DELTA = CHANGES + OTHER_LIVE_CHANGE + "/specs/iac-other/spec.md"
ARCHIVED_DELTA = (
    CHANGES + ARCHIVE_SEGMENT + "/2026-01-01-" + LIVE_CHANGE + f"/specs/{PLATFORM[0]}/spec.md"
)


def _main(block: str) -> str:
    return f"# {PLATFORM[0]}\n\n## Purpose\nSee `docs/backlog.md`.\n\n## Requirements\n\n{block}"


def _delta(operation: str, block: str) -> str:
    return f"## {operation} Requirements\n\n{block}"


class TestTheCitationDetectorFires(unittest.TestCase):
    def test_the_new_form_yields_its_entry(self) -> None:
        self.assertEqual(PLATFORM[2], cited_entry(NEW_FORM_BLOCK))
        self.assertEqual([], ENTRY_FILE_PATH.findall(NEW_FORM_BLOCK))

    def test_the_new_form_across_a_line_break_yields_its_entry(self) -> None:
        wrapped = NEW_FORM_BLOCK.replace("tracked in `docs", "tracked\nin `docs")
        self.assertEqual(PLATFORM[2], cited_entry(wrapped))

    def test_the_old_form_yields_no_entry(self) -> None:
        self.assertIsNone(cited_entry(OLD_FORM_BLOCK))

    def test_the_path_form_yields_no_entry_and_is_reported_as_a_path(self) -> None:
        self.assertIsNone(cited_entry(PATH_FORM_BLOCK))
        self.assertEqual([f"docs/backlog/{PLATFORM[2]}.md"], ENTRY_FILE_PATH.findall(PATH_FORM_BLOCK))

    def test_a_citation_of_an_existing_entry_file_is_clean(self) -> None:
        root = _tree(self, {f"docs/backlog/{PLATFORM[2]}.md": "---\n---\n"})
        self.assertEqual([], citation_offences(NEW_FORM_BLOCK, PLATFORM[2], root))

    def test_a_citation_of_a_missing_entry_file_is_reported(self) -> None:
        root = _tree(self, {"docs/backlog/README.md": "readme\n"})
        offences = citation_offences(NEW_FORM_BLOCK, PLATFORM[2], root)
        self.assertEqual(1, len(offences))
        self.assertIn("is not a file", offences[0])

    def test_a_directory_of_the_entrys_name_is_not_an_entry(self) -> None:
        root = _tree(self, {f"docs/backlog/{PLATFORM[2]}.md/x": "x\n"})
        self.assertNotEqual([], citation_offences(NEW_FORM_BLOCK, PLATFORM[2], root))

    def test_an_entry_named_only_inside_the_old_single_file_is_reported(self) -> None:
        root = _tree(self, {OLD_BACKLOG: f"### `{PLATFORM[2]}`\n"})
        self.assertNotEqual([], citation_offences(NEW_FORM_BLOCK, PLATFORM[2], root))

    def test_a_citation_of_another_entry_is_reported(self) -> None:
        other = NEW_FORM_BLOCK.replace(PLATFORM[2], "some-other-entry")
        root = _tree(self, {"docs/backlog/some-other-entry.md": "x\n"})
        self.assertEqual(1, len(citation_offences(other, PLATFORM[2], root)))

    def test_an_old_form_citation_is_reported(self) -> None:
        root = _tree(self, {f"docs/backlog/{PLATFORM[2]}.md": "x\n"})
        self.assertNotEqual([], citation_offences(OLD_FORM_BLOCK, PLATFORM[2], root))


class TestTheRequirementIsReadWhereItIsAboutToStand(unittest.TestCase):
    def test_a_live_delta_is_read_over_the_main_specification(self) -> None:
        root = _tree(
            self,
            {MAIN_SPEC: _main(OLD_FORM_BLOCK), LIVE_DELTA: _delta("MODIFIED", NEW_FORM_BLOCK)},
        )
        sources = requirement_sources(PLATFORM[0], PLATFORM[1], root)
        self.assertEqual([LIVE_DELTA], [source for source, _ in sources])
        self.assertEqual(PLATFORM[2], cited_entry(sources[0][1]))

    def test_the_main_specification_is_read_where_no_live_delta_carries_it(self) -> None:
        root = _tree(
            self,
            {MAIN_SPEC: _main(NEW_FORM_BLOCK), ARCHIVED_DELTA: _delta("MODIFIED", OLD_FORM_BLOCK)},
        )
        sources = requirement_sources(PLATFORM[0], PLATFORM[1], root)
        self.assertEqual([MAIN_SPEC], [source for source, _ in sources])

    def test_a_tree_carrying_the_requirement_nowhere_yields_nothing(self) -> None:
        root = _tree(self, {"README.md": "x\n"})
        self.assertEqual([], requirement_sources(PLATFORM[0], PLATFORM[1], root))


class TestTheOldPathGuardFires(unittest.TestCase):
    def test_a_main_specification_requirement_naming_the_old_path_is_reported(self) -> None:
        root = _tree(self, {MAIN_SPEC: _main(OLD_FORM_BLOCK)})
        self.assertEqual([f"{MAIN_SPEC}: {PLATFORM[1]}"], old_path_citations(root))

    def test_a_requirement_shadowed_by_a_live_modified_delta_is_read_from_it(self) -> None:
        root = _tree(
            self,
            {MAIN_SPEC: _main(OLD_FORM_BLOCK), LIVE_DELTA: _delta("MODIFIED", NEW_FORM_BLOCK)},
        )
        self.assertEqual([], old_path_citations(root))

    def test_a_live_added_delta_does_not_shadow_the_main_specification(self) -> None:
        """Only a MODIFIED delta replaces the requirement's text (design,
        Risks)."""
        root = _tree(
            self,
            {MAIN_SPEC: _main(OLD_FORM_BLOCK), LIVE_DELTA: _delta("ADDED", NEW_FORM_BLOCK)},
        )
        self.assertEqual([f"{MAIN_SPEC}: {PLATFORM[1]}"], old_path_citations(root))

    def test_a_live_delta_naming_the_old_path_is_reported(self) -> None:
        root = _tree(
            self,
            {
                MAIN_SPEC: _main(NEW_FORM_BLOCK),
                OTHER_LIVE_DELTA: _delta(
                    "ADDED", OLD_FORM_BLOCK.replace(PLATFORM[1], "Something Else")
                ),
            },
        )
        self.assertEqual([f"{OTHER_LIVE_DELTA}: Something Else"], old_path_citations(root))

    def test_a_live_modified_delta_naming_the_old_path_is_reported(self) -> None:
        root = _tree(
            self,
            {MAIN_SPEC: _main(NEW_FORM_BLOCK), LIVE_DELTA: _delta("MODIFIED", OLD_FORM_BLOCK)},
        )
        self.assertEqual([f"{LIVE_DELTA}: {PLATFORM[1]}"], old_path_citations(root))

    def test_the_archive_is_not_read(self) -> None:
        root = _tree(
            self,
            {MAIN_SPEC: _main(NEW_FORM_BLOCK), ARCHIVED_DELTA: _delta("MODIFIED", OLD_FORM_BLOCK)},
        )
        self.assertEqual([], old_path_citations(root))

    def test_text_outside_any_requirement_is_not_reported(self) -> None:
        """`_main` names the old path in its Purpose section on purpose."""
        root = _tree(self, {MAIN_SPEC: _main(NEW_FORM_BLOCK)})
        self.assertEqual([], old_path_citations(root))
        self.assertEqual(1, len(requirements_as_they_stand(root)))

    def test_a_block_stops_at_the_next_requirement(self) -> None:
        text = _main(NEW_FORM_BLOCK + "\n### Requirement: Next\nSee `docs/backlog.md`.\n")
        root = _tree(self, {MAIN_SPEC: text})
        self.assertEqual([f"{MAIN_SPEC}: Next"], old_path_citations(root))


class TestTheOldFileCheckFires(unittest.TestCase):
    def test_a_tree_holding_the_old_file_is_detected(self) -> None:
        root = _tree(self, {OLD_BACKLOG: "# Backlog\n"})
        self.assertTrue((root / OLD_BACKLOG).exists())

    def test_a_tree_holding_only_entry_files_is_clean(self) -> None:
        root = _tree(self, {"docs/backlog/README.md": "x\n", f"docs/backlog/{PLATFORM[2]}.md": "x\n"})
        self.assertFalse((root / OLD_BACKLOG).exists())


class TestTheConventionDetectorsFire(unittest.TestCase):
    AGENTS = (
        "<!-- ai-toolkit:development-workflow v12 -->\n"
        "## Development workflow\nRecord it in `docs/backlog.md`.\n"
        "## Project conventions\n### Testing\nSee `docs/backlog/`'s entry.\n"
    )

    def test_the_conventions_section_excludes_the_workflow_block(self) -> None:
        self.assertNotIn(OLD_BACKLOG, project_conventions(self.AGENTS))

    def test_a_conventions_pointer_to_the_old_path_is_seen(self) -> None:
        text = self.AGENTS.replace("`docs/backlog/`'s entry", "`docs/backlog.md`'s entry")
        self.assertIn(OLD_BACKLOG, project_conventions(text))

    def test_the_marker_version_is_read(self) -> None:
        self.assertEqual("12", WORKFLOW_MARKER.search(self.AGENTS).group("version"))
        old = self.AGENTS.replace("v12", "v10")
        self.assertEqual("10", WORKFLOW_MARKER.search(old).group("version"))


if __name__ == "__main__":
    unittest.main()
