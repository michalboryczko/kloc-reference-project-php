"""Context command contract tests.

Validates combined usages+deps, --impl flag, --direct flag.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))
from src.decorators import contract_test
from src.helpers import collect_fqns
from src.output_validator import OutputValidator


@contract_test(
    name="Context shows USES and USED BY",
    description="Verifies that context of App\\Repository\\OrderRepository shows both USES (Order) and USED BY (OrderService) sections",
    category="context",
)
@pytest.mark.context
def test_context_bidirectional(cli: OutputValidator):
    """Context should show both USES and USED BY."""
    result = cli.json_output("context", "App\\Repository\\OrderRepository", "--depth", "1")
    assert result["target"]["fqn"] == "App\\Repository\\OrderRepository"

    # Should have both sections
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
    name="Context --impl includes implementations",
    description="Verifies that context with --impl flag produces at least as many results as without it",
    category="context",
)
@pytest.mark.context
def test_context_impl_flag(cli: OutputValidator):
    """--impl should produce at least as many results as without it.

    The --impl flag enables polymorphic analysis:
    - USES direction: attaches implementations to interface/method targets
    - USED BY direction: for concrete methods, includes callers of the interface method
    With --impl, the result set should be a superset of the result without --impl.
    """
    # Get context WITHOUT --impl
    result_without = cli.json_output(
        "context", "App\\Service\\OrderService", "--depth", "1"
    )
    # Get context WITH --impl
    result_with = cli.json_output(
        "context", "App\\Service\\OrderService", "--depth", "1", "--impl"
    )
    assert result_with["target"]["fqn"] == "App\\Service\\OrderService"

    # Both results should have used_by and uses sections
    assert "used_by" in result_with
    assert "uses" in result_with

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
    # (implementations are added as additional entries, never removed)
    assert len(fqns_with) >= len(fqns_without), (
        f"--impl should produce at least as many results: "
        f"with={len(fqns_with)}, without={len(fqns_without)}"
    )
    # Every FQN from without-impl should still be present in with-impl
    fqns_without_set = set(fqns_without)
    fqns_with_set = set(fqns_with)
    assert fqns_without_set.issubset(fqns_with_set), (
        f"--impl results should be superset of default results. "
        f"Missing: {fqns_without_set - fqns_with_set}"
    )


@contract_test(
    name="Context of OrderService",
    description="Verifies that context of App\\Service\\OrderService shows correct usages and dependencies",
    category="context",
)
@pytest.mark.context
def test_context_order_service(cli: OutputValidator):
    """Context of OrderService should show both directions."""
    result = cli.json_output("context", "App\\Service\\OrderService", "--depth", "1")

    # OrderService is used by OrderController
    used_by_fqns = collect_fqns(result["used_by"])
    assert any("OrderController" in fqn for fqn in used_by_fqns), (
        f"Expected OrderController in used_by, got: {used_by_fqns}"
    )

    # OrderService uses OrderRepository and Order
    uses_fqns = collect_fqns(result["uses"])
    assert any("OrderRepository" in fqn or "Order" in fqn for fqn in uses_fqns), (
        f"Expected OrderRepository or Order in uses, got: {uses_fqns}"
    )


@contract_test(
    name="Context --direct filters member usages",
    description="Verifies that context with --direct flag shows only direct symbol references, not member usages",
    category="context",
)
@pytest.mark.context
def test_context_direct_flag(cli: OutputValidator):
    """--direct should filter to direct references only (fewer results than default)."""
    # Get context WITHOUT --direct (includes member-level usages)
    result_full = cli.json_output(
        "context", "App\\Entity\\Order", "--depth", "1"
    )
    # Get context WITH --direct (only direct references like extends, implements, type_hints)
    result_direct = cli.json_output(
        "context", "App\\Entity\\Order", "--depth", "1", "--direct"
    )

    assert "used_by" in result_direct
    assert "uses" in result_direct

    # Collect FQNs from both
    full_fqns = (
        collect_fqns(result_full.get("used_by", []))
        + collect_fqns(result_full.get("uses", []))
    )
    direct_fqns = (
        collect_fqns(result_direct.get("used_by", []))
        + collect_fqns(result_direct.get("uses", []))
    )

    # --direct should produce fewer or equal results (subset of full context)
    assert len(direct_fqns) <= len(full_fqns), (
        f"--direct should produce at most as many results as default: "
        f"direct={len(direct_fqns)}, full={len(full_fqns)}"
    )
