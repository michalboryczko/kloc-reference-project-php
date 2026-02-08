"""Context query E2E tests.

Validates context queries against real pipeline output from the reference project.
Context shows both USES and USED BY for a symbol.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from decorators import contract_test
from helpers import collect_fqns


pytestmark = pytest.mark.context


@contract_test(
    name="Context of OrderRepository shows USES and USED BY",
    description="Verifies context of OrderRepository shows Order in USES and OrderService in USED BY",
    category="context",
)
def test_context_order_repository(cli):
    """Context should show both USES and USED BY."""
    result = cli("context", "App\\Repository\\OrderRepository", "--depth", "1")
    assert result["target"]["fqn"] == "App\\Repository\\OrderRepository"

    assert "used_by" in result
    assert "uses" in result

    # OrderRepository is used by OrderService
    used_by_fqns = collect_fqns(result["used_by"])
    assert any("OrderService" in fqn for fqn in used_by_fqns), (
        f"Expected OrderService in used_by, got: {used_by_fqns}"
    )

    # OrderRepository uses Order
    uses_fqns = collect_fqns(result["uses"])
    assert any("Order" in fqn for fqn in uses_fqns), (
        f"Expected Order in uses, got: {uses_fqns}"
    )


@contract_test(
    name="Context of OrderService",
    description="Verifies context of OrderService shows OrderController in USED BY and OrderRepository in USES",
    category="context",
)
def test_context_order_service(cli):
    """Context of OrderService should show both directions."""
    result = cli("context", "App\\Service\\OrderService", "--depth", "1")

    # OrderService is used by OrderController
    used_by_fqns = collect_fqns(result["used_by"])
    assert any("OrderController" in fqn for fqn in used_by_fqns), (
        f"Expected OrderController in used_by, got: {used_by_fqns}"
    )

    # OrderService uses OrderRepository and/or Order
    uses_fqns = collect_fqns(result["uses"])
    assert any("OrderRepository" in fqn or "Order" in fqn for fqn in uses_fqns), (
        f"Expected OrderRepository or Order in uses, got: {uses_fqns}"
    )


@contract_test(
    name="Context --impl includes implementations",
    description="Verifies context with --impl for EmailSenderInterface includes concrete EmailSender",
    category="context",
)
def test_context_impl_flag(cli):
    """--impl should include interface implementations in context output."""
    # Get context WITHOUT --impl
    result_without = cli(
        "context", "App\\Component\\EmailSenderInterface", "--depth", "1"
    )
    # Get context WITH --impl
    result_with = cli(
        "context", "App\\Component\\EmailSenderInterface", "--depth", "1", "--impl"
    )
    assert result_with["target"]["fqn"] == "App\\Component\\EmailSenderInterface"

    # Collect all FQNs from both results
    fqns_without = (
        collect_fqns(result_without.get("used_by", []))
        + collect_fqns(result_without.get("uses", []))
    )
    fqns_with = (
        collect_fqns(result_with.get("used_by", []))
        + collect_fqns(result_with.get("uses", []))
    )

    # With --impl, the result should include at least as many symbols
    assert len(fqns_with) >= len(fqns_without), (
        f"--impl should produce at least as many results: "
        f"with={len(fqns_with)}, without={len(fqns_without)}"
    )
    # The concrete EmailSender should appear in --impl results
    assert any("EmailSender" in fqn and "Interface" not in fqn for fqn in fqns_with), (
        f"Expected concrete EmailSender in --impl results, got: {fqns_with}"
    )
