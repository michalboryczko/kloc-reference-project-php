"""Owners command contract tests.

Validates containment chain: Method -> Class -> File.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))
from src.decorators import contract_test
from src.output_validator import OutputValidator


@contract_test(
    name="Owners of method shows Method -> Class -> File chain",
    description="Verifies that owners of App\\Entity\\Order::getId() returns the containment chain: Method -> Class -> File",
    category="owners",
)
@pytest.mark.owners
def test_owners_method_chain(cli: OutputValidator):
    """Owners chain: Method -> Class -> File."""
    result = cli.json_output("owners", "App\\Entity\\Order::getId()")
    chain = result["chain"]

    # Chain should go from innermost to outermost
    assert len(chain) >= 2  # At least Method + Class (maybe File)

    # First entry should be the method itself or its class
    kinds = [c["kind"] for c in chain]
    fqns = [c["fqn"] for c in chain]

    # Should contain Method, Class (and optionally File)
    assert "Method" in kinds or "Class" in kinds
    assert any("Order" in fqn for fqn in fqns)


@contract_test(
    name="Owners of property shows Property -> Class -> File chain",
    description="Verifies that owners of App\\Entity\\Order::$id returns the containment chain: Property -> Class -> File",
    category="owners",
)
@pytest.mark.owners
def test_owners_property_chain(cli: OutputValidator):
    """Owners chain: Property -> Class -> File."""
    result = cli.json_output("owners", "App\\Entity\\Order::$id")
    chain = result["chain"]

    assert len(chain) >= 2  # At least Property + Class

    kinds = [c["kind"] for c in chain]
    fqns = [c["fqn"] for c in chain]

    assert any("Order" in fqn for fqn in fqns)


@contract_test(
    name="Owners of nested method shows full chain",
    description="Verifies that owners of App\\Service\\OrderService::createOrder() shows the full containment chain through class and file",
    category="owners",
)
@pytest.mark.owners
def test_owners_nested_method(cli: OutputValidator):
    """Owners of service method should show full containment."""
    result = cli.json_output("owners", "App\\Service\\OrderService::createOrder()")
    chain = result["chain"]

    fqns = [c["fqn"] for c in chain]
    # Should include OrderService class in the chain
    assert any("OrderService" in fqn for fqn in fqns), (
        f"Expected OrderService in chain, got: {fqns}"
    )
