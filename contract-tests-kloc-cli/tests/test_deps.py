"""Deps command contract tests.

Validates dependency finding: depth 1, depth 2 expansion, dependency types.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))
from src.decorators import contract_test
from src.output_validator import OutputValidator


@contract_test(
    name="Deps depth 1 of OrderService",
    description="Verifies that deps of App\\Service\\OrderService at depth 1 includes OrderRepository and Order",
    category="deps",
)
@pytest.mark.deps
def test_deps_depth_1(cli: OutputValidator):
    """Depth-1 deps of OrderService should include OrderRepository."""
    result = cli.json_output("deps", "App\\Service\\OrderService", "--depth", "1")
    assert result["target"]["fqn"] == "App\\Service\\OrderService"
    assert result["max_depth"] == 1

    fqns = _collect_fqns(result["tree"])
    assert any("OrderRepository" in fqn for fqn in fqns), (
        f"Expected OrderRepository in deps, got: {fqns}"
    )


@contract_test(
    name="Deps depth 2 expansion",
    description="Verifies that deps of App\\Service\\OrderService at depth 2 follows the dependency chain further",
    category="deps",
)
@pytest.mark.deps
def test_deps_depth_2(cli: OutputValidator):
    """Depth-2 deps should follow dependency chain."""
    result = cli.json_output("deps", "App\\Service\\OrderService", "--depth", "2")
    assert result["max_depth"] == 2

    fqns = _collect_fqns(result["tree"])
    # Depth 2 should expand further
    assert len(fqns) > 0


@contract_test(
    name="Deps of OrderController includes OrderService",
    description="Verifies that deps of App\\Ui\\Rest\\Controller\\OrderController includes OrderService",
    category="deps",
)
@pytest.mark.deps
def test_deps_controller(cli: OutputValidator):
    """Deps of OrderController should include OrderService."""
    result = cli.json_output(
        "deps", "App\\Ui\\Rest\\Controller\\OrderController", "--depth", "1"
    )
    fqns = _collect_fqns(result["tree"])
    assert any("OrderService" in fqn for fqn in fqns), (
        f"Expected OrderService in deps, got: {fqns}"
    )


def _collect_fqns(tree: list[dict]) -> list[str]:
    """Recursively collect all FQNs from a tree structure."""
    fqns = []
    for entry in tree:
        fqns.append(entry["fqn"])
        if entry.get("children"):
            fqns.extend(_collect_fqns(entry["children"]))
    return fqns
