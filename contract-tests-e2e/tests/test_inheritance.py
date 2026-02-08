"""Inheritance query E2E tests.

Validates inherit queries against real pipeline output from the reference project.
Tests class extends, interface implements, and both up/down directions.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from decorators import contract_test
from helpers import collect_fqns


pytestmark = pytest.mark.inheritance


@contract_test(
    name="Inherit interface down shows implementors",
    description="Verifies inherit of EmailSenderInterface with direction=down shows EmailSender",
    category="inheritance",
)
def test_inherit_interface_down(cli):
    """Direction down on interface should show implementors."""
    result = cli(
        "inherit", "App\\Component\\EmailSenderInterface",
        "--direction", "down", "--depth", "1"
    )
    assert result["root"]["fqn"] == "App\\Component\\EmailSenderInterface"

    fqns = collect_fqns(result["tree"])
    assert any("EmailSender" in fqn and "Interface" not in fqn for fqn in fqns), (
        f"Expected EmailSender in implementors, got: {fqns}"
    )


@contract_test(
    name="Inherit abstract class down shows subclasses",
    description="Verifies inherit of AbstractOrderProcessor with direction=down shows StandardOrderProcessor",
    category="inheritance",
)
def test_inherit_abstract_down(cli):
    """Direction down on abstract class should show subclasses."""
    result = cli(
        "inherit", "App\\Service\\AbstractOrderProcessor",
        "--direction", "down", "--depth", "1"
    )
    assert result["root"]["fqn"] == "App\\Service\\AbstractOrderProcessor"
    assert result["direction"] == "down"

    fqns = collect_fqns(result["tree"])
    assert any("StandardOrderProcessor" in fqn for fqn in fqns), (
        f"Expected StandardOrderProcessor in children, got: {fqns}"
    )


@contract_test(
    name="Inherit direction up shows parents",
    description="Verifies inherit of StandardOrderProcessor with direction=up shows AbstractOrderProcessor",
    category="inheritance",
)
def test_inherit_direction_up(cli):
    """Direction up should show parent classes."""
    result = cli(
        "inherit", "App\\Service\\StandardOrderProcessor",
        "--direction", "up", "--depth", "1"
    )
    assert result["root"]["fqn"] == "App\\Service\\StandardOrderProcessor"
    assert result["direction"] == "up"

    fqns = collect_fqns(result["tree"])
    assert any("AbstractOrderProcessor" in fqn for fqn in fqns), (
        f"Expected AbstractOrderProcessor in parent chain, got: {fqns}"
    )
