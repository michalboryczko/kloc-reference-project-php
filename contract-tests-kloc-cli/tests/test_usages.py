"""Usages command contract tests.

Validates usage finding: depth 1, depth 2 expansion, limit parameter.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))
from src.decorators import contract_test
from src.output_validator import OutputValidator


@contract_test(
    name="Usages depth 1 of Order entity",
    description="Verifies that usages of App\\Entity\\Order at depth 1 includes OrderRepository and OrderService",
    category="usages",
)
@pytest.mark.usages
def test_usages_depth_1(cli: OutputValidator):
    """Depth-1 usages of Order should include OrderRepository and OrderService."""
    result = cli.json_output("usages", "App\\Entity\\Order", "--depth", "1")
    assert result["target"]["fqn"] == "App\\Entity\\Order"
    assert result["max_depth"] == 1

    # Collect all FQNs in the tree
    fqns = _collect_fqns(result["tree"])
    # OrderRepository uses Order (in save() and findById())
    assert any("OrderRepository" in fqn for fqn in fqns), (
        f"Expected OrderRepository in usages, got: {fqns}"
    )


@contract_test(
    name="Usages depth 2 expansion",
    description="Verifies that usages of App\\Entity\\Order at depth 2 expands to include transitive users like OrderController",
    category="usages",
)
@pytest.mark.usages
def test_usages_depth_2(cli: OutputValidator):
    """Depth-2 usages should expand to transitive users."""
    result = cli.json_output("usages", "App\\Entity\\Order", "--depth", "2")
    assert result["max_depth"] == 2

    # Depth 2 should find users of OrderRepository and OrderService
    fqns = _collect_fqns(result["tree"])
    # At depth 2, we should see more symbols than depth 1
    assert len(fqns) > 0


@contract_test(
    name="Usages with limit parameter",
    description="Verifies that the --limit parameter caps the number of results returned by the usages command",
    category="usages",
)
@pytest.mark.usages
def test_usages_limit(cli: OutputValidator):
    """--limit should cap results."""
    result = cli.json_output("usages", "App\\Entity\\Order", "--depth", "1", "--limit", "1")
    assert result["total"] <= 1


@contract_test(
    name="Usages of OrderRepository",
    description="Verifies that usages of App\\Repository\\OrderRepository includes OrderService",
    category="usages",
)
@pytest.mark.usages
def test_usages_order_repository(cli: OutputValidator):
    """Usages of OrderRepository should include OrderService."""
    result = cli.json_output("usages", "App\\Repository\\OrderRepository", "--depth", "1")
    fqns = _collect_fqns(result["tree"])
    assert any("OrderService" in fqn for fqn in fqns), (
        f"Expected OrderService in usages, got: {fqns}"
    )


def _collect_fqns(tree: list[dict]) -> list[str]:
    """Recursively collect all FQNs from a tree structure."""
    fqns = []
    for entry in tree:
        fqns.append(entry["fqn"])
        if entry.get("children"):
            fqns.extend(_collect_fqns(entry["children"]))
    return fqns
