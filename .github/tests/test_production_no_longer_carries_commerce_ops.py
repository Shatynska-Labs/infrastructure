"""Static assertions that `main-production` no longer carries `commerce-ops`.

Derived from the delta specification of the OpenSpec change
`remove-commerce-ops-from-production` -- one MODIFIED requirement, *No Store on
This Host Holds Data Requiring Backup* (`openspec/specs/iac-safety-hardening/spec.md`)
-- by an author other than whoever implements the change, and before any of
its implementation existed. The delta's path is not written here: a change's
artifacts move when it is archived, so this repository's citation convention is
to name the change and the artifact in prose. See that change's `test-plan.md`
for the scenario-to-test mapping, the baseline, the scenarios left uncovered and
why, and the obsolete-test candidates.

What the delta changes, and what is asserted here
-------------------------------------------------
The requirement loses its stated divergence -- `commerce-ops`'s own PostgreSQL
on the production host, recorded as unmet -- and its scenario *The stated
divergence is not a precedent* stops naming an application. The requirement
then records no unmet store at all, and a store is admitted only by one of its
reasons or by a rehearsed backup.

The requirement's own text changes in `openspec/specs/` only when the change is
archived, after its verification has run, so nothing here reads it: a check
over it would be red through the whole of `apply`. What this module reads
instead are the committed files that restated the divergence, or authorised the
application on the production host, as present facts. A document still saying
the production host carries `commerce-ops`'s own PostgreSQL contradicts a
requirement that records no such store, and is exactly the "another
application does" a later proposal would cite as precedent. Which sentences
those are is that change's `design.md` (Decision 5) and `proposal.md`, so every
assertion below is **DERIVED**; none traces to SHALL text alone.

What situation these tests are in
---------------------------------
Static reads of committed files. Nothing here executes the behaviour asserted,
so a green result reports only that the files were read and carry the shape
asserted. Most of the checks over the real tree are red at authoring, because
the files still carry what the change removes; that red run is recorded in the
test plan as what establishes they discriminate on real content. Every detector
is also run over material this module supplies, in the `...DetectorFires`
classes at the foot, so a later edit that stops a detector matching fails a
test rather than passing silently.

What this deliberately does not attempt
---------------------------------------
Whether the hand clean-up on the host happened (sudoers files, `/opt/commerce-ops`,
the two `authorized_keys` lines). That is a read of a live host, which this
suite may not make; it is the operator's pasted output, recorded by that
change's tasks.

Sentences that record what happened, or use `commerce-ops` as an example name,
are kept by that change (its proposal's Non-Goals), so the detectors below match
a line only where it pairs the application with what makes it a present claim
about production -- never the bare name.

Arrangement
-----------
Every helper here is declared in this module. This suite has no shared test
arrangement (AGENTS.md, *Testing*), and a derivation does not import from
another test module, `test_ci_configuration.py` included.

Runner
------
    python3 -m unittest discover --start-directory .github/tests

    # or one test:
    python3 -m unittest \\
        test_production_no_longer_carries_commerce_ops.TestTheProductionHostVarsNoLongerAuthoriseCommerceOps.test_no_deploy_apps_entry_is_named_commerce_ops

Run from the repository root.
"""

from __future__ import annotations

import os
import shutil
import tempfile
import unittest
from pathlib import Path

import yaml

# --------------------------------------------------------------------------
# Local arrangement: repository access
# --------------------------------------------------------------------------


def _repo_root() -> Path:
    """The repository root, found the way every module in this suite finds it:
    the nearest ancestor carrying `openspec/config.yaml`, or `REPO_ROOT`."""
    override = os.environ.get("REPO_ROOT")
    if override:
        return Path(override).resolve()
    here = Path(__file__).resolve()
    for candidate in (here, *here.parents):
        if (candidate / "openspec" / "config.yaml").is_file():
            return candidate
    raise RuntimeError(
        "could not locate the repository root: no ancestor of "
        f"{here} contains openspec/config.yaml, and REPO_ROOT is unset"
    )


ROOT = _repo_root()

APPLICATION = "commerce-ops"

PRODUCTION_HOST_VARS = ROOT / "ansible" / "inventory" / "host_vars" / "main-production.yml"
RUNBOOK = ROOT / "docs" / "runbook-rebuild.md"
ONBOARDING_GUIDE = ROOT / "docs" / "onboard-an-application.md"
BOOTSTRAP_GUIDE = ROOT / "docs" / "bootstrap-a-new-host.md"
PLATFORM_README = ROOT / "platform" / "README.md"

# DERIVED (design.md Decision 2): the applications whose deploy and probe lines
# the production host keeps -- "a deploy line and a probe line for each of
# `platform`, `shatynskyj`, `portfolio` and `basis-api`".
APPLICATIONS_PRODUCTION_KEEPS = ("platform", "shatynskyj", "portfolio", "basis-api")

# DERIVED (design.md Decision 5): the two identifiers `platform/README.md`
# names as the production host's, and not the shared instance's.
PRODUCTION_STORE_IDENTIFIERS = ("commerce-ops-postgres-1", "commerce_ops_pgdata")


def _shown(path: Path) -> str:
    try:
        return str(path.relative_to(ROOT))
    except ValueError:
        return str(path)


def read_text(path: Path) -> str:
    """A file's text, failing the calling test where it is absent or empty.

    An absent or empty file would let every absence check below pass having
    read nothing, so both are failures rather than skips."""
    if not path.is_file():
        raise AssertionError(f"{_shown(path)} does not exist")
    text = path.read_text(encoding="utf-8")
    if not text.strip():
        raise AssertionError(
            f"{_shown(path)} is empty, so a check that it names "
            "nothing stale would pass having read nothing"
        )
    return text


class UnreadableHostVars(AssertionError):
    """A host vars file that does not parse into a mapping."""


class _VaultTolerantLoader(yaml.SafeLoader):
    """`yaml.SafeLoader`, accepting `!vault` and refusing any other tag.

    An inventory file may carry vaulted values, which `yaml.safe_load` refuses.
    A catch-all for every unknown tag would map a mistyped one to `None`, and
    `deploy_apps` read out of that is an absent list -- the very absence one
    check below asserts -- so only `!vault` is accepted."""


def _vault(loader: yaml.SafeLoader, node: yaml.Node) -> str:
    return "<vaulted>"


_VaultTolerantLoader.add_constructor("!vault", _vault)


def host_vars(text: str) -> dict:
    try:
        document = yaml.load(text, Loader=_VaultTolerantLoader)  # noqa: S506
    except yaml.YAMLError as error:
        raise UnreadableHostVars(f"the host vars do not parse: {error}") from error
    if not isinstance(document, dict):
        raise UnreadableHostVars(
            f"the host vars parse to {type(document).__name__}, not a mapping"
        )
    return document


def deploy_app_names(document: dict) -> list[str]:
    """Every `deploy_apps` entry's `name`, failing where the list is absent.

    An absent or empty list would make "no entry is named `commerce-ops`" true
    of a file that authorises nothing, so it is refused rather than read as a
    pass."""
    entries = document.get("deploy_apps")
    if not isinstance(entries, list) or not entries:
        raise UnreadableHostVars("the host vars declare no non-empty `deploy_apps` list")
    names = []
    for entry in entries:
        if not isinstance(entry, dict) or not isinstance(entry.get("name"), str):
            raise UnreadableHostVars(f"a `deploy_apps` entry carries no name: {entry!r}")
        names.append(entry["name"])
    return names


# --------------------------------------------------------------------------
# Local arrangement: the line detector
# --------------------------------------------------------------------------


def lines_naming(text: str, *groups: tuple[str, ...]) -> list[str]:
    """Each line naming `commerce-ops` and, for every group, one of its terms.

    Case-insensitive, and fenced lines are read too: an example command is as
    much a present claim as prose. Prose in this repository is not hard-wrapped,
    so a line is a paragraph and a co-occurrence on one line is a co-occurrence
    in one statement."""
    found = []
    for number, raw in enumerate(text.splitlines(), start=1):
        lowered = raw.lower()
        if APPLICATION not in lowered:
            continue
        if all(any(term.lower() in lowered for term in group) for group in groups):
            found.append(f"{number}: {raw.strip()}")
    return found


# The pairings that make a line naming the application a present claim about
# production, one per document, each DERIVED from design.md Decision 5.

# The runbook's production warning ("On `main-production` there is a third"),
# its phase 14 sentence ("`main-production` carries `commerce-ops`"), its phase
# 15 aside about the application's `Deploy` trigger and its `/health` example --
# the last two "rewritten without naming an application".
RUNBOOK_PAIRINGS: tuple[tuple[str, ...], ...] = (("main-production", "/health", "trigger"),)

# The bootstrap guide's statement that both `host_vars` files carry a
# `commerce-ops` entry.
BOOTSTRAP_PAIRINGS: tuple[tuple[str, ...], ...] = (("host_vars", "main-production"),)

# The onboarding guide's comment-convention paragraph citing
# `commerce-ops-deploy` in `main-production.yml`.
ONBOARDING_HOST_VARS_PAIRINGS: tuple[tuple[str, ...], ...] = (("main-production.yml",),)

# The onboarding guide's production-divergence paragraph: the application, the
# production host, and the store or the divergence. The guide keeps
# `commerce-ops` as its worked example (proposal.md, Non-Goals), so the bare
# pairing with the production host is deliberately not enough. "production"
# rather than "main-production": the paragraph says "the **production** host",
# and a first version of this pairing keyed on the host name passed over it at
# authoring -- the alarm that a static check meets nothing.
ONBOARDING_DIVERGENCE_PAIRINGS: tuple[tuple[str, ...], ...] = (
    ("production",),
    ("postgres", "database", "divergen", "backup"),
)


def platform_readme_offences(text: str) -> list[str]:
    """Lines of `platform/README.md` still describing the production host's
    `commerce-ops` store, or a production database reserved for a cutover."""
    offences = []
    for number, raw in enumerate(text.splitlines(), start=1):
        lowered = raw.lower()
        named = [ident for ident in PRODUCTION_STORE_IDENTIFIERS if ident in lowered]
        if named:
            offences.append(f"{number}: names {', '.join(named)}: {raw.strip()}")
        elif "cutover" in lowered and "production" in lowered:
            offences.append(f"{number}: a production database for a cutover: {raw.strip()}")
    return offences


# --------------------------------------------------------------------------
# The production host's own configuration
# --------------------------------------------------------------------------


class TestTheProductionHostVarsNoLongerAuthoriseCommerceOps(unittest.TestCase):
    """DERIVED -- proposal.md, What Changes: "The `commerce-ops` entry is
    deleted from `ansible/inventory/host_vars/main-production.yml`, with the
    comments that describe it." An entry the requirement no longer records a
    store for, kept authorised on the host, is the authorisation a later
    application would cite.

    RED AT AUTHORING: the entry and its comments are still there.
    """

    def test_no_deploy_apps_entry_is_named_commerce_ops(self) -> None:
        names = deploy_app_names(host_vars(read_text(PRODUCTION_HOST_VARS)))
        self.assertNotIn(
            APPLICATION,
            names,
            f"{PRODUCTION_HOST_VARS.relative_to(ROOT)} still authorises "
            f"`{APPLICATION}` in `deploy_apps` ({names}); the change deletes that entry",
        )

    def test_the_file_names_commerce_ops_nowhere(self) -> None:
        """DERIVED -- design.md Decision 5's last item: the comments naming
        `commerce-ops`, comparing its keys with `main-staging.yml`'s, or counting
        "the two deploy keys here" are rewritten. Comments are read too."""
        offences = lines_naming(read_text(PRODUCTION_HOST_VARS))
        self.assertEqual(
            [],
            offences,
            f"{PRODUCTION_HOST_VARS.relative_to(ROOT)} still names `{APPLICATION}`",
        )

    def test_every_other_application_keeps_its_entry(self) -> None:
        """DERIVED -- design.md Decision 2 expects the host to keep a deploy and
        a probe line for each of four applications after the clean-up; deleting
        more than the one entry would revoke them at the next converge's render.
        Green at authoring; its discriminator is in the detector class below."""
        names = deploy_app_names(host_vars(read_text(PRODUCTION_HOST_VARS)))
        missing = [app for app in APPLICATIONS_PRODUCTION_KEEPS if app not in names]
        self.assertEqual(
            [],
            missing,
            f"{PRODUCTION_HOST_VARS.relative_to(ROOT)} no longer authorises {missing}",
        )


# --------------------------------------------------------------------------
# The documents that restated the divergence
# --------------------------------------------------------------------------


class TestNoDocumentStillPlacesCommerceOpsOnProduction(unittest.TestCase):
    """DERIVED -- design.md Decision 5: "A sentence stating a present fact about
    `commerce-ops` on production changes." With the divergence deleted from
    *No Store on This Host Holds Data Requiring Backup*, each of these restates
    a store the requirement no longer records, and *A Host's Rebuild Procedure
    Is Recorded, and Its Rehearsal State With It*
    (`openspec/specs/iac-server-lifecycle/spec.md`) derives the runbook's
    statement of what a rebuild loses from that requirement.

    RED AT AUTHORING over every document below except where the stale sentence
    happens not to match its pairing; the test plan records which.
    """

    def test_the_runbook_does_not_place_commerce_ops_on_production(self) -> None:
        offences = lines_naming(read_text(RUNBOOK), *RUNBOOK_PAIRINGS)
        self.assertEqual(
            [],
            offences,
            f"{RUNBOOK.relative_to(ROOT)} still states `{APPLICATION}` on the "
            "production host, or names it in the phase 15 aside or the `/health` "
            "example the change rewrites without naming an application",
        )

    def test_the_bootstrap_guide_does_not_say_host_vars_carry_commerce_ops(self) -> None:
        offences = lines_naming(read_text(BOOTSTRAP_GUIDE), *BOOTSTRAP_PAIRINGS)
        self.assertEqual(
            [],
            offences,
            f"{BOOTSTRAP_GUIDE.relative_to(ROOT)} still says a `host_vars` file "
            f"carries a `{APPLICATION}` entry; neither does after this change",
        )

    def test_the_onboarding_guide_cites_no_commerce_ops_entry_in_production(self) -> None:
        offences = lines_naming(read_text(ONBOARDING_GUIDE), *ONBOARDING_HOST_VARS_PAIRINGS)
        self.assertEqual(
            [],
            offences,
            f"{ONBOARDING_GUIDE.relative_to(ROOT)} still cites a `{APPLICATION}` "
            "entry in `main-production.yml` as a committed example",
        )

    def test_the_onboarding_guide_states_no_production_divergence(self) -> None:
        offences = lines_naming(read_text(ONBOARDING_GUIDE), *ONBOARDING_DIVERGENCE_PAIRINGS)
        self.assertEqual(
            [],
            offences,
            f"{ONBOARDING_GUIDE.relative_to(ROOT)} still describes `{APPLICATION}`'s "
            "store on the production host",
        )

    def test_the_platform_readme_describes_no_production_commerce_ops_store(self) -> None:
        offences = platform_readme_offences(read_text(PLATFORM_README))
        self.assertEqual(
            [],
            offences,
            f"{PLATFORM_README.relative_to(ROOT)} still describes `{APPLICATION}`'s "
            "production store, or a production database reserved for a cutover",
        )


# --------------------------------------------------------------------------
# Fixture-driven discriminators: every detector above, over supplied material
# --------------------------------------------------------------------------


class TestTheHostVarsReadersFire(unittest.TestCase):
    WITH = (
        "---\n"
        "# commerce-ops-deploy: the two deploy keys here\n"
        "deploy_apps:\n"
        "  - name: platform\n    public_key: ssh-ed25519 AAAA\n"
        "  - name: commerce-ops\n    public_key: ssh-ed25519 BBBB\n"
        "ghcr_pull_token: !vault |\n  $ANSIBLE_VAULT;1.2;AES256;production\n  3333\n"
    )
    WITHOUT = (
        "---\n"
        "deploy_apps:\n"
        "  - name: platform\n    public_key: ssh-ed25519 AAAA\n"
        "  - name: shatynskyj\n    public_key: ssh-ed25519 CCCC\n"
    )

    def test_an_entry_named_commerce_ops_is_found(self) -> None:
        self.assertIn(APPLICATION, deploy_app_names(host_vars(self.WITH)))

    def test_a_file_without_it_does_not_name_it(self) -> None:
        self.assertNotIn(APPLICATION, deploy_app_names(host_vars(self.WITHOUT)))
        self.assertEqual([], lines_naming(self.WITHOUT))

    def test_a_comment_naming_it_is_found(self) -> None:
        self.assertEqual(2, len(lines_naming(self.WITH)))

    def test_an_absent_deploy_apps_list_is_refused_not_passed(self) -> None:
        with self.assertRaises(UnreadableHostVars):
            deploy_app_names(host_vars("---\nother: 1\n"))
        with self.assertRaises(UnreadableHostVars):
            deploy_app_names(host_vars("---\ndeploy_apps: []\n"))

    def test_an_unknown_tag_is_refused_rather_than_read_as_empty(self) -> None:
        with self.assertRaises(UnreadableHostVars):
            host_vars("deploy_apps: !something\n  - name: platform\n")

    def test_an_application_dropped_with_it_is_reported(self) -> None:
        names = deploy_app_names(host_vars(self.WITHOUT))
        missing = [app for app in APPLICATIONS_PRODUCTION_KEEPS if app not in names]
        self.assertEqual(["portfolio", "basis-api"], missing)


class TestTheDocumentDetectorsFire(unittest.TestCase):
    def test_the_runbook_warning_is_reported(self) -> None:
        text = (
            "On `main-production` there is a third: commerce-ops's own "
            "PostgreSQL is lost outright.\n"
        )
        self.assertEqual(1, len(lines_naming(text, *RUNBOOK_PAIRINGS)))

    def test_the_runbook_health_example_is_reported(self) -> None:
        text = "```sh\ncurl -fsS https://commerce-ops.example.test/health\n```\n"
        self.assertEqual(1, len(lines_naming(text, *RUNBOOK_PAIRINGS)))

    def test_the_runbook_trigger_aside_is_reported(self) -> None:
        text = "Re-run commerce-ops's `Deploy` workflow; its trigger is a push.\n"
        self.assertEqual(1, len(lines_naming(text, *RUNBOOK_PAIRINGS)))

    def test_a_staging_history_sentence_is_not_reported(self) -> None:
        text = "`remove-commerce-ops-from-staging` took commerce-ops off `main-staging`.\n"
        self.assertEqual([], lines_naming(text, *RUNBOOK_PAIRINGS))

    def test_a_rewritten_health_example_is_not_reported(self) -> None:
        text = "curl -fsS https://<application>.<server>.<domain>/health\n"
        self.assertEqual([], lines_naming(text, *RUNBOOK_PAIRINGS))

    def test_the_bootstrap_statement_is_reported(self) -> None:
        text = "Both `host_vars` files carry a `commerce-ops` entry.\n"
        self.assertEqual(1, len(lines_naming(text, *BOOTSTRAP_PAIRINGS)))

    def test_a_bootstrap_line_naming_only_the_application_is_not_reported(self) -> None:
        text = "An application such as `commerce-ops` deploys from its own repository.\n"
        self.assertEqual([], lines_naming(text, *BOOTSTRAP_PAIRINGS))

    def test_the_onboarding_comment_convention_citation_is_reported(self) -> None:
        text = "See the `commerce-ops-deploy` comment in `main-production.yml`.\n"
        self.assertEqual(1, len(lines_naming(text, *ONBOARDING_HOST_VARS_PAIRINGS)))

    def test_the_onboarding_divergence_is_reported(self) -> None:
        text = (
            "On `main-production`, commerce-ops keeps its own PostgreSQL, a "
            "divergence no backup covers.\n"
        )
        self.assertEqual(1, len(lines_naming(text, *ONBOARDING_DIVERGENCE_PAIRINGS)))

    def test_the_onboarding_worked_example_is_not_reported(self) -> None:
        text = "This guide follows `commerce-ops` from its first deploy to `main-production`.\n"
        self.assertEqual([], lines_naming(text, *ONBOARDING_DIVERGENCE_PAIRINGS))

    def test_the_platform_readme_identifiers_are_reported(self) -> None:
        text = (
            "`commerce-ops-postgres-1` and `commerce-ops_commerce_ops_pgdata` on "
            "the production host are not this instance.\n"
        )
        self.assertEqual(1, len(platform_readme_offences(text)))

    def test_the_platform_readme_cutover_sentence_is_reported(self) -> None:
        text = "On production a database is reserved for the cutover.\n"
        self.assertEqual(1, len(platform_readme_offences(text)))

    def test_a_platform_readme_without_them_is_not_reported(self) -> None:
        text = "The shared instance keeps its data in `/mnt/main/postgres`.\n"
        self.assertEqual([], platform_readme_offences(text))

    def test_an_empty_document_is_refused_rather_than_read_as_clean(self) -> None:
        directory = Path(tempfile.mkdtemp(prefix="empty-document-"))
        self.addCleanup(shutil.rmtree, directory, ignore_errors=True)
        path = directory / "empty.md"
        path.write_text("\n", encoding="utf-8")
        with self.assertRaises(AssertionError):
            read_text(path)


if __name__ == "__main__":
    unittest.main()
