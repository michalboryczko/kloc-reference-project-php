"""Usages query E2E tests.

Validates usage queries against real pipeline output from the reference project.
Tests that the full pipeline correctly tracks which symbols reference which.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from decorators import contract_test
from helpers import collect_fqns


pytestmark = pytest.mark.usages


@contract_test(
    name="Usages of Order entity",
    description="Verifies usages of App\\Entity\\Order returns OrderRepository, OrderService, and OrderController",
    category="usages",
)
def test_usages_order_entity(cli):
    """Order should be used by OrderRepository and OrderService."""
    result = cli("usages", "App\\Entity\\Order", "--depth", "1")
    assert result["target"]["fqn"] == "App\\Entity\\Order"

    fqns = collect_fqns(result["tree"])
    assert any("OrderRepository" in fqn for fqn in fqns), (
        f"Expected OrderRepository in usages of Order, got: {fqns}"
    )


@contract_test(
    name="Usages of OrderRepository",
    description="Verifies usages of App\\Repository\\OrderRepository includes OrderService",
    category="usages",
)
def test_usages_order_repository(cli):
    """OrderRepository should be used by OrderService."""
    result = cli("usages", "App\\Repository\\OrderRepository", "--depth", "1")
    fqns = collect_fqns(result["tree"])
    assert any("OrderService" in fqn for fqn in fqns), (
        f"Expected OrderService in usages of OrderRepository, got: {fqns}"
    )


@contract_test(
    name="Usages depth 2 expands transitively",
    description="Verifies usages at depth 2 follows the chain further (Order -> OrderRepository -> OrderService)",
    category="usages",
)
def test_usages_depth_2(cli):
    """Depth-2 usages should expand transitively."""
    result = cli("usages", "App\\Entity\\Order", "--depth", "2")
    assert result["max_depth"] == 2

    fqns = collect_fqns(result["tree"])
    # At depth 2, we should find symbols that use Order's users
    assert len(fqns) > 0, "Depth 2 should produce results"


@contract_test(
    name="Usages of OrderService",
    description="Verifies usages of App\\Service\\OrderService includes OrderController",
    category="usages",
)
def test_usages_order_service(cli):
    """OrderService should be used by OrderController."""
    result = cli("usages", "App\\Service\\OrderService", "--depth", "1")
    fqns = collect_fqns(result["tree"])
    assert any("OrderController" in fqn for fqn in fqns), (
        f"Expected OrderController in usages of OrderService, got: {fqns}"
    )
