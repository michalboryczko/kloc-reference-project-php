"""Overrides query E2E tests.

Validates override chain queries against real pipeline output from the reference project.
Tests method override relationships in both up and down directions.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from decorators import contract_test
from helpers import collect_fqns


pytestmark = pytest.mark.overrides


@contract_test(
    name="Overrides direction down shows overriding methods",
    description="Verifies overrides of AbstractOrderProcessor::doProcess() with direction=down shows StandardOrderProcessor::doProcess()",
    category="overrides",
)
def test_overrides_abstract_down(cli):
    """Direction down should show methods that override the abstract method."""
    result = cli(
        "overrides", "App\\Service\\AbstractOrderProcessor::doProcess()",
        "--direction", "down", "--depth", "1"
    )
    assert result["root"]["fqn"] == "App\\Service\\AbstractOrderProcessor::doProcess()"
    assert result["direction"] == "down"

    fqns = collect_fqns(result["tree"])
    assert any("StandardOrderProcessor" in fqn for fqn in fqns), (
        f"Expected StandardOrderProcessor::doProcess() in overrides, got: {fqns}"
    )


@contract_test(
    name="Overrides direction up shows overridden method",
    description="Verifies overrides of EmailSender::send() with direction=up shows EmailSenderInterface::send()",
    category="overrides",
)
def test_overrides_concrete_up(cli):
    """Direction up should show the method being overridden."""
    result = cli(
        "overrides", "App\\Component\\EmailSender::send()",
        "--direction", "up", "--depth", "1"
    )
    assert result["root"]["fqn"] == "App\\Component\\EmailSender::send()"
    assert result["direction"] == "up"

    fqns = collect_fqns(result["tree"])
    assert any("EmailSenderInterface" in fqn for fqn in fqns), (
        f"Expected EmailSenderInterface::send() in override chain, got: {fqns}"
    )
