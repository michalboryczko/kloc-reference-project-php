"""Value mapping tests for kloc-mapper.

Verifies that calls.json values become Value nodes with correct
value_kind (parameter, local, result, literal, constant) and type_symbol.
"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from decorators import contract_test
from sot_data import SoTData


pytestmark = pytest.mark.value_mapping


@contract_test(
    name="Parameter value node",
    description="Verifies calls.json parameter value becomes Value node with value_kind='parameter'",
    category="value-mapping",
)
def test_parameter_value_node(sot_data: SoTData):
    """Parameter values from calls.json should become Value nodes."""
    value_nodes = sot_data.nodes_by_kind("Value")
    param_nodes = [v for v in value_nodes if v.get("value_kind") == "parameter"]
    assert len(param_nodes) >= 1, "Should have at least one parameter Value node"

    # Check first parameter node has expected fields
    param = param_nodes[0]
    assert param["kind"] == "Value"
    assert param["value_kind"] == "parameter"
    assert param.get("file") is not None, "Parameter value should have file"


@contract_test(
    name="Local value node",
    description="Verifies calls.json local value becomes Value node with value_kind='local'",
    category="value-mapping",
)
def test_local_value_node(sot_data: SoTData):
    """Local variable values should become Value nodes."""
    value_nodes = sot_data.nodes_by_kind("Value")
    local_nodes = [v for v in value_nodes if v.get("value_kind") == "local"]
    assert len(local_nodes) >= 1, "Should have at least one local Value node"

    local = local_nodes[0]
    assert local["kind"] == "Value"
    assert local["value_kind"] == "local"


@contract_test(
    name="Result value node",
    description="Verifies calls.json result value becomes Value node with value_kind='result'",
    category="value-mapping",
)
def test_result_value_node(sot_data: SoTData):
    """Result values from calls.json should become Value nodes."""
    value_nodes = sot_data.nodes_by_kind("Value")
    result_nodes = [v for v in value_nodes if v.get("value_kind") == "result"]
    assert len(result_nodes) >= 1, "Should have at least one result Value node"

    result = result_nodes[0]
    assert result["kind"] == "Value"
    assert result["value_kind"] == "result"


@contract_test(
    name="Literal value node",
    description="Verifies calls.json literal value becomes Value node with value_kind='literal'",
    category="value-mapping",
)
def test_literal_value_node(sot_data: SoTData):
    """Literal values from calls.json should become Value nodes."""
    value_nodes = sot_data.nodes_by_kind("Value")
    literal_nodes = [v for v in value_nodes if v.get("value_kind") == "literal"]
    assert len(literal_nodes) >= 1, "Should have at least one literal Value node"


@contract_test(
    name="Constant value node",
    description="Verifies calls.json constant value becomes Value node with value_kind='constant'",
    category="value-mapping",
)
def test_constant_value_node(sot_data: SoTData):
    """Constant values from calls.json should become Value nodes."""
    value_nodes = sot_data.nodes_by_kind("Value")
    constant_nodes = [v for v in value_nodes if v.get("value_kind") == "constant"]
    assert len(constant_nodes) >= 1, "Should have at least one constant Value node"


@contract_test(
    name="Value type_symbol mapped",
    description="Verifies Value nodes with typed values have type_symbol field populated",
    category="value-mapping",
)
def test_value_type_symbol(sot_data: SoTData):
    """Value nodes should preserve type_symbol from calls.json."""
    value_nodes = sot_data.nodes_by_kind("Value")
    # Parameter nodes for $order should have type_symbol pointing to Order class
    typed_values = [v for v in value_nodes if v.get("type_symbol")]
    assert len(typed_values) >= 1, "Should have at least one Value node with type_symbol"


@contract_test(
    name="Value node file and range",
    description="Verifies Value nodes have file and range fields from calls.json location",
    category="value-mapping",
)
def test_value_file_and_range(sot_data: SoTData):
    """Value nodes should have file and range from calls.json location."""
    value_nodes = sot_data.nodes_by_kind("Value")
    for vn in value_nodes:
        assert vn.get("file") is not None, f"Value node should have file: {vn}"
        assert vn.get("range") is not None, f"Value node should have range: {vn}"


@contract_test(
    name="Type_of edge for typed values",
    description="Verifies type_of edge connects Value node to its type Class/Interface",
    category="value-mapping",
)
def test_type_of_edge(sot_data: SoTData):
    """Typed value nodes should have type_of edge to their type."""
    type_of_edges = sot_data.edges_by_type("type_of")
    # We have parameter values typed as Order
    assert len(type_of_edges) >= 1, "Should have at least one type_of edge"

    for edge in type_of_edges:
        source = sot_data.node_by_id(edge["source"])
        target = sot_data.node_by_id(edge["target"])
        assert source is not None
        assert target is not None
        assert source["kind"] == "Value", "type_of source should be Value node"
        assert target["kind"] in ("Class", "Interface", "Trait", "Enum"), \
            f"type_of target should be a type node, got {target['kind']}"
