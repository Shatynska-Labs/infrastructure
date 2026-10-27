"""Every stack's `terraform.tfvars` assigns every variable it declares without a
`default`.

Written for `docs/backlog.md`'s `assert-every-tfvars-assigns-its-required-variables`,
taken as a fix.

Otherwise a gap surfaces only at plan time: `pr-validation.yml`, `apply.yml` and
`drift.yml` plan with `-input=false`, so the plan fails with `No value for
required variable`, the required check fails, and the nightly drift sweep fails
every night. Finding it that way needs a credential, a workspace and a network;
the same fact is a static read of two committed files.

WHERE A VALUE CAN COME FROM
---------------------------
Only `terraform.tfvars`. No workflow sets a `TF_VAR_` environment variable or
passes `-var`/`-var-file`, and the Hetzner token reaches the provider as
`HCLOUD_TOKEN`, not as a Terraform variable. A stack that starts taking a
variable from elsewhere is the case to revisit this module for.

THE PARSER
----------
This suite carries no HCL library, so the read is lexical: a `variable "<name>"`
block, delimited by brace depth with quoted strings and comments skipped, is
required when no `default` attribute sits at its top level; an assignment is a
top-level `<name> =` line. It is enough for the shapes the stacks use and is
exercised against a fixture below. The shapes it cannot read -- a heredoc, a
`/* */` comment, an unquoted block label -- are refused by name rather than
read wrongly, since each could make a gap pass.

Runner:

    python3 -m unittest discover --start-directory .github/tests
"""

from __future__ import annotations

import re
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
STACKS = ROOT / "terraform" / "stacks"

VARIABLE_OPENING = re.compile(r'^\s*variable\s+"([^"]+)"\s*\{')
ATTRIBUTE = re.compile(r"^\s*([A-Za-z_][A-Za-z0-9_-]*)\s*=")
UNREADABLE = re.compile(r"<<|/\*|^\s*variable\s+[A-Za-z_]", re.MULTILINE)


def stack_directories() -> list[Path]:
    """Every stack directory under `terraform/stacks/`."""
    if not STACKS.is_dir():
        return []
    return sorted(
        entry for entry in STACKS.iterdir() if entry.is_dir() and not entry.name.startswith(".")
    )


def stack_terraform_text(directory: Path) -> str:
    """Every `.tf` file in a stack directory, concatenated."""
    return "\n".join(
        path.read_text(encoding="utf-8") for path in sorted(directory.glob("*.tf"))
    )


def refuse_what_cannot_be_read(text: str, source: str) -> None:
    """Raise where `text` holds a shape the lexical read would misread."""
    found = UNREADABLE.search(text)
    if found:
        line = text.count("\n", 0, found.start()) + 1
        raise AssertionError(
            f"{source}:{line} holds `{found.group(0).strip()}`, a heredoc, block "
            f"comment or unquoted label this module's lexical HCL read cannot "
            f"follow; extend the parser before trusting its verdict"
        )


def _code(line: str) -> str:
    """The line with brackets inside quoted strings dropped and any comment
    removed, so a brace or a `#` inside a description is not read as structure."""
    kept = []
    quoted = False
    index = 0
    while index < len(line):
        char = line[index]
        if quoted:
            if char == "\\":
                index += 2
                continue
            if char == '"':
                quoted = False
            if char not in "{}[]":
                kept.append(char)
        elif char == '"':
            quoted = True
            kept.append(char)
        elif char == "#" or line.startswith("//", index):
            break
        else:
            kept.append(char)
        index += 1
    return "".join(kept)


def required_variables(terraform: str) -> set[str]:
    """The variables declared in `terraform` with no top-level `default`."""
    required: set[str] = set()
    current: str | None = None
    has_default = False
    depth = 0
    for line in terraform.splitlines():
        code = _code(line)
        if current is None:
            opening = VARIABLE_OPENING.match(code)
            if not opening:
                continue
            current, has_default, depth = opening.group(1), False, 0
        elif depth == 1:
            attribute = ATTRIBUTE.match(code)
            if attribute and attribute.group(1) == "default":
                has_default = True
        depth += code.count("{") - code.count("}")
        if depth <= 0:
            if not has_default:
                required.add(current)
            current = None
    return required


def assigned_variables(tfvars: str) -> set[str]:
    """The names a `.tfvars` file assigns at its top level."""
    assigned: set[str] = set()
    depth = 0
    for line in tfvars.splitlines():
        code = _code(line)
        if depth == 0:
            attribute = ATTRIBUTE.match(code)
            if attribute:
                assigned.add(attribute.group(1))
        depth += code.count("{") + code.count("[") - code.count("}") - code.count("]")
    return assigned


def unassigned_required_variables(directory: Path) -> list[str]:
    """The stack's required variables its `terraform.tfvars` does not assign."""
    tfvars = directory / "terraform.tfvars"
    tfvars_text = tfvars.read_text(encoding="utf-8") if tfvars.is_file() else ""
    terraform = stack_terraform_text(directory)
    refuse_what_cannot_be_read(terraform, f"{directory.name}/*.tf")
    refuse_what_cannot_be_read(tfvars_text, f"{directory.name}/terraform.tfvars")
    return sorted(required_variables(terraform) - assigned_variables(tfvars_text))


class TestEveryTfvarsAssignsItsRequiredVariables(unittest.TestCase):
    """`docs/backlog.md`'s `assert-every-tfvars-assigns-its-required-variables`,
    taken as a fix."""

    def test_there_are_stacks_with_required_variables_to_check(self) -> None:
        """The vacuity guard: the assertion below passes over no stacks, and
        over stacks whose variables the parser failed to find."""
        stacks = stack_directories()
        self.assertTrue(stacks, "no stack directory was found under terraform/stacks/")
        for directory in stacks:
            with self.subTest(stack=directory.name):
                self.assertTrue(
                    required_variables(stack_terraform_text(directory)),
                    f"no required variable was found in {directory.name}, so the "
                    f"check would pass having read nothing -- check the parser "
                    f"before believing the stack has none",
                )

    def test_every_stack_assigns_its_required_variables(self) -> None:
        for directory in stack_directories():
            with self.subTest(stack=directory.name):
                missing = unassigned_required_variables(directory)
                self.assertEqual(
                    [],
                    missing,
                    f"terraform/stacks/{directory.name}/terraform.tfvars does not "
                    f"assign {missing}, which the stack declares without a default. "
                    f"Every pipeline plan runs with -input=false, so the plan fails "
                    f"`No value for required variable`",
                )


class TestTheParserReadsWhatItClaimsTo(unittest.TestCase):
    """The lexical read, against shapes the stacks use and ones that would
    mislead a naive one."""

    TERRAFORM = (
        'variable "plain" {\n'
        '  type = string\n'
        '}\n'
        '\n'
        'variable "defaulted" {\n'
        '  description = "Has a { brace and a # hash in its description"\n'
        '  default     = []\n'
        '}\n'
        '\n'
        'variable "validated" {\n'
        '  type = number\n'
        '  validation {\n'
        '    condition     = var.validated > 0\n'
        '    error_message = "default = 1 is not a default"\n'
        '  }\n'
        '}\n'
        '\n'
        '# variable "commented" {\n'
        'resource "x" "y" {\n'
        '  default = 1\n'
        '}\n'
    )

    def test_required_are_those_without_a_top_level_default(self) -> None:
        self.assertEqual({"plain", "validated"}, required_variables(self.TERRAFORM))

    def test_assignments_are_read_at_the_top_level_only(self) -> None:
        tfvars = (
            '# commented = 1\n'
            'plain = "a" # trailing\n'
            'listed = [\n'
            '  "nested = no",\n'
            ']\n'
            'mapped = {\n'
            '  inner = 1\n'
            '}\n'
        )
        self.assertEqual({"plain", "listed", "mapped"}, assigned_variables(tfvars))

    def test_an_unassigned_required_variable_is_reported(self) -> None:
        with tempfile.TemporaryDirectory() as scratch:
            directory = Path(scratch)
            (directory / "variables.tf").write_text(self.TERRAFORM, encoding="utf-8")
            (directory / "terraform.tfvars").write_text('plain = "a"\n', encoding="utf-8")
            self.assertEqual(["validated"], unassigned_required_variables(directory))

    def test_shapes_the_read_cannot_follow_are_refused(self) -> None:
        for text in (
            'variable "a" {\n  description = <<-EOT\n  default = 1\n  EOT\n}\n',
            '/* variable "a" { default = 1 } */\n',
            "variable a {\n}\n",
        ):
            with self.subTest(text=text):
                with self.assertRaises(AssertionError):
                    refuse_what_cannot_be_read(text, "fixture")


if __name__ == "__main__":
    unittest.main()
