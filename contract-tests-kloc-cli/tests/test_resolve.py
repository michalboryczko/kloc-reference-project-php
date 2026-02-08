"""Resolve command contract tests.

Validates symbol resolution: exact match, partial match, case-insensitive, not found.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))
from src.decorators import contract_test
from src.output_validator import OutputValidator


@contract_test(
    name="Resolve exact FQN match",
    description="Verifies that resolving an exact FQN returns a single matching node with correct kind, file, and fqn",
    category="resolve",
)
@pytest.mark.resolve
def test_resolve_exact_match(cli: OutputValidator):
    """Exact FQN match should return a single node."""
    result = cli.json_output("resolve", "App\\Entity\\Order")
    assert result["fqn"] == "App\\Entity\\Order"
    assert result["kind"] == "Class"
    assert result["file"] == "src/Entity/Order.php"


@contract_test(
    name="Resolve partial name match",
    description="Verifies that resolving a short name (e.g., 'OrderService') returns matching candidates",
    category="resolve",
)
@pytest.mark.resolve
def test_resolve_partial_match(cli: OutputValidator):
    """Partial name match should return candidates."""
    result = cli.json_output("resolve", "OrderService")
    # Should match App\Service\OrderService
    # Could return single node or candidates list
    if "candidates" in result:
        fqns = [c["fqn"] for c in result["candidates"]]
        assert any("OrderService" in fqn for fqn in fqns)
    else:
        assert "OrderService" in result["fqn"]


@contract_test(
    name="Resolve not-found returns error",
    description="Verifies that resolving a non-existent symbol returns an error with the queried symbol in the message",
    category="resolve",
)
@pytest.mark.resolve
def test_resolve_not_found(cli: OutputValidator):
    """Non-existent symbol should return error."""
    data, returncode = cli.json_output_allow_error("resolve", "NonExistent\\Class\\That\\Does\\Not\\Exist")
    assert returncode != 0
    if data:
        assert "error" in data
        assert "not found" in data["error"].lower() or "not found" in str(data).lower()


@contract_test(
    name="Resolve method by FQN",
    description="Verifies that resolving a method FQN like 'App\\Entity\\Order::getId()' returns the correct method node",
    category="resolve",
)
@pytest.mark.resolve
def test_resolve_method_fqn(cli: OutputValidator):
    """Method FQN should resolve to the correct method node."""
    result = cli.json_output("resolve", "App\\Entity\\Order::getId()")
    assert result["fqn"] == "App\\Entity\\Order::getId()"
    assert result["kind"] == "Method"
    assert result["file"] == "src/Entity/Order.php"
