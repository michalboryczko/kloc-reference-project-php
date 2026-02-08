"""Inherit command contract tests.

Validates inheritance tree: direction up (parents), direction down (children),
depth expansion, class/interface/trait filtering.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))
from src.decorators import contract_test
from src.output_validator import OutputValidator


@contract_test(
    name="Inherit direction up shows parents",
    description="Verifies that inherit of StandardOrderProcessor with direction=up shows AbstractOrderProcessor as parent",
    category="inherit",
)
@pytest.mark.inherit
def test_inherit_direction_up(cli: OutputValidator):
    """Direction up should show parent classes."""
    result = cli.json_output(
        "inherit", "App\\Service\\StandardOrderProcessor", "--direction", "up", "--depth", "1"
    )
    assert result["root"]["fqn"] == "App\\Service\\StandardOrderProcessor"
    assert result["direction"] == "up"

    fqns = _collect_fqns(result["tree"])
    assert any("AbstractOrderProcessor" in fqn for fqn in fqns), (
        f"Expected AbstractOrderProcessor in parent chain, got: {fqns}"
    )


@contract_test(
    name="Inherit direction down shows children",
    description="Verifies that inherit of AbstractOrderProcessor with direction=down shows StandardOrderProcessor",
    category="inherit",
)
@pytest.mark.inherit
def test_inherit_direction_down(cli: OutputValidator):
    """Direction down should show child classes."""
    result = cli.json_output(
        "inherit", "App\\Service\\AbstractOrderProcessor", "--direction", "down", "--depth", "1"
    )
    assert result["root"]["fqn"] == "App\\Service\\AbstractOrderProcessor"
    assert result["direction"] == "down"

    fqns = _collect_fqns(result["tree"])
    assert any("StandardOrderProcessor" in fqn for fqn in fqns), (
        f"Expected StandardOrderProcessor in children, got: {fqns}"
    )


@contract_test(
    name="Inherit interface implementors",
    description="Verifies that inherit of EmailSenderInterface with direction=down shows EmailSender as implementor",
    category="inherit",
)
@pytest.mark.inherit
def test_inherit_interface_down(cli: OutputValidator):
    """Direction down on interface should show implementors."""
    result = cli.json_output(
        "inherit", "App\\Component\\EmailSenderInterface", "--direction", "down", "--depth", "1"
    )
    assert result["root"]["fqn"] == "App\\Component\\EmailSenderInterface"

    fqns = _collect_fqns(result["tree"])
    assert any("EmailSender" in fqn for fqn in fqns), (
        f"Expected EmailSender in implementors, got: {fqns}"
    )


def _collect_fqns(tree: list[dict]) -> list[str]:
    """Recursively collect all FQNs from a tree structure."""
    fqns = []
    for entry in tree:
        fqns.append(entry["fqn"])
        if entry.get("children"):
            fqns.extend(_collect_fqns(entry["children"]))
    return fqns
