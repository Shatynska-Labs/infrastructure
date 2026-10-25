"""Static-assertion tests for recording `basis-api`'s durable store.

Derived from the delta specifications of the OpenSpec change
`record-basis-api-durable-store`, before any implementation of that change
existed. The path those deltas sit at is not written here: a change's artifacts
move when it is archived, and this repository's citation convention is to name
the change and the artifact in prose instead. That change's `test-plan.md`
carries the scenario-to-test map, the baseline, the per-assertion
classification, the unresolved project questions and the scenarios left
uncovered.

Requirements traced (each cited by its capability's spec path and its name):

- *Conditional Prod Volume Creation* and *Volume Attached to Prod Server at
  Creation* -- `openspec/specs/iac-data-volumes/spec.md`;
- *Conditional Prod Server Creation* -- `openspec/specs/iac-server-lifecycle/spec.md`;
- *No Store on This Host Holds Data Requiring Backup* --
  `openspec/specs/iac-safety-hardening/spec.md`;
- *Platform Data Volume Is Mounted at a Fixed Host Path* --
  `openspec/specs/iac-host-configuration/spec.md`;
- *A Backed-Up Store's Backup Age Is Alerted On* --
  `openspec/specs/iac-platform-services/spec.md` (a requirement this change
  adds, so its name resolves there once the change is archived).

Why this suite
--------------
Every property here is a static read of a committed file: a stack's `main.tf`,
an inventory vars file, `platform/docker-compose.yml`, a document. The stack's
`count` and its choice of `location` are unreachable by `terraform test`, which
exercises modules only; the inventory's placement of a variable is not a
behaviour of the role Molecule converges. Standard library plus PyYAML -- no
network, no credential, no container runtime, no Terraform binary, and nothing
here spawns a process.

WHAT NO ASSERTION HERE ESTABLISHES
----------------------------------
That `terraform plan` shows what the scenarios say it shows. The plan's
outcome rests on the provider's treatment of `Optional, Computed` attributes,
which design.md decision 3 reasons from provider source and tasks.md 1.4/1.5
check against real plans. What is asserted is that the committed configuration
has the shape that reasoning depends on.

That an alert fires. Nothing here runs Prometheus; tasks.md 7.2 provokes each
rule on the host.

Provenance
----------
Every assertion is annotated SPECIFIED (traces to SHALL text or a scenario in
the delta) or DERIVED (traces to design.md/tasks.md, or to this pass's own
judgement). Every check is a function over a path or a text so that the
fixture-driven discriminators at the end of each section can point it at
material the test supplies; those discriminators are what make this module's
green mean anything.

No helper is imported from a sibling test module: AGENTS.md ("Testing") records
that this suite has no shared arrangement, and that a derivation does not
import from `test_ci_configuration.py`. Everything this file needs is declared
below and listed in that change's `test-plan.md` under "Missing shared
arrangement".

Runner
------
    python3 -m unittest discover --start-directory .github/tests

    # a single test:
    python3 -m unittest discover --start-directory .github/tests \\
        -k test_basis_api_durable_store.TestProductionVolumeSurvivesTheServerToggle

Run from the repository root.

NOTHING IN THIS FILE EDITS, DELETES OR DISABLES AN EXISTING TEST.
"""

from __future__ import annotations

import re
import shutil
import tempfile
import unittest
from pathlib import Path

import yaml

# --------------------------------------------------------------------------
# Locally declared arrangement (no shared arrangement exists in this suite)
# --------------------------------------------------------------------------

ROOT = Path(__file__).resolve().parents[2]

PRODUCTION_STACK = "terraform/stacks/main-production/main.tf"
STAGING_STACK = "terraform/stacks/main-staging/main.tf"

GROUP_VARS = "ansible/inventory/group_vars"
HOST_VARS = "ansible/inventory/host_vars"
ENVIRONMENT_VARS = ("production.yml", "staging.yml")
PRODUCTION_HOST_VARS = "main-production.yml"

ENV_SUBDIRS_VARIABLE = "platform_data_volume_subdirs"
HOST_SUBDIRS_VARIABLE = "platform_data_volume_host_subdirs"

PLATFORM_COMPOSE = "platform/docker-compose.yml"
NODE_EXPORTER_IMAGE = "prom/node-exporter"
APPLICATION_NETWORK = "platform_edge"
RULES_CONFIG = "prometheus_rules"
ALERTMANAGER_CONFIG = "alertmanager_config"

# The data volume's fixed mount path (*Platform Data Volume Is Mounted at a
# Fixed Host Path*, and the requirement this change adds, which names
# `/mnt/main/applications/<application>/metrics`).
MOUNT = "/mnt/main"
APPLICATIONS_METRICS_GLOB = "mnt/main/applications/*/metrics"
PLATFORM_METRICS_DIR = "applications/platform/metrics"

ONBOARDING = "docs/onboard-an-application.md"
RUNBOOK = "docs/runbook-rebuild.md"
BACKLOG = "docs/backlog.md"
BACKLOG_ENTRY = "finish-basis-api-s-move-to-its-own-database"
RETIRED_ONBOARDING_SENTENCE = "no application has cleared that bar"

TIMESTAMP_METRIC = "backup_last_success_timestamp_seconds"
MAX_AGE_METRIC = "backup_max_age_seconds"
SCRAPE_ERROR_METRIC = "node_textfile_scrape_error"
HANDLER_ERRORS_METRIC = "promhttp_metric_handler_errors_total"

# DERIVED -- the four names come from design.md decision 2 and tasks.md 3.2; the
# requirement describes the alerts without naming them.
BACKUP_STALE = "BackupStale"
BACKUP_AGE_UNBOUNDED = "BackupAgeUnbounded"
TEXTFILE_UNREADABLE = "TextfileMetricsUnreadable"
GATHERING_ERRORS = "NodeExporterGatheringErrors"
FOUR_ALERTS = (BACKUP_STALE, BACKUP_AGE_UNBOUNDED, TEXTFILE_UNREADABLE, GATHERING_ERRORS)


def _base(root: Path | None) -> Path:
    return ROOT if root is None else root


def read_required(path: Path) -> str:
    """A file's text, failing the calling test where it is absent. An absent
    file is a finding, never a reason to skip."""
    if not path.is_file():
        raise AssertionError(f"{path} does not exist")
    return path.read_text(encoding="utf-8")


class _VaultTolerantLoader(yaml.SafeLoader):
    """SafeLoader that reads any unknown tag (Ansible's `!vault`) as an opaque
    string, so a vars file carrying encrypted values still parses."""


def _opaque_tag(loader: yaml.SafeLoader, suffix: str, node: yaml.Node) -> object:
    if isinstance(node, yaml.ScalarNode):
        return loader.construct_scalar(node)
    if isinstance(node, yaml.SequenceNode):
        return loader.construct_sequence(node)
    return loader.construct_mapping(node)


_VaultTolerantLoader.add_multi_constructor("!", _opaque_tag)


def load_vars(path: Path) -> dict:
    document = yaml.load(read_required(path), Loader=_VaultTolerantLoader)
    if document is None:
        return {}
    if not isinstance(document, dict):
        raise AssertionError(f"{path} does not parse as a mapping")
    return document


# ---- HCL: just enough to read one block's top-level attributes ------------


def _strip_hcl_comments(text: str) -> str:
    """Drop `#`, `//` and `/* */` comments, leaving string literals alone."""
    out: list[str] = []
    i, n = 0, len(text)
    in_string = False
    while i < n:
        ch = text[i]
        if in_string:
            out.append(ch)
            if ch == "\\" and i + 1 < n:
                out.append(text[i + 1])
                i += 2
                continue
            if ch == '"':
                in_string = False
            i += 1
            continue
        if ch == '"':
            in_string = True
            out.append(ch)
            i += 1
            continue
        if ch == "#" or text.startswith("//", i):
            while i < n and text[i] != "\n":
                i += 1
            continue
        if text.startswith("/*", i):
            end = text.find("*/", i + 2)
            i = n if end == -1 else end + 2
            continue
        out.append(ch)
        i += 1
    return "".join(out)


def hcl_block(text: str, kind: str, label: str) -> str | None:
    """The body of `<kind> "<label>" { ... }`, or None where it is absent."""
    clean = _strip_hcl_comments(text)
    match = re.search(rf'(?m)^\s*{re.escape(kind)}\s+"{re.escape(label)}"\s*\{{', clean)
    if not match:
        return None
    depth, start = 1, match.end()
    for index in range(start, len(clean)):
        if clean[index] == "{":
            depth += 1
        elif clean[index] == "}":
            depth -= 1
            if depth == 0:
                return clean[start:index]
    raise AssertionError(f'{kind} "{label}" is never closed')


def hcl_blocks_of_kind(text: str, kind: str) -> list[str]:
    clean = _strip_hcl_comments(text)
    return re.findall(rf'(?m)^\s*{re.escape(kind)}\s*\{{([^}}]*)\}}', clean)


def top_level_attributes(body: str) -> dict[str, str]:
    """`name = expression` pairs at depth 0 of a block body, expression
    whitespace-normalised."""
    attributes: dict[str, str] = {}
    depth = 0
    for line in body.splitlines():
        if depth == 0:
            match = re.match(r"^\s*([A-Za-z_][\w-]*)\s*=\s*(.+?)\s*$", line)
            if match:
                attributes[match.group(1)] = " ".join(match.group(2).split())
        depth += line.count("{") + line.count("[") + line.count("(")
        depth -= line.count("}") + line.count("]") + line.count(")")
    return attributes


def stack_module_attributes(path: Path, label: str) -> dict[str, str]:
    body = hcl_block(read_required(path), "module", label)
    if body is None:
        raise AssertionError(f'{path} declares no module "{label}"')
    return top_level_attributes(body)


TOGGLE_CONDITIONAL = re.compile(
    r"^\(?\s*(?P<negated>!\s*)?var\.server_enabled\s*\)?\s*\?\s*(?P<yes>[^:]+?)\s*:\s*(?P<no>.+?)\s*$"
)


def location_by_server_toggle(expression: str) -> dict[bool, str] | None:
    """What a `location` expression yields for each value of
    `var.server_enabled`, where it is a conditional on that toggle alone;
    otherwise None."""
    match = TOGGLE_CONDITIONAL.match(expression)
    if not match:
        return None
    yes, no = match.group("yes").strip(), match.group("no").strip()
    if match.group("negated"):
        yes, no = no, yes
    return {True: yes, False: no}


# ---- Compose ---------------------------------------------------------------


def compose_document(path: Path) -> dict:
    document = yaml.safe_load(read_required(path))
    if not isinstance(document, dict) or not isinstance(document.get("services"), dict):
        raise AssertionError(f"{path} declares no `services:` mapping")
    return document


def node_exporter_service(document: dict) -> dict:
    found = [
        definition
        for definition in document["services"].values()
        if isinstance(definition, dict)
        and str(definition.get("image", "")).split("@")[0].split(":")[0] == NODE_EXPORTER_IMAGE
    ]
    if len(found) != 1:
        raise AssertionError(
            f"expected exactly one service running {NODE_EXPORTER_IMAGE}, found {len(found)}"
        )
    return found[0]


def service_command(service: dict) -> list[str]:
    command = service.get("command")
    if command is None:
        return []
    if isinstance(command, str):
        return command.split()
    return [str(part) for part in command]


def service_mounts(service: dict) -> list[dict]:
    """Every volume entry as {source, target, read_only}, both Compose forms."""
    mounts = []
    for entry in service.get("volumes") or []:
        if isinstance(entry, str):
            parts = entry.split(":")
            if len(parts) == 1:
                mounts.append({"source": None, "target": parts[0], "read_only": False})
                continue
            options = parts[2].split(",") if len(parts) > 2 else []
            mounts.append({"source": parts[0], "target": parts[1], "read_only": "ro" in options})
        elif isinstance(entry, dict):
            mounts.append(
                {
                    "source": entry.get("source"),
                    "target": entry.get("target"),
                    "read_only": bool(entry.get("read_only")),
                }
            )
    return mounts


def service_networks(service: dict) -> list[str]:
    networks = service.get("networks")
    if isinstance(networks, dict):
        return [str(name) for name in networks]
    if isinstance(networks, list):
        return [str(name) for name in networks]
    return []


def config_content(document: dict, name: str) -> str:
    configs = document.get("configs")
    definition = configs.get(name) if isinstance(configs, dict) else None
    content = definition.get("content") if isinstance(definition, dict) else None
    if not isinstance(content, str) or not content.strip():
        raise AssertionError(f"the `{name}` config carries no inline content")
    return content


def alerting_rules(document: dict) -> dict[str, dict]:
    rules_document = yaml.safe_load(config_content(document, RULES_CONFIG)) or {}
    rules: dict[str, dict] = {}
    for group in rules_document.get("groups") or []:
        for rule in (group or {}).get("rules") or []:
            if isinstance(rule, dict) and rule.get("alert"):
                rules[str(rule["alert"])] = rule
    if not rules:
        raise AssertionError(f"the `{RULES_CONFIG}` content declares no alerting rule")
    return rules


def _expr(rule: dict) -> str:
    return " ".join(str(rule.get("expr", "")).split())


def _word(name: str) -> re.Pattern[str]:
    return re.compile(rf"(?<![A-Za-z0-9_]){re.escape(name)}(?![A-Za-z0-9_])")


def _matching_labels(expr: str, keyword: str) -> set[str]:
    match = re.search(rf"\b{keyword}\s*\(([^)]*)\)", expr)
    if not match:
        return set()
    return {label.strip() for label in match.group(1).split(",") if label.strip()}


def annotations_name_store_and_kind(rule: dict) -> bool:
    rendered = yaml.safe_dump(rule.get("annotations") or {})
    return bool(
        re.search(r"\$labels\.store\b|\.Labels\.store\b", rendered)
        and re.search(r"\$labels\.kind\b|\.Labels\.kind\b", rendered)
    )


# --------------------------------------------------------------------------
# Section 1. Terraform stacks: production's volume survives the toggle
# --------------------------------------------------------------------------


def production_volume_offences(path: Path, server_label: str = "server") -> list[str]:
    """Every way a stack's `module "volume"` fails to survive its server
    toggle in the form the requirement states."""
    attributes = stack_module_attributes(path, "volume")
    offences = []
    count = attributes.get("count", "")
    if "var.volume_enabled" not in count:
        offences.append(f"count ({count!r}) does not read var.volume_enabled")
    if "var.server_enabled" in count:
        offences.append(
            f"count ({count!r}) still reads var.server_enabled: the volume's existence "
            "would depend on the server's toggle"
        )
    location = attributes.get("location")
    if location is None:
        offences.append("passes no location, so it cannot exist while no server does")
    else:
        if "module." in location:
            offences.append(
                f"location ({location!r}) turns on a module reference, not on a value "
                "known at plan time"
            )
        branches = location_by_server_toggle(location)
        if branches is None:
            offences.append(
                f"location ({location!r}) is not a choice on var.server_enabled"
            )
        else:
            if branches[True] != "null":
                offences.append(
                    f"location with the server enabled is {branches[True]!r}, not null: "
                    "Hetzner's client refuses a volume created with both"
                )
            server = stack_module_attributes(path, server_label)
            server_location = server.get("location")
            if branches[False] != server_location:
                offences.append(
                    f"location with the server disabled is {branches[False]!r}, not "
                    f"the variable the server's location is taken from "
                    f"({server_location!r})"
                )
            if not branches[False].startswith("var."):
                offences.append(
                    f"location with the server disabled is {branches[False]!r}, not a "
                    "stack variable"
                )
    server_id = attributes.get("server_id", "")
    if "module.server" not in server_id:
        offences.append(
            f"server_id ({server_id!r}) does not reference the stack's server, so a "
            "volume would not be attached to it"
        )
    return offences


def staging_volume_offences(path: Path) -> list[str]:
    """Every way a stack's `module "volume"` fails to stay coupled to its
    server."""
    attributes = stack_module_attributes(path, "volume")
    offences = []
    count = attributes.get("count", "")
    for variable in ("var.volume_enabled", "var.server_enabled"):
        if variable not in count:
            offences.append(f"count ({count!r}) does not read {variable}")
    if "location" in attributes:
        offences.append(
            f"passes location ({attributes['location']!r}); a coupled volume takes its "
            "location from its server"
        )
    if "module.server" not in attributes.get("server_id", ""):
        offences.append("server_id does not reference the stack's server")
    return offences


def moved_blocks_naming_the_volume(path: Path) -> list[str]:
    return [
        " ".join(body.split())
        for body in hcl_blocks_of_kind(read_required(path), "moved")
        if "module.volume" in body
    ]


class TestProductionVolumeSurvivesTheServerToggle(unittest.TestCase):
    """*Conditional Prod Volume Creation*, *Volume Attached to Prod Server at
    Creation*, *Conditional Prod Server Creation*, and *No Store on This Host
    Holds Data Requiring Backup*'s scenario "A store admitted under the
    fallback survives the server toggle".

    RED until tasks.md 1.2 lands: the committed stack gates the volume on both
    toggles and passes no location.
    """

    def test_the_production_volume_survives_its_server_toggle(self) -> None:
        """SPECIFIED -- "The `main-production` volume's existence SHALL depend on
        the volume-enabled variable alone"; "SHALL declare the volume's location
        from the same variable the server's location is taken from"; "passed
        to the volume only while the stack's server toggle is false"; "The
        choice SHALL turn on a value known at plan time -- the toggle, not the
        server reference". Scenarios: "Disabling the server keeps the
        production volume", "Toggle disabled keeps the production volume", "A
        store admitted under the fallback survives the server toggle",
        "Re-enabling the server does not replace the kept volume", "Volume
        shares the server's location", "Declaring the existing volume's
        location changes nothing" (whose no-change outcome rests on the
        location being the server's own variable)."""
        self.assertEqual([], production_volume_offences(ROOT / PRODUCTION_STACK))

    def test_the_production_volume_server_reference_is_null_without_a_server(self) -> None:
        """DERIVED -- design.md decision 3 and tasks.md 1.2 keep
        `server_id = one(module.server[*].id)`, which is what makes the
        reference null in configuration while the server is disabled
        (scenario "Disabling the server keeps the production volume": "the
        volume SHALL carry no server reference in configuration"). A form
        indexing `module.server[0]` would error rather than yield null."""
        attributes = stack_module_attributes(ROOT / PRODUCTION_STACK, "volume")
        self.assertRegex(
            attributes.get("server_id", ""),
            r"^one\(\s*module\.server\[\*\]\.id\s*\)$",
        )

    def test_the_production_volume_keeps_its_address(self) -> None:
        """DERIVED -- design.md decision 3: "The address stays
        `module.volume[0].hcloud_volume.this`: no `moved` block." A moved
        volume address is how a refactor plans a destroy-and-create of the
        store this change exists to keep. Green at authoring; protects."""
        self.assertEqual([], moved_blocks_naming_the_volume(ROOT / PRODUCTION_STACK))

    def test_the_staging_volume_stays_coupled_to_its_server(self) -> None:
        """SPECIFIED -- "`main-staging`'s volume remains coupled to its server,
        its effective existence depending on both toggles together"; "A stack
        whose volume is coupled to its server (`main-staging`) SHALL let the
        volume take its location from that server rather than declaring one".
        Scenario "Disabling the server also removes the volume" and *Conditional
        Prod Server Creation*'s "Other resources MAY be coupled". Green at
        authoring; protects against the decoupling spreading to staging."""
        self.assertEqual([], staging_volume_offences(ROOT / STAGING_STACK))


class TestTheStackChecksDiscriminate(unittest.TestCase):
    """Fixture-driven discriminators for section 1."""

    SERVER = 'module "server" {\n  source = "../../modules/server"\n  count = var.server_enabled ? 1 : 0\n  location = var.location\n}\n'

    def _stack(self, volume_body: str, extra: str = "") -> Path:
        directory = Path(tempfile.mkdtemp(prefix="durable-store-stack-"))
        self.addCleanup(shutil.rmtree, directory, ignore_errors=True)
        path = directory / "main.tf"
        path.write_text(
            self.SERVER + 'module "volume" {\n' + volume_body + "}\n" + extra, encoding="utf-8"
        )
        return path

    DECOUPLED = (
        "  # the volume survives the toggle\n"
        "  source    = \"../../modules/volume\"\n"
        "  count     = var.volume_enabled ? 1 : 0\n"
        "  server_id = one(module.server[*].id)\n"
        "  location  = var.server_enabled ? null : var.location\n"
        "  labels = {\n    role = \"data\"\n  }\n"
    )
    COUPLED = (
        "  source    = \"../../modules/volume\"\n"
        "  count     = var.volume_enabled && var.server_enabled ? 1 : 0\n"
        "  server_id = one(module.server[*].id)\n"
    )

    def test_the_decoupled_form_is_accepted(self) -> None:
        self.assertEqual([], production_volume_offences(self._stack(self.DECOUPLED)))

    def test_the_negated_spelling_is_accepted(self) -> None:
        body = self.DECOUPLED.replace(
            "var.server_enabled ? null : var.location", "!var.server_enabled ? var.location : null"
        )
        self.assertEqual([], production_volume_offences(self._stack(body)))

    def test_the_coupled_form_is_reported_for_production(self) -> None:
        offences = production_volume_offences(self._stack(self.COUPLED))
        self.assertTrue(any("var.server_enabled" in o for o in offences), offences)
        self.assertTrue(any("passes no location" in o for o in offences), offences)

    def test_a_choice_on_the_server_reference_is_reported(self) -> None:
        body = self.DECOUPLED.replace(
            "var.server_enabled ? null : var.location",
            "one(module.server[*].id) == null ? var.location : null",
        )
        offences = production_volume_offences(self._stack(body))
        self.assertTrue(any("plan time" in o for o in offences), offences)

    def test_a_location_passed_with_the_server_enabled_is_reported(self) -> None:
        body = self.DECOUPLED.replace(
            "var.server_enabled ? null : var.location", "var.location"
        )
        self.assertNotEqual([], production_volume_offences(self._stack(body)))

    def test_a_separately_specified_location_is_reported(self) -> None:
        body = self.DECOUPLED.replace(
            "var.server_enabled ? null : var.location",
            "var.server_enabled ? null : var.volume_location",
        )
        offences = production_volume_offences(self._stack(body))
        self.assertTrue(any("server's location" in o for o in offences), offences)

    def test_a_literal_location_is_reported(self) -> None:
        body = self.DECOUPLED.replace(
            "var.server_enabled ? null : var.location", 'var.server_enabled ? null : "hel1"'
        )
        self.assertNotEqual([], production_volume_offences(self._stack(body)))

    def test_the_coupled_form_is_accepted_for_staging(self) -> None:
        self.assertEqual([], staging_volume_offences(self._stack(self.COUPLED)))

    def test_the_decoupled_form_is_reported_for_staging(self) -> None:
        offences = staging_volume_offences(self._stack(self.DECOUPLED))
        self.assertTrue(any("var.server_enabled" in o for o in offences), offences)
        self.assertTrue(any("passes location" in o for o in offences), offences)

    def test_a_commented_out_location_is_not_read(self) -> None:
        body = self.COUPLED.replace(
            "  server_id", "  # location = var.server_enabled ? null : var.location\n  server_id"
        ).replace("var.volume_enabled && var.server_enabled", "var.volume_enabled")
        offences = production_volume_offences(self._stack(body))
        self.assertTrue(any("passes no location" in o for o in offences), offences)

    def test_a_moved_block_naming_the_volume_is_reported(self) -> None:
        path = self._stack(
            self.DECOUPLED,
            'moved {\n  from = module.volume\n  to   = module.volume[0]\n}\n',
        )
        self.assertEqual(1, len(moved_blocks_naming_the_volume(path)))

    def test_an_absent_stack_fails_rather_than_passing(self) -> None:
        with self.assertRaises(AssertionError):
            production_volume_offences(Path(tempfile.gettempdir()) / "no-such-stack" / "main.tf")


# --------------------------------------------------------------------------
# Section 2. Inventory: the application's directories, on its own host
# --------------------------------------------------------------------------


def _norm_id(value: object) -> str:
    return str(value).strip()


def _norm_mode(value: object) -> str:
    if isinstance(value, int):
        return format(value, "04o")
    text = str(value).strip()
    return text if len(text) == 4 else text.rjust(4, "0")


def subdir_entries(document: dict, variable: str) -> list[dict]:
    entries = document.get(variable)
    if entries is None:
        return []
    if not isinstance(entries, list):
        raise AssertionError(f"{variable} is {type(entries).__name__}, not a list")
    return [entry for entry in entries if isinstance(entry, dict)]


def _owned(entry: dict, owner: str, group: str, mode: str) -> bool:
    return (
        _norm_id(entry.get("owner")) in owner.split("|")
        and _norm_id(entry.get("group")) in group.split("|")
        and _norm_mode(entry.get("mode")) == mode
    )


# DERIVED -- the parents' ownership is design.md decision 4 ("all `root:root
# 0755`"); the requirement itself says only that the metrics directory is
# "empty and root-owned".
ENVIRONMENT_SUBDIRS_EXPECTED = (
    ("applications", "root|0", "root|0", "0755"),
    ("applications/platform", "root|0", "root|0", "0755"),
    (PLATFORM_METRICS_DIR, "root|0", "root|0", "0755"),
)

# DERIVED -- the entries and their ownership are design.md decision 4 and
# tasks.md 2.2 (`999` is the Debian-based postgres image's user).
PRODUCTION_HOST_SUBDIRS_EXPECTED = (
    ("applications/basis-api", "root|0", "root|0", "0755"),
    ("applications/basis-api/postgres", "999", "999", "0700"),
    ("applications/basis-api/metrics", "999", "999", "0755"),
)


def environment_subdir_offences(path: Path) -> list[str]:
    entries = {str(e.get("path", "")).strip("/"): e for e in subdir_entries(load_vars(path), ENV_SUBDIRS_VARIABLE)}
    offences = []
    for subdir, owner, group, mode in ENVIRONMENT_SUBDIRS_EXPECTED:
        entry = entries.get(subdir)
        if entry is None:
            offences.append(f"{path.name}: {ENV_SUBDIRS_VARIABLE} declares no {subdir}")
        elif not _owned(entry, owner, group, mode):
            offences.append(
                f"{path.name}: {subdir} is {entry.get('owner')}:{entry.get('group')} "
                f"{entry.get('mode')}, wanted root:root {mode}"
            )
    return offences


def host_subdir_offences(path: Path) -> list[str]:
    entries = subdir_entries(load_vars(path), HOST_SUBDIRS_VARIABLE)
    by_path = {str(e.get("path", "")).strip("/"): e for e in entries}
    offences = []
    for subdir, owner, group, mode in PRODUCTION_HOST_SUBDIRS_EXPECTED:
        entry = by_path.get(subdir)
        if entry is None:
            offences.append(f"{path.name}: {HOST_SUBDIRS_VARIABLE} declares no {subdir}")
        elif not _owned(entry, owner, group, mode):
            offences.append(
                f"{path.name}: {subdir} is {entry.get('owner')}:{entry.get('group')} "
                f"{entry.get('mode')}, wanted {owner.split('|')[0]}:{group.split('|')[0]} {mode}"
            )
    return offences


APPLICATION_PATH = re.compile(r"^applications/(?P<app>[^/]+)(/.*)?$")


def host_subdirs_outside_an_application(path: Path) -> list[str]:
    """Every host-scoped entry not beneath `applications/<application>/`, or
    claiming the platform's own directory there."""
    offences = []
    for entry in subdir_entries(load_vars(path), HOST_SUBDIRS_VARIABLE):
        subdir = str(entry.get("path", "")).strip("/")
        match = APPLICATION_PATH.match(subdir)
        if not match or match.group("app") == "platform":
            offences.append(f"{path.name}: {subdir!r}")
    return offences


def application_subdirs_in_group_vars(directory: Path) -> list[str]:
    """Every group_vars file declaring the host-scoped list, or an
    environment-wide entry under an application's directory."""
    files = sorted(directory.glob("*.yml")) + sorted(directory.glob("*/*.yml"))
    if not files:
        raise AssertionError(f"{directory} holds no vars file, so nothing was read")
    offences = []
    for path in files:
        document = load_vars(path)
        if HOST_SUBDIRS_VARIABLE in document:
            offences.append(f"{path.name} declares {HOST_SUBDIRS_VARIABLE}")
        for entry in subdir_entries(document, ENV_SUBDIRS_VARIABLE):
            subdir = str(entry.get("path", "")).strip("/")
            match = APPLICATION_PATH.match(subdir)
            if match and match.group("app") != "platform":
                offences.append(f"{path.name} declares {subdir} for every host")
    return offences


def other_hosts_declaring(directory: Path, own: str, application: str) -> list[str]:
    offences = []
    for path in sorted(directory.glob("*.yml")):
        if path.name == own:
            continue
        for entry in subdir_entries(load_vars(path), HOST_SUBDIRS_VARIABLE):
            if str(entry.get("path", "")).strip("/").startswith(f"applications/{application}"):
                offences.append(f"{path.name}: {entry.get('path')}")
    return offences


class TestTheApplicationsDirectoriesAreHostScoped(unittest.TestCase):
    """*Platform Data Volume Is Mounted at a Fixed Host Path*, scenario "An
    application's subdirectories exist on the host it is declared for" (the
    inventory half -- Molecule's `with-application-subdirs` scenario holds the
    converge half), and the platform's always-present metrics directory the
    requirement *A Backed-Up Store's Backup Age Is Alerted On* relies on."""

    def test_every_environment_carries_the_platform_metrics_directory(self) -> None:
        """SPECIFIED -- "The environment's own subdirectories SHALL include
        `applications/platform/metrics`, empty and root-owned, on every host";
        *A Backed-Up Store's Backup Age Is Alerted On*: "The collector's
        pattern SHALL match at least one directory on every host". Parents'
        ownership DERIVED (design.md decision 4). RED until tasks.md 2.2."""
        offences = []
        for name in ENVIRONMENT_VARS:
            offences += environment_subdir_offences(ROOT / GROUP_VARS / name)
        self.assertEqual([], offences)

    def test_production_declares_basis_api_directories_in_its_own_host_vars(self) -> None:
        """SPECIFIED -- "An application's subdirectories on the volume SHALL be
        declared in the vars file of the host it is deployed to". The entries
        and their ownership DERIVED (design.md decision 4, tasks.md 2.2). RED
        until tasks.md 2.2."""
        self.assertEqual([], host_subdir_offences(ROOT / HOST_VARS / PRODUCTION_HOST_VARS))

    def test_host_scoped_entries_sit_beneath_their_application(self) -> None:
        """SPECIFIED -- "They SHALL sit beneath `applications/<application>/`,
        so that no application's directory can be mistaken for a platform
        service's." Paired with the test above so an empty list cannot pass it
        vacuously."""
        path = ROOT / HOST_VARS / PRODUCTION_HOST_VARS
        self.assertNotEqual([], subdir_entries(load_vars(path), HOST_SUBDIRS_VARIABLE))
        self.assertEqual([], host_subdirs_outside_an_application(path))

    def test_no_environment_wide_file_declares_an_applications_directory(self) -> None:
        """SPECIFIED -- "no other host SHALL receive them": a declaration in
        `group_vars` reaches every host of the environment. Green at
        authoring; protects."""
        self.assertEqual([], application_subdirs_in_group_vars(ROOT / GROUP_VARS))

    def test_no_other_host_declares_basis_api_directories(self) -> None:
        """SPECIFIED -- "no other host SHALL receive them". Green at authoring;
        protects."""
        self.assertEqual(
            [], other_hosts_declaring(ROOT / HOST_VARS, PRODUCTION_HOST_VARS, "basis-api")
        )


class TestTheInventoryChecksDiscriminate(unittest.TestCase):
    """Fixture-driven discriminators for section 2."""

    def _file(self, name: str, text: str, sub: str = "") -> Path:
        directory = Path(tempfile.mkdtemp(prefix="durable-store-vars-"))
        self.addCleanup(shutil.rmtree, directory, ignore_errors=True)
        (directory / sub).mkdir(parents=True, exist_ok=True)
        path = directory / sub / name
        path.write_text(text, encoding="utf-8")
        return path

    ENV_GOOD = (
        "secret: !vault |\n  $ANSIBLE_VAULT;1.1;AES256\n  3031\n"
        f"{ENV_SUBDIRS_VARIABLE}:\n"
        "  - {path: prometheus, owner: '65534', group: '65534', mode: '0755'}\n"
        "  - {path: applications, owner: root, group: root, mode: '0755'}\n"
        "  - {path: applications/platform, owner: root, group: root, mode: '0755'}\n"
        "  - {path: applications/platform/metrics, owner: root, group: root, mode: '0755'}\n"
    )
    HOST_GOOD = (
        f"{HOST_SUBDIRS_VARIABLE}:\n"
        "  - {path: applications/basis-api, owner: root, group: root, mode: '0755'}\n"
        "  - {path: applications/basis-api/postgres, owner: '999', group: '999', mode: '0700'}\n"
        "  - {path: applications/basis-api/metrics, owner: '999', group: '999', mode: '0755'}\n"
    )

    def test_a_complete_environment_file_is_accepted_through_a_vault_tag(self) -> None:
        self.assertEqual([], environment_subdir_offences(self._file("production.yml", self.ENV_GOOD)))

    def test_a_missing_platform_metrics_directory_is_reported(self) -> None:
        text = "\n".join(l for l in self.ENV_GOOD.splitlines() if "platform/metrics" not in l)
        self.assertNotEqual([], environment_subdir_offences(self._file("production.yml", text)))

    def test_a_non_root_platform_metrics_directory_is_reported(self) -> None:
        text = self.ENV_GOOD.replace(
            "applications/platform/metrics, owner: root", "applications/platform/metrics, owner: '65534'"
        )
        self.assertNotEqual([], environment_subdir_offences(self._file("production.yml", text)))

    def test_a_complete_host_file_is_accepted(self) -> None:
        self.assertEqual([], host_subdir_offences(self._file("main-production.yml", self.HOST_GOOD)))

    def test_the_postgres_directory_world_traversable_is_reported(self) -> None:
        text = self.HOST_GOOD.replace("mode: '0700'", "mode: '0755'")
        self.assertNotEqual([], host_subdir_offences(self._file("main-production.yml", text)))

    def test_the_alpine_uid_is_reported(self) -> None:
        text = self.HOST_GOOD.replace("postgres, owner: '999', group: '999'", "postgres, owner: '70', group: '70'")
        self.assertNotEqual([], host_subdir_offences(self._file("main-production.yml", text)))

    def test_a_host_file_declaring_nothing_is_reported(self) -> None:
        self.assertNotEqual([], host_subdir_offences(self._file("main-production.yml", "x: 1\n")))

    def test_an_entry_outside_applications_is_reported(self) -> None:
        text = self.HOST_GOOD + "  - {path: basis-api, owner: root, group: root, mode: '0755'}\n"
        self.assertEqual(
            ["main-production.yml: 'basis-api'"],
            host_subdirs_outside_an_application(self._file("main-production.yml", text)),
        )

    def test_an_entry_under_the_platform_directory_is_reported(self) -> None:
        text = self.HOST_GOOD + "  - {path: applications/platform/x, owner: root, group: root, mode: '0755'}\n"
        self.assertNotEqual([], host_subdirs_outside_an_application(self._file("main-production.yml", text)))

    def test_an_application_directory_in_group_vars_is_reported(self) -> None:
        path = self._file(
            "staging.yml",
            self.ENV_GOOD + "  - {path: applications/basis-api, owner: root, group: root, mode: '0755'}\n",
        )
        self.assertEqual(1, len(application_subdirs_in_group_vars(path.parent)))

    def test_the_host_list_in_group_vars_is_reported(self) -> None:
        path = self._file("production.yml", self.ENV_GOOD + self.HOST_GOOD)
        self.assertEqual(1, len(application_subdirs_in_group_vars(path.parent)))

    def test_the_platform_directory_in_group_vars_is_not_reported(self) -> None:
        path = self._file("production.yml", self.ENV_GOOD)
        self.assertEqual([], application_subdirs_in_group_vars(path.parent))

    def test_another_host_declaring_basis_api_is_reported(self) -> None:
        own = self._file("main-production.yml", self.HOST_GOOD)
        (own.parent / "main-staging.yml").write_text(self.HOST_GOOD, encoding="utf-8")
        self.assertEqual(3, len(other_hosts_declaring(own.parent, own.name, "basis-api")))

    def test_an_empty_group_vars_directory_fails_rather_than_passing(self) -> None:
        directory = Path(tempfile.mkdtemp(prefix="durable-store-empty-"))
        self.addCleanup(shutil.rmtree, directory, ignore_errors=True)
        with self.assertRaises(AssertionError):
            application_subdirs_in_group_vars(directory)


# --------------------------------------------------------------------------
# Section 3. Platform stack: collection and the four rules
# --------------------------------------------------------------------------


def collection_offences(path: Path) -> list[str]:
    """Every way node-exporter fails to read the application metrics
    directories through its read-only root mount, off the application
    network."""
    service = node_exporter_service(compose_document(path))
    offences = []
    root_mounts = [m for m in service_mounts(service) if m["source"] == "/"]
    if not root_mounts:
        offences.append("node-exporter has no mount of the host's root filesystem")
    elif not all(m["read_only"] for m in root_mounts):
        offences.append("node-exporter's root filesystem mount is not read-only")
    for mount in service_mounts(service):
        source = str(mount["source"] or "")
        if source == MOUNT or source.startswith(MOUNT + "/"):
            offences.append(f"node-exporter mounts {source} directly rather than through /")
    targets = [str(m["target"]).rstrip("/") for m in root_mounts]
    flags = [
        part.split("=", 1)[1]
        for part in service_command(service)
        if part.startswith("--collector.textfile.directory=")
    ]
    wanted = [f"{target}/{APPLICATIONS_METRICS_GLOB}" for target in targets]
    if not any(flag in wanted for flag in flags):
        offences.append(
            f"node-exporter's textfile directories are {flags}; none is {wanted}"
        )
    if APPLICATION_NETWORK in service_networks(service):
        offences.append(f"node-exporter is attached to {APPLICATION_NETWORK}")
    return offences


def rule_offences(path: Path) -> list[str]:
    """Every way the four backup-age rules fail to say what the requirement
    says."""
    rules = alerting_rules(compose_document(path))
    offences = []
    missing = [name for name in FOUR_ALERTS if name not in rules]
    if missing:
        return [f"no rule named {name}" for name in missing]

    stale = _expr(rules[BACKUP_STALE])
    if not (_word(TIMESTAMP_METRIC).search(stale) and _word(MAX_AGE_METRIC).search(stale)):
        offences.append(f"{BACKUP_STALE} does not read both contract series: {stale!r}")
    if "time()" not in stale or ">" not in stale:
        offences.append(f"{BACKUP_STALE} does not compare age with the maximum: {stale!r}")
    if not {"store", "kind"} <= _matching_labels(stale, "on"):
        offences.append(f"{BACKUP_STALE} does not match the pair on (store, kind): {stale!r}")

    unbounded = _expr(rules[BACKUP_AGE_UNBOUNDED])
    if not (
        _word(TIMESTAMP_METRIC).search(unbounded)
        and _word(MAX_AGE_METRIC).search(unbounded)
        and re.search(r"\bunless\b", unbounded)
    ):
        offences.append(
            f"{BACKUP_AGE_UNBOUNDED} does not report a timestamp with no maximum: {unbounded!r}"
        )
    if not {"store", "kind"} <= _matching_labels(unbounded, "on"):
        offences.append(f"{BACKUP_AGE_UNBOUNDED} does not match on (store, kind): {unbounded!r}")

    for name in (BACKUP_STALE, BACKUP_AGE_UNBOUNDED):
        if not annotations_name_store_and_kind(rules[name]):
            offences.append(f"{name}'s annotations do not name the store and kind")

    unreadable = _expr(rules[TEXTFILE_UNREADABLE])
    if not _word(SCRAPE_ERROR_METRIC).search(unreadable):
        offences.append(f"{TEXTFILE_UNREADABLE} does not read {SCRAPE_ERROR_METRIC}: {unreadable!r}")

    gathering = _expr(rules[GATHERING_ERRORS])
    if not (
        _word(HANDLER_ERRORS_METRIC).search(gathering)
        and re.search(r"""cause\s*=\s*["']gathering["']""", gathering)
    ):
        offences.append(
            f"{GATHERING_ERRORS} does not read gathering errors of the handler: {gathering!r}"
        )
    return offences


def rules_without_a_duration(path: Path) -> list[str]:
    rules = alerting_rules(compose_document(path))
    return [
        name
        for name in (BACKUP_STALE, BACKUP_AGE_UNBOUNDED, TEXTFILE_UNREADABLE)
        if name in rules and not str(rules[name].get("for", "")).strip()
    ]


def _route_names_alert(route: dict, name: str) -> bool:
    rendered = yaml.safe_dump(
        {key: route.get(key) for key in ("matchers", "match", "match_re") if key in route}
    )
    return name in rendered


def routing_offences(path: Path) -> list[str]:
    """Every one of the four alerts a child route sends somewhere other than
    the root receiver every other rule reaches."""
    document = yaml.safe_load(config_content(compose_document(path), ALERTMANAGER_CONFIG)) or {}
    route = document.get("route") or {}
    root_receiver = route.get("receiver")
    receivers = [r.get("name") for r in document.get("receivers") or [] if isinstance(r, dict)]
    if not root_receiver or root_receiver not in receivers:
        return [f"the root route's receiver {root_receiver!r} is not declared"]
    offences = []
    stack = list(route.get("routes") or [])
    while stack:
        child = stack.pop()
        if not isinstance(child, dict):
            continue
        stack.extend(child.get("routes") or [])
        for name in FOUR_ALERTS:
            receiver = child.get("receiver")
            if _route_names_alert(child, name) and receiver not in (None, root_receiver):
                offences.append(f"{name} is routed to {receiver}")
    return offences


class TestABackedUpStoresBackupAgeIsAlertedOn(unittest.TestCase):
    """*A Backed-Up Store's Backup Age Is Alerted On*.

    RED until tasks.md 3.1 and 3.2 land."""

    def test_node_exporter_collects_the_application_metrics_directories(self) -> None:
        """SPECIFIED -- "Collection SHALL be by node-exporter's textfile
        collector, reading `*.prom` files from every
        `/mnt/main/applications/<application>/metrics` directory through
        node-exporter's existing read-only mount of the host's root filesystem.
        No monitoring service SHALL be attached to a network an application
        joins". Scenario "Collection attaches no monitoring service to the
        application network". The flag's spelling is DERIVED (design.md
        decision 2); its value is derived from the committed root mount."""
        self.assertEqual([], collection_offences(ROOT / PLATFORM_COMPOSE))

    def test_the_four_rules_say_what_the_requirement_says(self) -> None:
        """SPECIFIED -- the four alerts the requirement lists, and scenarios "An
        overdue backup raises an alert" and "A timestamp without a maximum age
        raises an alert" ("naming that store and kind"), "An unreadable
        metrics file raises an alert", "Two files emitting the same series
        raise an alert". DERIVED: the rule names, matching `on(store, kind)`,
        and `cause="gathering"` (design.md decision 2)."""
        self.assertEqual([], rule_offences(ROOT / PLATFORM_COMPOSE))

    def test_three_rules_wait_before_firing(self) -> None:
        """DERIVED -- design.md decision 2 gives `for:` 10m, 1h and 15m; the
        Migration Plan's converge window rests on the 15 minutes."""
        rules = alerting_rules(compose_document(ROOT / PLATFORM_COMPOSE))
        self.assertTrue(all(name in rules for name in FOUR_ALERTS), sorted(rules))
        self.assertEqual([], rules_without_a_duration(ROOT / PLATFORM_COMPOSE))

    def test_the_rules_are_routed_like_every_other_rule(self) -> None:
        """SPECIFIED -- "Alerts, routed like every other rule". Partial: what is
        read is that no child route diverts one of the four from the root
        receiver; that the root receiver delivers to Slack is not re-read."""
        self.assertEqual([], routing_offences(ROOT / PLATFORM_COMPOSE))


class TestThePlatformChecksDiscriminate(unittest.TestCase):
    """Fixture-driven discriminators for section 3."""

    GOOD_RULES = {
        "groups": [
            {
                "name": "backups",
                "rules": [
                    {
                        "alert": BACKUP_STALE,
                        "expr": f"time() - {TIMESTAMP_METRIC} > on(store, kind) {MAX_AGE_METRIC}",
                        "for": "10m",
                        "annotations": {"summary": "{{ $labels.store }} {{ $labels.kind }} overdue"},
                    },
                    {
                        "alert": BACKUP_AGE_UNBOUNDED,
                        "expr": f"{TIMESTAMP_METRIC} unless on(store, kind) {MAX_AGE_METRIC}",
                        "for": "1h",
                        "annotations": {"description": "{{ $labels.store }}/{{ $labels.kind }}"},
                    },
                    {"alert": TEXTFILE_UNREADABLE, "expr": f"{SCRAPE_ERROR_METRIC} == 1", "for": "15m"},
                    {
                        "alert": GATHERING_ERRORS,
                        "expr": f'increase({HANDLER_ERRORS_METRIC}{{job="node-exporter", cause="gathering"}}[15m]) > 0',
                    },
                ],
            }
        ]
    }

    def _compose(
        self,
        *,
        command: object = ("--path.rootfs=/host/root", "--collector.textfile.directory=/host/root/mnt/main/applications/*/metrics"),
        volumes: object = ("/:/host/root:ro", "/proc:/host/proc:ro"),
        networks: object = ("platform_monitoring",),
        rules: dict | None = None,
        routes: list | None = None,
    ) -> Path:
        alertmanager = {
            "route": {"receiver": "slack", "routes": routes or [
                {"matchers": ['alertname="Watchdog"'], "receiver": "deadmansswitch"}
            ]},
            "receivers": [{"name": "slack"}, {"name": "deadmansswitch"}],
        }
        document = {
            "services": {
                "node-exporter": {
                    "image": "prom/node-exporter:v1.12.1",
                    "command": list(command) if not isinstance(command, str) else command,
                    "volumes": list(volumes),
                    "networks": list(networks),
                }
            },
            "configs": {
                RULES_CONFIG: {"content": yaml.safe_dump(rules if rules is not None else self.GOOD_RULES)},
                ALERTMANAGER_CONFIG: {"content": yaml.safe_dump(alertmanager)},
            },
        }
        directory = Path(tempfile.mkdtemp(prefix="durable-store-compose-"))
        self.addCleanup(shutil.rmtree, directory, ignore_errors=True)
        path = directory / "docker-compose.yml"
        path.write_text(yaml.safe_dump(document, sort_keys=False), encoding="utf-8")
        return path

    def _rules_with(self, name: str, **changes: object) -> dict:
        rules = yaml.safe_load(yaml.safe_dump(self.GOOD_RULES))
        for rule in rules["groups"][0]["rules"]:
            if rule["alert"] == name:
                rule.update(changes)
                for key, value in list(rule.items()):
                    if value is None:
                        del rule[key]
        return rules

    def test_a_stack_satisfying_every_property_is_accepted(self) -> None:
        path = self._compose()
        self.assertEqual([], collection_offences(path))
        self.assertEqual([], rule_offences(path))
        self.assertEqual([], rules_without_a_duration(path))
        self.assertEqual([], routing_offences(path))

    def test_a_string_command_is_read(self) -> None:
        path = self._compose(command="--collector.textfile.directory=/host/root/mnt/main/applications/*/metrics")
        self.assertEqual([], collection_offences(path))

    def test_no_textfile_flag_is_reported(self) -> None:
        self.assertNotEqual([], collection_offences(self._compose(command=["--path.rootfs=/host/root"])))

    def test_a_flag_outside_the_root_mount_is_reported(self) -> None:
        path = self._compose(command=["--collector.textfile.directory=/mnt/main/applications/*/metrics"])
        self.assertNotEqual([], collection_offences(path))

    def test_a_direct_mount_of_the_volume_is_reported(self) -> None:
        path = self._compose(volumes=["/:/host/root:ro", "/mnt/main/applications:/apps:ro"])
        self.assertNotEqual([], collection_offences(path))

    def test_a_writable_root_mount_is_reported(self) -> None:
        self.assertNotEqual([], collection_offences(self._compose(volumes=["/:/host/root"])))

    def test_the_application_network_is_reported(self) -> None:
        path = self._compose(networks=["platform_monitoring", APPLICATION_NETWORK])
        self.assertTrue(any(APPLICATION_NETWORK in o for o in collection_offences(path)))

    def test_a_missing_rule_is_reported(self) -> None:
        rules = yaml.safe_load(yaml.safe_dump(self.GOOD_RULES))
        rules["groups"][0]["rules"] = rules["groups"][0]["rules"][1:]
        self.assertEqual([f"no rule named {BACKUP_STALE}"], rule_offences(self._compose(rules=rules)))

    def test_a_staleness_rule_without_the_maximum_is_reported(self) -> None:
        rules = self._rules_with(BACKUP_STALE, expr=f"time() - {TIMESTAMP_METRIC} > 86400")
        self.assertNotEqual([], rule_offences(self._compose(rules=rules)))

    def test_a_staleness_rule_matching_on_store_alone_is_reported(self) -> None:
        rules = self._rules_with(
            BACKUP_STALE, expr=f"time() - {TIMESTAMP_METRIC} > on(store) {MAX_AGE_METRIC}"
        )
        self.assertNotEqual([], rule_offences(self._compose(rules=rules)))

    def test_an_unbounded_rule_without_unless_is_reported(self) -> None:
        rules = self._rules_with(
            BACKUP_AGE_UNBOUNDED, expr=f"{TIMESTAMP_METRIC} and on(store, kind) {MAX_AGE_METRIC}"
        )
        self.assertNotEqual([], rule_offences(self._compose(rules=rules)))

    def test_annotations_not_naming_the_kind_are_reported(self) -> None:
        rules = self._rules_with(BACKUP_STALE, annotations={"summary": "{{ $labels.store }} overdue"})
        offences = rule_offences(self._compose(rules=rules))
        self.assertTrue(any("store and kind" in o for o in offences), offences)

    def test_a_gathering_rule_without_the_cause_is_reported(self) -> None:
        rules = self._rules_with(GATHERING_ERRORS, expr=f"increase({HANDLER_ERRORS_METRIC}[15m]) > 0")
        self.assertNotEqual([], rule_offences(self._compose(rules=rules)))

    def test_an_unreadable_rule_on_another_metric_is_reported(self) -> None:
        rules = self._rules_with(TEXTFILE_UNREADABLE, expr="node_scrape_collector_success == 0")
        self.assertNotEqual([], rule_offences(self._compose(rules=rules)))

    def test_a_rule_with_no_duration_is_reported(self) -> None:
        rules = self._rules_with(TEXTFILE_UNREADABLE, **{"for": None})
        self.assertEqual([TEXTFILE_UNREADABLE], rules_without_a_duration(self._compose(rules=rules)))

    def test_a_diverting_route_is_reported(self) -> None:
        path = self._compose(routes=[{"matchers": [f'alertname="{BACKUP_STALE}"'], "receiver": "deadmansswitch"}])
        self.assertEqual([f"{BACKUP_STALE} is routed to deadmansswitch"], routing_offences(path))

    def test_a_stack_with_no_rules_fails_rather_than_passing(self) -> None:
        with self.assertRaises(AssertionError):
            rule_offences(self._compose(rules={"groups": []}))


# --------------------------------------------------------------------------
# Section 4. Documents (DERIVED -- tasks.md 4.1 to 4.3; no scenario names a
# document)
# --------------------------------------------------------------------------


def onboarding_offences(text: str) -> list[str]:
    offences = []
    if RETIRED_ONBOARDING_SENTENCE in " ".join(text.lower().split()):
        offences.append(f"still says {RETIRED_ONBOARDING_SENTENCE!r}")
    if "basis-api" not in text:
        offences.append("does not name the admitted store's application, basis-api")
    if HOST_SUBDIRS_VARIABLE not in text:
        offences.append(f"does not say an application declares its directories in {HOST_SUBDIRS_VARIABLE}")
    for metric in (TIMESTAMP_METRIC, MAX_AGE_METRIC):
        if metric not in text:
            offences.append(f"does not name {metric}")
    return offences


def runbook_offences(text: str) -> list[str]:
    offences = []
    if BACKUP_STALE not in text:
        offences.append(f"does not name {BACKUP_STALE} among the expected alarms")
    if "basis-api" not in text:
        offences.append("does not say a lost volume means restoring basis-api's store")
    return offences


def backlog_offences(text: str) -> list[str]:
    return [] if BACKLOG_ENTRY in text else [f"carries no entry {BACKLOG_ENTRY!r}"]


class TestTheDocumentsRecordTheStore(unittest.TestCase):
    """DERIVED throughout -- *No Store on This Host Holds Data Requiring
    Backup* is what these documents restate, but its scenarios name no
    document. Each check traces to the tasks.md item named. RED until tasks.md
    4.1 to 4.3 land."""

    def test_the_onboarding_guide_records_the_admitted_store(self) -> None:
        """DERIVED -- tasks.md 4.1: replace "no application has cleared that
        bar" with the admitted store, and say how an application declares its
        directories and publishes its backup metrics."""
        self.assertEqual([], onboarding_offences(read_required(ROOT / ONBOARDING)))

    def test_the_rebuild_runbook_names_the_production_store(self) -> None:
        """DERIVED -- tasks.md 4.2: `BackupStale` joins the expected alarms, and
        a lost volume means a restore of `basis-api`'s store."""
        self.assertEqual([], runbook_offences(read_required(ROOT / RUNBOOK)))

    def test_the_backlog_carries_the_follow_up(self) -> None:
        """DERIVED -- tasks.md 4.3 and proposal.md's "Backlog" item."""
        self.assertEqual([], backlog_offences(read_required(ROOT / BACKLOG)))


class TestTheDocumentChecksDiscriminate(unittest.TestCase):
    GOOD_ONBOARDING = (
        "## 3.1\nNo other application has cleared that bar beyond `basis-api`.\n"
        f"Declare `{HOST_SUBDIRS_VARIABLE}`; publish `{TIMESTAMP_METRIC}` and `{MAX_AGE_METRIC}`.\n"
    )

    def test_good_documents_are_accepted(self) -> None:
        self.assertEqual([], onboarding_offences(self.GOOD_ONBOARDING))
        self.assertEqual([], runbook_offences("expect BackupStale; restore basis-api's store"))
        self.assertEqual([], backlog_offences(f"### `{BACKLOG_ENTRY}`\n"))

    def test_the_retired_sentence_is_reported_across_a_line_break(self) -> None:
        text = self.GOOD_ONBOARDING + "So far no application\nhas cleared that bar.\n"
        self.assertNotEqual([], onboarding_offences(text))

    def test_an_onboarding_guide_without_the_contract_is_reported(self) -> None:
        self.assertNotEqual([], onboarding_offences("basis-api only\n"))

    def test_a_runbook_without_the_alarm_is_reported(self) -> None:
        self.assertNotEqual([], runbook_offences("restore basis-api's store\n"))

    def test_a_backlog_without_the_entry_is_reported(self) -> None:
        self.assertNotEqual([], backlog_offences("### `finish-something-else`\n"))


if __name__ == "__main__":
    unittest.main()
