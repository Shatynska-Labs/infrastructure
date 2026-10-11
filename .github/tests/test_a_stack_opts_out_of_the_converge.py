"""Tests for a stack that declares, in its own pipeline declaration, that the
host-configuration workflow has no host to reach.

Derived from the delta specifications of the OpenSpec change
`let-a-stack-opt-out-of-the-converge`, before any implementation of that change
existed -- from those deltas at commit `e0c3ce6`, the commit holding the
approved plan. The path those deltas sit at is not written here: a change's
artifacts move when it is archived, and this repository's citation convention is
to name the change and the artifact in prose instead.

The deltas modify two requirements of `iac-cicd-pipeline`
(`openspec/specs/iac-cicd-pipeline/spec.md`): *Host Configuration Is Applied by
a Gated Workflow* and *Each Stack Declares Its Own Pipeline Configuration*. Each
class below names the requirement and the scenario it traces to, and every
assertion is annotated SPECIFIED (it traces to SHALL text or to a scenario in a
delta spec) or DERIVED (it traces to that change's `proposal.md`, `design.md` or
`tasks.md` rather than to a scenario). See that change's `test-plan.md` for the
scenario-to-test mapping, the baseline, the scenarios deliberately left
uncovered, the obsolete-test candidates, and the project questions this file
took an assumption on.

Why this is a new module rather than a section of an existing one
-----------------------------------------------------------------
These tests were written by an author other than whoever implements the change,
and that author may only add. Nothing in this file edits, deletes or disables an
existing test. One existing assertion rests on a proposition this change retires
-- `test_the_platform_stack_deploys_per_stack
.TestEveryStackThatReceivesThePlatformStackDeclaresIt
.test_both_committed_stacks_receive_the_platform_stack` -- and is recorded in
`test-plan.md`'s obsolete list as a candidate for human confirmation rather than
touched here.

The discovery body is EXECUTED, not read: the same extract-and-run shape
`test_host_converge_workflow.TestHostConvergeDiscoveryFailsClosed` uses, with its
locator and fixture mixins imported rather than restated. That the body can be
run at all is that change's tasks.md 2.5 ("Keep the step body free of
event-derived values").

`TestEveryModuleInTheSuiteDirectoryNeedsNoPrivilegedResource` in
`test_ci_configuration.py` reads every module in this directory; this one uses
the standard library, `yaml`, the helpers of the modules beside it, and `bash`
as the only spawned command.

Runner
------
    python3 -m unittest discover --start-directory .github/tests

    # or one class / one test, individually selectable:
    python3 -m unittest discover --start-directory .github/tests \\
        -k TestAStackExcludedByItsOwnDeclarationIsNamedAndNotConverged
    python3 -m unittest discover --start-directory .github/tests \\
        -k test_every_stack_excluded_fails_naming_them

Run from the repository root, and through `discover`: it is discovery that puts
`.github/tests` on `sys.path`, which is what makes the sibling imports resolve.

Which assertions are red before the implementation
--------------------------------------------------
- RED until the change lands: every test in which a fixture stack declares the
  converge field `false` or an unrecognised value (the committed discovery
  ignores the field), the committed-tree reads of `main-staging`'s declaration,
  and `TestTheCommittedTreeConvergesProductionAndExcludesStaging`.
- GREEN at authoring, by design, and stated so that the pass is not read as the
  "passed before any implementation existed" alarm:
  `test_an_excluded_stack_with_no_inventory_source_is_refused` (the cross-check
  it exercises already runs for every stack -- what it guards against is the
  exclusion being placed BEFORE that cross-check), the two default-converges
  tests (a field nobody reads defaults to converging today), the not-found
  dispatch test, and the discriminators in `TestTheseReadsDiscriminate`, which
  run over material this file supplies.
"""

from __future__ import annotations

import json
import os
import re
import shutil
import tempfile
import unittest
from pathlib import Path

from test_ci_configuration import ROOT, require_external_tools
from test_environment_agnostic_pipeline import (
    ACTIONS_EXPRESSION,
    PROD_DIRECTORY,
    SECRET_KEY_HINTS,
    TARGET_GROUP_KEY_HINT,
    environment_declarations,
    run_snippet,
)
from test_host_converge_workflow import (
    DISPATCH_INPUT,
    HostConvergeTreeFixtureMixin,
    WorkflowLocatorMixin,
)
from test_the_platform_stack_deploys_per_stack import platform_opt_in

# --------------------------------------------------------------------------
# Identifiers this file names, and why each is a constraint rather than a
# property the specification states.
# --------------------------------------------------------------------------

# The converge field's spelling. DERIVED -- the delta states WHAT a declaration
# declares ("whether the host-configuration workflow converges its host") and
# fixes no name; `converges_host` is the reviewed proposal's and tasks.md 2.1's.
# Unlike `PLATFORM_KEY_HINT` in the sibling module, this is matched literally:
# the name is fixed by the approved plan, and a hint such as `converge` would
# also match any comment-free key a future field happens to share it with.
CONVERGE_KEY = "converges_host"

# The stack this change opts out. DERIVED (design.md Decision 5, tasks.md 3.2):
# no scenario names a stack.
STAGING_DIRECTORY = "main-staging"

# How a run's output is read as naming a stack AS EXCLUDED, rather than merely
# naming it. SPECIFIED as to the obligation ("SHALL name that stack as excluded
# by its own declaration"); the word stem is DERIVED (tasks.md 2.2's message
# "Excluded by their own declarations, and converged by nothing: <names>"). The
# stem rather than the sentence, so the wording stays the implementer's.
EXCLUSION_WORD = re.compile(r"exclu", re.IGNORECASE)

# Words that would make a converge field's name state its inverse. SPECIFIED as
# to the obligation (each optional field "SHALL name what happens when it is
# true ... rather than whether the stack is ... excluded or dormant"); the list
# is DERIVED, taken from that sentence and from design.md Decision 1's rejected
# `host_excluded` / `dormant`.
INVERTED_POLARITY_WORDS = ("exclude", "excluded", "dormant", "skip", "disabled", "without")


# --------------------------------------------------------------------------
# Reads, each exercised over supplied material by `TestTheseReadsDiscriminate`
# --------------------------------------------------------------------------


def converge_value(mapping: dict) -> tuple:
    """`(value, offence)` for one declaration's converge field.

    `None` with no offence is the field being ABSENT, which the requirement
    gives a default for -- "defaults to the host **being** converged when
    absent" -- and is therefore not an offence. A value that is not a boolean
    is one: "a value ... that is neither true nor false" is refused.
    """
    if CONVERGE_KEY not in mapping:
        return None, None
    value = mapping[CONVERGE_KEY]
    if not isinstance(value, bool):
        return None, (
            f"`{CONVERGE_KEY}` is {value!r}, which is neither true nor false; "
            "host-configuration discovery refuses it rather than reading it as "
            "either answer"
        )
    return value, None


def polarity_offences(declarations: dict) -> list:
    """Every converge-naming key whose name carries a negation."""
    offenders = []
    for name, mapping in sorted(declarations.items()):
        for key in mapping:
            normal = re.sub(r"[^a-z0-9]", "", str(key).lower())
            if "converge" not in normal:
                continue
            if any(word in normal for word in INVERTED_POLARITY_WORDS):
                offenders.append(f"{name}: {key!r}")
    return offenders


def _json_values(text: str) -> list:
    """Every JSON value written to a `$GITHUB_OUTPUT` file, in both the
    `key=value` and the `key<<DELIMITER` forms the runner accepts."""
    values = []
    lines = text.splitlines()
    index = 0
    while index < len(lines):
        line = lines[index]
        index += 1
        heredoc = re.match(r"^[A-Za-z0-9_\-]+<<(.+)$", line)
        if heredoc:
            delimiter = heredoc.group(1)
            body = []
            while index < len(lines) and lines[index] != delimiter:
                body.append(lines[index])
                index += 1
            index += 1
            candidate = "\n".join(body)
        elif "=" in line:
            candidate = line.split("=", 1)[1]
        else:
            continue
        try:
            values.append(json.loads(candidate))
        except ValueError:
            continue
    return values


def matrix_rows(output_text: str) -> list:
    """Every row the emitted matrix carries: a mapping, or a bare string held in
    a list. DERIVED as to shape -- the requirement says discovery emits the set
    the converge job runs over and fixes no encoding; a `fromJSON` matrix is how
    one is consumed, and both encodings it admits are read here."""
    rows = []

    def walk(value) -> None:
        if isinstance(value, dict):
            if value and all(not isinstance(v, (dict, list)) for v in value.values()):
                rows.append(value)
            for child in value.values():
                if isinstance(child, (dict, list)):
                    walk(child)
        elif isinstance(value, list):
            for child in value:
                if isinstance(child, str):
                    rows.append(child)
                else:
                    walk(child)

    for value in _json_values(output_text):
        walk(value)
    return rows


def rows_naming(rows: list, stack: str) -> list:
    """The rows naming `stack` as one of their values -- exactly, so `alpha`
    does not match a row for `alpha-environment`."""
    named = []
    for row in rows:
        if isinstance(row, str) and row == stack:
            named.append(row)
        elif isinstance(row, dict) and any(str(v) == stack for v in row.values()):
            named.append(row)
    return named


def names_as_excluded(text: str, stack: str) -> bool:
    """Whether one line of `text` names `stack` (as a whole word) together with
    the exclusion."""
    pattern = re.compile(rf"(?<![\w-]){re.escape(stack)}(?![\w-])")
    return any(
        pattern.search(line) and EXCLUSION_WORD.search(line) for line in text.splitlines()
    )


# --------------------------------------------------------------------------
# Running the discovery body
# --------------------------------------------------------------------------


class ConvergeOptOutDiscoveryMixin(HostConvergeTreeFixtureMixin, WorkflowLocatorMixin):
    """Runs `host-converge.yml`'s discovery body over a scratch tree whose
    declarations carry the converge field.

    The run harness repeats `TestHostConvergeDiscoveryFailsClosed._run_discovery`
    rather than importing that class: a TestCase class imported into this module
    would be collected and run here a second time. It additionally returns the
    run summary, since naming an excluded stack "in every run" may legitimately
    land there rather than on stdout.
    """

    def setUp(self) -> None:
        require_external_tools(
            self,
            ("bash", "find", "jq"),
            "execute the host-converge workflow's environment-discovery body",
        )

    def _input_variable(self, job: dict, step: dict) -> str | None:
        for holder in (step, job):
            for key, value in (holder.get("env") or {}).items():
                if DISPATCH_INPUT.search(str(value)):
                    return str(key)
        return None

    def _run(self, tree: Path, dispatched: str | None = None):
        """`(returncode, output text, everything the run said)`."""
        _, job, step = self.discovery_step()
        outputs = tree / "github_output"
        summary = tree / "step_summary"
        outputs.write_text("", encoding="utf-8")
        summary.write_text("", encoding="utf-8")
        environment = dict(
            os.environ,
            GITHUB_OUTPUT=str(outputs),
            GITHUB_ENV=str(outputs),
            GITHUB_STEP_SUMMARY=str(summary),
            GITHUB_WORKSPACE=str(tree),
        )
        for holder in (job, step):
            for key, value in (holder.get("env") or {}).items():
                if not ACTIONS_EXPRESSION.search(str(value)):
                    environment[str(key)] = str(value)
        variable = self._input_variable(job, step)
        if dispatched is not None:
            self.assertIsNotNone(
                variable,
                "the discovery step takes no environment variable carrying the "
                "dispatch input, so a run requested by hand cannot be exercised. Its "
                f"`env:` keys are {sorted((step.get('env') or {}))}",
            )
            environment[variable] = dispatched
        elif variable:
            environment[variable] = ""
        result = run_snippet(str(step["run"]), environment, tree)
        said = "\n".join(
            part
            for part in (result.stdout, result.stderr, summary.read_text(encoding="utf-8"))
            if part
        )
        return result.returncode, outputs.read_text(encoding="utf-8"), said

    def _declaration(self, name: str, converges, **without) -> dict:
        """A fixture declaration for `name`; `converges` is the converge field's
        value, or `None` for a declaration that does not carry it."""
        mapping = self._declaration_for(
            f"HCLOUD_TOKEN_{name.upper()}", f"{name}-environment", gate=False
        )
        mapping.pop(CONVERGE_KEY, None)
        if converges is not None:
            mapping[CONVERGE_KEY] = converges
        if without.get("target_group"):
            mapping = self._without_field(mapping, (TARGET_GROUP_KEY_HINT,))
        if without.get("secret"):
            mapping = self._without_field(mapping, SECRET_KEY_HINTS)
        return mapping

    def _tree(self, stacks: dict, ansible: dict | None = None) -> Path:
        """`stacks` maps a stack to its converge value (or `None`); `ansible`
        overrides the default (has inventory source, has group_vars) per stack."""
        scratch = self._scratch()
        self._write_tree(
            scratch, {name: self._declaration(name, value) for name, value in stacks.items()}
        )
        sides = {name: (True, True) for name in stacks}
        sides.update(ansible or {})
        self._write_ansible_side(scratch, sides)
        return scratch

    def assertConverges(self, output: str, said: str, stack: str) -> None:
        self.assertTrue(
            rows_naming(matrix_rows(output), stack),
            f"the emitted matrix carries no row for `{stack}`, so its host is converged "
            f"by nothing. Output: {output!r}. Run said: {said[-800:]!r}",
        )

    def assertNotConverged(self, output: str, stack: str) -> None:
        self.assertEqual(
            [],
            rows_naming(matrix_rows(output), stack),
            f"`{stack}` declares that its host is not converged and still reached the "
            f"converge matrix: {output!r}",
        )


# --------------------------------------------------------------------------
# iac-cicd-pipeline / Host Configuration Is Applied by a Gated Workflow
# (MODIFIED)
# --------------------------------------------------------------------------


class TestAStackExcludedByItsOwnDeclarationIsNamedAndNotConverged(
    ConvergeOptOutDiscoveryMixin, unittest.TestCase
):
    """MODIFIED requirement: Host Configuration Is Applied by a Gated Workflow --
    "The workflow SHALL name each such stack as excluded by its own declaration
    before it emits the matrix, SHALL converge it in no row".

    Scenarios "A stack excluded by its own declaration is named and not
    converged" and, as revised, "A merge to the host configuration converges
    without a workstation" ("each already-configured stack's host, other than
    one excluded by its own declaration, SHALL be converged").
    """

    def test_an_excluded_stack_is_named_and_every_other_stack_is_converged(self) -> None:
        """SPECIFIED -- scenario "A stack excluded by its own declaration is named
        and not converged": the workflow "SHALL name that stack as excluded by its
        own declaration, SHALL run no converge job for it, and SHALL converge every
        other discovered stack as before"."""
        tree = self._tree({"alpha": None, "bravo": False, "charlie": True})
        code, output, said = self._run(tree)
        self.assertEqual(
            0,
            code,
            f"discovery refused a tree whose only difference is one stack switched off: "
            f"{said[-800:]!r}",
        )
        self.assertNotConverged(output, "bravo")
        for stack in ("alpha", "charlie"):
            self.assertConverges(output, said, stack)
        self.assertTrue(
            names_as_excluded(said, "bravo"),
            "the run does not name `bravo` as excluded on any line, so a stack switched "
            "off by its declaration is indistinguishable from one omitted by a defect: "
            f"{said[-800:]!r}",
        )

    def test_a_merge_converges_every_stack_its_declaration_does_not_exclude(self) -> None:
        """SPECIFIED -- scenario "A merge to the host configuration converges
        without a workstation", as revised: "each already-configured stack's host,
        other than one excluded by its own declaration, SHALL be converged by the
        workflow". A merge supplies an empty dispatch input, which is what `_run`
        supplies when no stack is named."""
        tree = self._tree({"alpha": True, "bravo": True, "charlie": False})
        code, output, said = self._run(tree)
        self.assertEqual(0, code, f"discovery refused the tree: {said[-800:]!r}")
        self.assertConverges(output, said, "alpha")
        self.assertConverges(output, said, "bravo")
        self.assertNotConverged(output, "charlie")


class TestAnExcludedStackIsNotRefusedForAFieldOnlyItsConvergeWouldConsume(
    ConvergeOptOutDiscoveryMixin, unittest.TestCase
):
    """MODIFIED requirement: Host Configuration Is Applied by a Gated Workflow --
    "A stack excluded by its own declaration SHALL NOT be refused for the
    absence or invalidity of a field only its converge would consume -- its
    declared Ansible group, that group's variables file or its read-only secret
    name"."""

    def _assert_accepted(self, tree: Path, case: str) -> None:
        code, output, said = self._run(tree)
        self.assertEqual(
            0,
            code,
            f"discovery refused an EXCLUDED stack for {case}, which only a converge of "
            f"it would read -- switching a stack off is harder than switching it on: "
            f"{said[-800:]!r}",
        )
        self.assertConverges(output, said, "alpha")
        self.assertNotConverged(output, "bravo")
        self.assertTrue(
            names_as_excluded(said, "bravo"),
            f"the accepted tree does not name `bravo` as excluded: {said[-800:]!r}",
        )

    def test_an_excluded_stack_declaring_no_ansible_group_is_accepted(self) -> None:
        """SPECIFIED -- scenario "An excluded stack is not refused for a field
        only its converge would consume": "declares no Ansible group"."""
        scratch = self._scratch()
        self._write_tree(
            scratch,
            {
                "alpha": self._declaration("alpha", None),
                "bravo": self._declaration("bravo", False, target_group=True),
            },
        )
        self._write_ansible_side(scratch, {"alpha": (True, True), "bravo": (True, False)})
        self._assert_accepted(scratch, "declaring no Ansible group")

    def test_an_excluded_stack_whose_group_has_no_variables_file_is_accepted(self) -> None:
        """SPECIFIED -- the same scenario: "or one whose variables file does not
        exist"."""
        tree = self._tree({"alpha": None, "bravo": False}, {"bravo": (True, False)})
        self._assert_accepted(tree, "naming a group with no variables file")

    def test_an_excluded_stack_declaring_no_read_only_secret_is_accepted(self) -> None:
        """SPECIFIED -- the requirement text rather than the scenario: the fields
        an excluded stack is not refused for include "its read-only secret
        name"."""
        scratch = self._scratch()
        self._write_tree(
            scratch,
            {
                "alpha": self._declaration("alpha", None),
                "bravo": self._declaration("bravo", False, secret=True),
            },
        )
        self._write_ansible_side(scratch, {"alpha": (True, True), "bravo": (True, True)})
        self._assert_accepted(scratch, "declaring no read-only secret name")


class TestAnExcludedStackStillNeedsItsInventorySource(
    ConvergeOptOutDiscoveryMixin, unittest.TestCase
):
    """MODIFIED requirement: Host Configuration Is Applied by a Gated Workflow --
    "the check that its inventory source and its pipeline declaration exist for
    each other SHALL still apply to it, being a property of the tree rather than
    of a converge".

    GREEN at authoring: the committed discovery reads no converge field, so it
    applies this cross-check to every stack already. What this asserts is that the
    implementation's early exit for an excluded stack (design.md Decision 3) is
    not placed ahead of it.
    """

    def test_an_excluded_stack_with_no_inventory_source_is_refused(self) -> None:
        """SPECIFIED -- scenario "An excluded stack still needs its inventory
        source": "discovery SHALL fail naming that stack and the missing side,
        exactly as it does for a stack that is not excluded"."""
        tree = self._tree({"alpha": None, "bravo": False}, {"bravo": (False, True)})
        code, output, said = self._run(tree)
        self.assertNotEqual(
            0,
            code,
            "discovery accepted an excluded stack that has no inventory source, so the "
            "tree-level cross-check was skipped along with the converge: "
            f"{said[-800:]!r}",
        )
        refusal = [line for line in said.splitlines() if "bravo" in line]
        self.assertTrue(refusal, f"the refusal does not name `bravo`: {said[-800:]!r}")
        self.assertTrue(
            any(re.search(r"inventory|source|hcloud", line, re.IGNORECASE) for line in refusal),
            "no line naming `bravo` names the missing side (its inventory source): "
            f"{refusal!r}",
        )


class TestARunRequestedForAnExcludedStackFailsNamingTheExclusion(
    ConvergeOptOutDiscoveryMixin, unittest.TestCase
):
    """MODIFIED requirement: Host Configuration Is Applied by a Gated Workflow --
    the workflow "SHALL fail a run requested by hand that names it, saying that
    it is excluded rather than that it was not found"."""

    def _new_lines(self, tree: Path, dispatched: str) -> tuple:
        """What a dispatched run says that the same tree's undispatched run does
        not -- so the exclusion listing every run prints is not mistaken for the
        refusal of the dispatch."""
        _, _, baseline = self._run(tree)
        code, output, said = self._run(tree, dispatched=dispatched)
        common = set(baseline.splitlines())
        return code, output, [line for line in said.splitlines() if line not in common]

    def test_a_dispatch_naming_an_excluded_stack_fails_saying_it_is_excluded(self) -> None:
        """SPECIFIED -- scenario "A run requested for an excluded stack fails
        naming the exclusion": "the run SHALL fail saying that the stack is
        excluded by its own declaration, rather than converging nothing and
        reporting success"."""
        tree = self._tree({"alpha": None, "bravo": False})
        code, output, new = self._new_lines(tree, "bravo")
        self.assertNotEqual(
            0,
            code,
            "a converge requested by hand for a stack excluded by its own declaration "
            f"concluded successfully. Output: {output!r}",
        )
        self.assertNotConverged(output, "bravo")
        self.assertTrue(
            any(EXCLUSION_WORD.search(line) for line in new),
            "the refusal of the dispatch does not say the stack is excluded; the "
            f"lines this dispatch added were {new!r}",
        )

    def test_the_excluded_refusal_is_not_the_not_found_refusal(self) -> None:
        """SPECIFIED -- the same scenario: "rather than ... reporting the stack as
        not found". Compared against the not-found refusal of the SAME tree with the
        requested name masked, so the comparison is between the two messages
        rather than between the two names."""
        tree = self._tree({"alpha": None, "bravo": False})
        excluded_code, _, excluded = self._new_lines(tree, "bravo")
        unknown_code, _, unknown = self._new_lines(tree, "charlie")
        # Both must be refusals for the comparison to be between two refusal
        # messages; without this, an excluded dispatch that SUCCEEDS differs from
        # the not-found refusal trivially and this test would pass on it.
        self.assertNotEqual(0, excluded_code, f"the excluded dispatch succeeded: {excluded!r}")
        self.assertNotEqual(0, unknown_code, f"the unknown dispatch succeeded: {unknown!r}")
        self.assertNotEqual(
            [line.replace("bravo", "<stack>") for line in excluded],
            [line.replace("charlie", "<stack>") for line in unknown],
            "a dispatch naming an excluded stack is refused with the same message as one "
            "naming a stack that does not exist, so the operator is pointed at a typo "
            f"rather than at the declaration: {excluded!r}",
        )

    def test_a_dispatch_naming_an_unknown_stack_is_still_refused_as_not_found(self) -> None:
        """SPECIFIED -- scenario "A run is requested for an environment that does
        not exist" (unchanged text, carried in the MODIFIED requirement), read on a
        tree that now carries an excluded stack: "the run SHALL fail naming the
        stacks that were found". Only the converged stack's name is asserted; whether
        an excluded stack counts as "found" for this message is not stated."""
        tree = self._tree({"alpha": None, "bravo": False})
        code, _, said = self._run(tree, dispatched="charlie")
        self.assertNotEqual(0, code, f"the unknown dispatch succeeded: {said[-800:]!r}")
        self.assertIn("alpha", said, f"the refusal names no found stack: {said[-800:]!r}")

    def test_a_dispatch_naming_a_converged_stack_beside_an_excluded_one_runs(self) -> None:
        """DERIVED -- the converse the refusals above need: a body refusing every
        dispatch on a tree carrying an exclusion would satisfy them while making a
        by-hand converge impossible."""
        tree = self._tree({"alpha": None, "bravo": False})
        code, output, said = self._run(tree, dispatched="alpha")
        self.assertEqual(0, code, f"the dispatch of `alpha` was refused: {said[-800:]!r}")
        self.assertConverges(output, said, "alpha")
        self.assertNotConverged(output, "bravo")


class TestEveryStackExcludedFailsRatherThanReportingSuccess(
    ConvergeOptOutDiscoveryMixin, unittest.TestCase
):
    """MODIFIED requirement: Host Configuration Is Applied by a Gated Workflow --
    "A run in which every discovered stack is excluded SHALL fail as discovery
    finding nothing does"."""

    def test_every_stack_excluded_fails_naming_them(self) -> None:
        """SPECIFIED -- scenario "Every stack excluded fails rather than reporting
        success": "the workflow SHALL fail naming the excluded stacks, and SHALL NOT
        allow a dependent job to be skipped and reported as successful". A non-zero
        exit of the discovery step is what fails the dependent job rather than
        skipping it."""
        tree = self._tree({"alpha": False, "bravo": False})
        code, output, said = self._run(tree)
        self.assertNotEqual(
            0,
            code,
            "discovery concluded successfully over a tree in which every stack is "
            "excluded, so the converge job is skipped on an empty matrix and the run "
            f"reports green having converged no host. Output: {output!r}",
        )
        for stack in ("alpha", "bravo"):
            self.assertIn(
                stack,
                said,
                f"the refusal does not name the excluded stack `{stack}`: {said[-800:]!r}",
            )


# --------------------------------------------------------------------------
# iac-cicd-pipeline / Each Stack Declares Its Own Pipeline Configuration
# (MODIFIED)
# --------------------------------------------------------------------------


class TestAStackDeclaringNothingAboutTheConvergeIsConverged(
    ConvergeOptOutDiscoveryMixin, unittest.TestCase
):
    """MODIFIED requirement: Each Stack Declares Its Own Pipeline Configuration --
    "whether the host-configuration workflow converges its host, which defaults
    to the host **being** converged when absent".

    GREEN at authoring: the committed discovery reads no such field. What these
    guard is the default's direction once the field is read -- the opposite of
    `deploys_platform`'s, and the one an implementation copied from
    `platform-deploy.yml` would get wrong.
    """

    def test_a_stack_declaring_nothing_about_the_converge_is_converged(self) -> None:
        """SPECIFIED -- scenario "A stack declaring nothing about the converge is
        converged": "the host-configuration workflow SHALL converge that stack's
        host"."""
        tree = self._tree({"alpha": None, "bravo": None})
        code, output, said = self._run(tree)
        self.assertEqual(0, code, f"discovery refused the tree: {said[-800:]!r}")
        self.assertConverges(output, said, "alpha")
        self.assertConverges(output, said, "bravo")
        self.assertFalse(
            names_as_excluded(said, "bravo"),
            f"a stack declaring nothing was named as excluded: {said[-800:]!r}",
        )

    def test_declaring_nothing_converges_exactly_as_declaring_true_does(self) -> None:
        """SPECIFIED -- the same scenario's "exactly as if the declaration had
        stated that it is": the row emitted for a stack that omits the field is the
        row emitted for the same stack declaring `true`."""
        absent = self._tree({"alpha": None})
        declared = self._tree({"alpha": True})
        code_absent, output_absent, said_absent = self._run(absent)
        code_declared, output_declared, said_declared = self._run(declared)
        self.assertEqual(0, code_absent, said_absent[-800:])
        self.assertEqual(0, code_declared, said_declared[-800:])
        self.assertEqual(
            rows_naming(matrix_rows(output_declared), "alpha"),
            rows_naming(matrix_rows(output_absent), "alpha"),
            "the row emitted for a stack omitting the converge field differs from the "
            "row for the same stack declaring it true",
        )
        self.assertTrue(rows_naming(matrix_rows(output_declared), "alpha"), output_declared)


class TestAnUnrecognisedConvergeValueIsRefused(ConvergeOptOutDiscoveryMixin, unittest.TestCase):
    """MODIFIED requirement: Each Stack Declares Its Own Pipeline Configuration --
    scenario "An unrecognised converge value is refused"."""

    def test_an_unrecognised_converge_value_is_refused_naming_stack_and_value(self) -> None:
        """SPECIFIED -- "host-configuration discovery SHALL fail naming that stack
        and the value, rather than reading the value as either answer". Each value
        is one a YAML reader and a line reader could each resolve differently, so a
        silent coercion in either direction would be read here as acceptance."""
        for value in ("maybe", "yes", "disabled"):
            with self.subTest(value=value):
                tree = self._tree({"alpha": None, "bravo": value})
                code, output, said = self._run(tree)
                self.assertNotEqual(
                    0,
                    code,
                    f"a declaration whose converge field reads {value!r} was resolved to "
                    f"an answer rather than refused. Output: {output!r}",
                )
                self.assertIn("bravo", said, f"the refusal names no stack: {said[-800:]!r}")
                self.assertIn(value, said, f"the refusal names no value: {said[-800:]!r}")


# --------------------------------------------------------------------------
# The committed tree (DERIVED: design.md Decision 5, tasks.md 3.1 and 3.2)
# --------------------------------------------------------------------------


class TestTheCommittedDeclarationsStateTheConvergeAsDecided(unittest.TestCase):
    """What the committed declarations say after this change. No scenario names
    a stack; these trace to design.md Decision 5 and tasks.md 3.1-3.2, except
    where an assertion says SPECIFIED.

    RED at authoring on `main-staging`'s two fields, which is the observed
    failure the testing standard counts as evidence that these checks
    discriminate on real content; `TestTheseReadsDiscriminate` is the fixture
    that keeps establishing it afterwards.
    """

    def setUp(self) -> None:
        self.declarations = environment_declarations()

    def _mapping(self, stack: str) -> dict:
        declaration = self.declarations.get(stack)
        if declaration is None or declaration.path is None:
            self.fail(f"terraform/stacks/{stack}/ carries no pipeline declaration")
        return declaration.mapping

    def test_staging_declares_its_host_is_not_converged(self) -> None:
        """DERIVED -- design.md Decision 5: "`converges_host: false` uses the new
        field"."""
        value, offence = converge_value(self._mapping(STAGING_DIRECTORY))
        self.assertIsNone(offence, offence)
        self.assertIs(
            False,
            value,
            f"{STAGING_DIRECTORY}'s declaration does not state `{CONVERGE_KEY}: false`, "
            "so its decommissioned server keeps producing a red converge row on every "
            f"merge touching `ansible/` (read {value!r})",
        )

    def test_staging_declares_no_platform_deploy(self) -> None:
        """DERIVED -- design.md Decision 5: "`deploys_platform: false` uses the
        existing one". Asserted as declared `false`, not merely absent, because the
        decision is to flip the value with a comment saying why."""
        value, offence = platform_opt_in(self._mapping(STAGING_DIRECTORY))
        self.assertIsNone(offence, offence)
        self.assertIs(
            False,
            value,
            f"{STAGING_DIRECTORY}'s declaration does not state the platform deploy as "
            f"false (read {value!r}), so every merge touching `platform/` starts a "
            "deploy row aimed at a host that no longer exists",
        )

    def test_production_keeps_the_converge_default(self) -> None:
        """DERIVED -- tasks.md 3.1: document the field "without setting it, so
        production keeps the default". Absent or `true` both satisfy it; only an
        exclusion would not."""
        value, offence = converge_value(self._mapping(PROD_DIRECTORY))
        self.assertIsNone(offence, offence)
        self.assertIn(
            value,
            (None, True),
            f"{PROD_DIRECTORY}'s declaration excludes its own host from the converge",
        )

    def test_no_committed_declaration_states_the_converge_in_a_refused_form(self) -> None:
        """SPECIFIED -- scenario "An unrecognised converge value is refused", read
        against the committed tree: a tree carrying such a value is one discovery
        refuses on every run."""
        offences = []
        for name, declaration in sorted(self.declarations.items()):
            _, offence = converge_value(declaration.mapping)
            if offence:
                offences.append(f"{name}: {offence}")
        self.assertEqual([], offences, "; ".join(offences))

    def test_the_converge_field_names_what_is_true_when_it_is_true(self) -> None:
        """SPECIFIED -- "Each optional field SHALL name what happens when it is
        **true** ... or whether the host is converged, rather than whether the
        stack is disposable, excluded or dormant". Guarded on at least one
        declaration carrying a converge-naming field, so it does not pass over a
        tree where nobody declares one."""
        mappings = {name: d.mapping for name, d in self.declarations.items()}
        carrying = [
            name
            for name, mapping in mappings.items()
            if any("converge" in re.sub(r"[^a-z0-9]", "", str(k).lower()) for k in mapping)
        ]
        self.assertTrue(
            carrying,
            "no committed declaration carries a field naming the converge, so the "
            "polarity read below has nothing to read",
        )
        offenders = polarity_offences(mappings)
        self.assertEqual(
            [],
            offenders,
            "these fields name the inverse of what they state, so the value that "
            f"converges a host reads as the value that excludes it: {offenders}",
        )


class TestTheCommittedTreeConvergesProductionAndExcludesStaging(
    ConvergeOptOutDiscoveryMixin, unittest.TestCase
):
    """DERIVED -- design.md Migration Plan step 2: "The next merge touching
    `ansible/` runs a converge with `main-production` only, and the run names
    `main-staging` as excluded". Executes the workflow's own discovery body over
    a COPY of the committed `terraform/stacks/` and `ansible/inventory/`, so the
    committed declarations and the committed body are exercised together and
    nothing is written into the working tree.

    UNRESOLVED PROJECT QUESTION (recorded in test-plan.md): that discovery reads
    nothing outside those two directories is assumed, not stated anywhere. If it
    does, this test fails on the copy rather than on the property, and the copy
    is what to widen.
    """

    def _committed_copy(self) -> Path:
        scratch = self._scratch()
        ignore = shutil.ignore_patterns(".terraform", "*.tfstate", "*.tfstate.*", "*.tfplan")
        for relative in (Path("terraform") / "stacks", Path("ansible") / "inventory"):
            shutil.copytree(ROOT / relative, scratch / relative, ignore=ignore)
        return scratch

    def test_a_merge_converges_production_alone_and_names_staging_as_excluded(self) -> None:
        tree = self._committed_copy()
        code, output, said = self._run(tree)
        self.assertEqual(
            0, code, f"discovery refused the committed tree: {said[-800:]!r}"
        )
        self.assertConverges(output, said, PROD_DIRECTORY)
        self.assertNotConverged(output, STAGING_DIRECTORY)
        self.assertTrue(
            names_as_excluded(said, STAGING_DIRECTORY),
            f"the run over the committed tree does not name {STAGING_DIRECTORY} as "
            f"excluded: {said[-800:]!r}",
        )


# --------------------------------------------------------------------------
# Fixture-driven discriminators for the reads above
# --------------------------------------------------------------------------


class TestTheseReadsDiscriminate(unittest.TestCase):
    """Each read this module's committed-tree checks rest on, run over material
    supplied here, so a read that asserted nothing would fail here rather than
    pass silently there. DERIVED throughout: these establish that the checks can
    fail, and add no requirement of their own."""

    def test_an_absent_converge_field_reads_as_the_default(self) -> None:
        self.assertEqual((None, None), converge_value({"github_environment": "x"}))

    def test_a_declared_converge_field_reads_as_declared(self) -> None:
        self.assertEqual((False, None), converge_value({CONVERGE_KEY: False}))
        self.assertEqual((True, None), converge_value({CONVERGE_KEY: True}))

    def test_a_non_boolean_converge_field_is_an_offence(self) -> None:
        value, offence = converge_value({CONVERGE_KEY: "maybe"})
        self.assertIsNone(value)
        self.assertIn("maybe", offence)

    def test_an_inverted_field_name_is_reported(self) -> None:
        self.assertEqual(
            ["alpha: 'host_converge_excluded'"],
            polarity_offences({"alpha": {"host_converge_excluded": True}}),
        )
        self.assertEqual([], polarity_offences({"alpha": {CONVERGE_KEY: False}}))

    def test_matrix_rows_are_read_from_both_output_forms(self) -> None:
        inline = 'matrix={"include":[{"stack":"alpha","environment":"alpha-environment"}]}\n'
        heredoc = 'matrix<<EOF\n["alpha"]\nEOF\nother=plain\n'
        self.assertTrue(rows_naming(matrix_rows(inline), "alpha"))
        self.assertTrue(rows_naming(matrix_rows(heredoc), "alpha"))
        self.assertEqual([], rows_naming(matrix_rows(inline), "bravo"))
        self.assertEqual([], rows_naming(matrix_rows("matrix=not json\n"), "alpha"))

    def test_a_row_for_a_longer_name_does_not_name_a_shorter_one(self) -> None:
        rows = matrix_rows('m={"include":[{"stack":"alpha-environment"}]}\n')
        self.assertEqual([], rows_naming(rows, "alpha"))

    def test_naming_as_excluded_needs_the_name_and_the_exclusion_on_one_line(self) -> None:
        self.assertTrue(
            names_as_excluded("Excluded by their own declarations: bravo", "bravo")
        )
        self.assertFalse(names_as_excluded("bravo\nExcluded: charlie", "bravo"))
        self.assertFalse(names_as_excluded("Excluded: bravo-two", "bravo"))


if __name__ == "__main__":
    unittest.main()
