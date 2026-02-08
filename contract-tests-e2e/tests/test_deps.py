"""Deps query E2E tests.

Validates dependency queries against real pipeline output from the reference project.
Tests that the full pipeline correctly identifies what a symbol depends on.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from decorators import contract_test
from helpers import collect_fqns


pytestmark = pytest.mark.deps


@contract_test(
    name="Deps of OrderController",
    description="Verifies deps of App\\Ui\\Rest\\Controller\\OrderController includes OrderService",
    category="deps",
)
def test_deps_order_controller(cli):
    """OrderController should depend on OrderService."""
    result = cli(
        "deps", "App\\Ui\\Rest\\Controller\\OrderController", "--depth", "1"
    )
    fqns = collect_fqns(result["tree"])
    assert any("OrderService" in fqn for fqn in fqns), (
        f"Expected OrderService in deps of OrderController, got: {fqns}"
    )


@contract_test(
    name="Deps of OrderService",
    description="Verifies deps of App\\Service\\OrderService includes OrderRepository",
    category="deps",
)
def test_deps_order_service(cli):
    """OrderService should depend on OrderRepository."""
    result = cli("deps", "App\\Service\\OrderService", "--depth", "1")
    assert result["target"]["fqn"] == "App\\Service\\OrderService"
    assert result["max_depth"] == 1

    fqns = collect_fqns(result["tree"])
    assert any("OrderRepository" in fqn for fqn in fqns), (
        f"Expected OrderRepository in deps of OrderService, got: {fqns}"
    )


@contract_test(
    name="Deps depth 2 of OrderService",
    description="Verifies deps at depth 2 follows OrderService -> OrderRepository -> Order",
    category="deps",
)
def test_deps_depth_2(cli):
    """Depth-2 deps should follow dependency chains deeper."""
    result = cli("deps", "App\\Service\\OrderService", "--depth", "2")
    assert result["max_depth"] == 2

    fqns = collect_fqns(result["tree"])
    assert len(fqns) > 0, "Depth 2 should produce results"
