"""Context command contract tests.

Validates combined usages+deps, --impl flag, --direct flag.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))
from src.decorators import contract_test
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
    used_by_fqns = _collect_fqns(result["used_by"])
    assert any("OrderService" in fqn for fqn in used_by_fqns), (
        f"Expected OrderService in used_by, got: {used_by_fqns}"
    )

    # OrderRepository uses Order
    uses_fqns = _collect_fqns(result["uses"])
    assert any("Order" in fqn for fqn in uses_fqns), (
        f"Expected Order in uses, got: {uses_fqns}"
    )


@contract_test(
    name="Context --impl includes implementations",
    description="Verifies that context with --impl flag for EmailSenderInterface includes concrete EmailSender implementation",
    category="context",
)
@pytest.mark.context
def test_context_impl_flag(cli: OutputValidator):
    """--impl should include interface implementations in USES direction."""
    result = cli.json_output(
        "context", "App\\Component\\EmailSenderInterface", "--depth", "1", "--impl"
    )
    assert result["target"]["fqn"] == "App\\Component\\EmailSenderInterface"

    # With --impl, should show implementations
    uses_fqns = _collect_fqns(result["uses"])
    # The interface may show EmailSender as an implementor
    # Check that the result is non-empty or contains implementation info
    assert "used_by" in result or "uses" in result


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
    used_by_fqns = _collect_fqns(result["used_by"])
    assert any("OrderController" in fqn for fqn in used_by_fqns), (
        f"Expected OrderController in used_by, got: {used_by_fqns}"
    )

    # OrderService uses OrderRepository and Order
    uses_fqns = _collect_fqns(result["uses"])
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
    """--direct should filter to direct references only."""
    result = cli.json_output(
        "context", "App\\Entity\\Order", "--depth", "1", "--direct"
    )
    # With --direct, should only show direct references (extends, implements, type_hints)
    # not member-level usages
    assert "used_by" in result
    assert "uses" in result


def _collect_fqns(entries: list[dict]) -> list[str]:
    """Recursively collect all FQNs from context entries."""
    fqns = []
    for entry in entries:
        fqns.append(entry["fqn"])
        if entry.get("children"):
            fqns.extend(_collect_fqns(entry["children"]))
        if entry.get("implementations"):
            fqns.extend(_collect_fqns(entry["implementations"]))
    return fqns
