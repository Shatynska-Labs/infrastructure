"""Every role this repository owns is listed in `.ansible-lint`'s `mock_roles`.

Written for `docs/backlog.md`'s `assert-every-role-has-a-mock-roles-entry`,
taken as a fix.

ansible-lint does not resolve a role referenced by name through
`ansible/ansible.cfg`'s `roles_path`, so `.ansible-lint` hand-lists every role
under `mock_roles`. A role added under `ansible/roles/` without an entry fails
ansible-lint twice -- in `ansible/playbooks/host-baseline.yml` and in the role's
own `converge.yml` -- with a "role not found" that names a search path, which
sends the time to the wrong file. This module moves that failure here, naming
the file to edit.

The roles are this repository's own, by `role_names()`: installed Galaxy content
is excluded by the rule that function derives from `ansible/requirements.yml`,
and `.ansible-lint` already excludes that content from linting.

Runner:

    python3 -m unittest discover --start-directory .github/tests
"""

from __future__ import annotations

import unittest
from pathlib import Path

from test_ci_configuration import ROOT, load_yaml, role_names

ANSIBLE_LINT_CONFIG = ROOT / ".ansible-lint"


def mock_roles(path: Path = ANSIBLE_LINT_CONFIG) -> set[str]:
    """The role names `.ansible-lint` mocks."""
    return {str(name).strip() for name in load_yaml(path).get("mock_roles") or []}


class TestEveryRoleHasAMockRolesEntry(unittest.TestCase):
    """`docs/backlog.md`'s `assert-every-role-has-a-mock-roles-entry`, taken as a fix."""

    def test_the_repository_has_roles_to_check(self) -> None:
        """The vacuity guard: the assertion below passes over an empty role
        set, which is also what a broken enumeration looks like."""
        self.assertTrue(
            role_names(),
            "no role was found under ansible/roles/, so the mock_roles check "
            "would pass having read nothing",
        )

    def test_every_role_is_mocked(self) -> None:
        missing = sorted(role_names() - mock_roles())
        self.assertEqual(
            [],
            missing,
            f"these roles under ansible/roles/ have no `mock_roles` entry in "
            f".ansible-lint: {missing}. ansible-lint does not resolve roles "
            f"through ansible.cfg's roles_path, so without an entry it reports "
            f"each as \"role not found\" wherever it is referenced by name",
        )


if __name__ == "__main__":
    unittest.main()
