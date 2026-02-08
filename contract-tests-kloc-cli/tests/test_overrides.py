"""Overrides command contract tests.

Validates override tree: direction up (overridden method), direction down (overriding methods).
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))
from src.decorators import contract_test
from src.output_validator import OutputValidator


@contract_test(
    name="Overrides direction up shows overridden method",
    description="Verifies that overrides of EmailSender::send() with direction=up shows EmailSenderInterface::send()",
    category="overrides",
)
@pytest.mark.overrides
def test_overrides_direction_up(cli: OutputValidator):
    """Direction up should show the overridden parent method."""
    result = cli.json_output(
        "overrides", "App\\Component\\EmailSender::send()", "--direction", "up", "--depth", "1"
    )
    assert result["root"]["fqn"] == "App\\Component\\EmailSender::send()"
    assert result["direction"] == "up"

    fqns = _collect_fqns(result["tree"])
    assert any("EmailSenderInterface" in fqn for fqn in fqns), (
        f"Expected EmailSenderInterface::send() in override chain, got: {fqns}"
    )


@contract_test(
    name="Overrides direction down shows overriding methods",
    description="Verifies that overrides of EmailSenderInterface::send() with direction=down shows EmailSender::send()",
    category="overrides",
)
@pytest.mark.overrides
def test_overrides_direction_down(cli: OutputValidator):
    """Direction down should show overriding concrete methods."""
    result = cli.json_output(
        "overrides", "App\\Component\\EmailSenderInterface::send()", "--direction", "down", "--depth", "1"
    )
    assert result["root"]["fqn"] == "App\\Component\\EmailSenderInterface::send()"
    assert result["direction"] == "down"

    fqns = _collect_fqns(result["tree"])
    assert any("EmailSender" in fqn and "send" in fqn for fqn in fqns), (
        f"Expected EmailSender::send() in overriding methods, got: {fqns}"
    )


@contract_test(
    name="Overrides of AbstractOrderProcessor::process() direction down",
    description="Verifies that overrides of AbstractOrderProcessor::process() with direction=down shows StandardOrderProcessor::process()",
    category="overrides",
)
@pytest.mark.overrides
def test_overrides_abstract_down(cli: OutputValidator):
    """Direction down on abstract method should show concrete implementations."""
    result = cli.json_output(
        "overrides", "App\\Service\\AbstractOrderProcessor::process()", "--direction", "down", "--depth", "1"
    )

    fqns = _collect_fqns(result["tree"])
    assert any("StandardOrderProcessor" in fqn for fqn in fqns), (
        f"Expected StandardOrderProcessor::process() in overrides, got: {fqns}"
    )


def _collect_fqns(tree: list[dict]) -> list[str]:
    """Recursively collect all FQNs from a tree structure."""
    fqns = []
    for entry in tree:
        fqns.append(entry["fqn"])
        if entry.get("children"):
            fqns.extend(_collect_fqns(entry["children"]))
    return fqns
