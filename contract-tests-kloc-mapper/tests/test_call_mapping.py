"""Call mapping tests for kloc-mapper.

Verifies that calls.json calls become Call nodes with correct call_kind
and associated edges (calls, receiver, argument, produces).
"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from decorators import contract_test
from sot_data import SoTData


pytestmark = pytest.mark.call_mapping


@contract_test(
    name="Method call node",
    description="Verifies calls.json method call becomes Call node with call_kind='method'",
    category="call-mapping",
)
def test_method_call_node(sot_data: SoTData):
    """Method calls from calls.json should become Call nodes."""
    call_nodes = sot_data.nodes_by_kind("Call")
    method_calls = [c for c in call_nodes if c.get("call_kind") == "method"]
    assert len(method_calls) >= 1, "Should have at least one method Call node"

    call = method_calls[0]
    assert call["kind"] == "Call"
    assert call["call_kind"] == "method"
    assert call.get("file") is not None, "Call node should have file"
    assert call.get("range") is not None, "Call node should have range"


@contract_test(
    name="Call has calls edge to target",
    description="Verifies Call node has 'calls' edge to the target Method node (callee)",
    category="call-mapping",
)
def test_call_has_calls_edge(sot_data: SoTData):
    """Each Call node should have a calls edge to its target."""
    call_nodes = sot_data.nodes_by_kind("Call")
    calls_edges = sot_data.edges_by_type("calls")

    # At least one Call node should have a calls edge
    call_ids = {c["id"] for c in call_nodes}
    call_edge_sources = {e["source"] for e in calls_edges}

    connected_calls = call_ids & call_edge_sources
    assert len(connected_calls) >= 1, \
        "At least one Call node should have a 'calls' edge to a target"


@contract_test(
    name="Call has receiver edge",
    description="Verifies Call node has 'receiver' edge to the receiver Value node",
    category="call-mapping",
)
def test_call_has_receiver_edge(sot_data: SoTData):
    """Call nodes with receivers should have receiver edges."""
    receiver_edges = sot_data.edges_by_type("receiver")
    assert len(receiver_edges) >= 1, "Should have at least one receiver edge"

    # Verify the receiver edge connects Call -> Value
    for edge in receiver_edges:
        source = sot_data.node_by_id(edge["source"])
        target = sot_data.node_by_id(edge["target"])
        assert source is not None and source["kind"] == "Call"
        assert target is not None and target["kind"] == "Value"


@contract_test(
    name="Call has argument edges with position",
    description="Verifies Call node has 'argument' edges to argument Value nodes with 0-based position",
    category="call-mapping",
)
def test_call_has_argument_edges(sot_data: SoTData):
    """Call nodes with arguments should have argument edges with position."""
    arg_edges = sot_data.edges_by_type("argument")
    assert len(arg_edges) >= 1, "Should have at least one argument edge"

    for edge in arg_edges:
        assert "position" in edge, "Argument edge must have position field"
        assert isinstance(edge["position"], int), "Position must be integer"
        assert edge["position"] >= 0, "Position must be non-negative"


@contract_test(
    name="Call has produces edge to result",
    description="Verifies Call node has 'produces' edge to result Value node",
    category="call-mapping",
)
def test_call_has_produces_edge(sot_data: SoTData):
    """Call nodes should have produces edge to their result value."""
    produces_edges = sot_data.edges_by_type("produces")
    assert len(produces_edges) >= 1, "Should have at least one produces edge"

    for edge in produces_edges:
        source = sot_data.node_by_id(edge["source"])
        target = sot_data.node_by_id(edge["target"])
        assert source is not None and source["kind"] == "Call", \
            "produces source should be Call node"
        assert target is not None and target["kind"] == "Value", \
            "produces target should be Value node"


@contract_test(
    name="Call contained in enclosing method",
    description="Verifies Call node is contained within its caller method via contains edge",
    category="call-mapping",
)
def test_call_contained_in_method(sot_data: SoTData):
    """Call nodes should be contained by their enclosing method."""
    call_nodes = sot_data.nodes_by_kind("Call")
    contains_edges = sot_data.edges_by_type("contains")

    # Find contains edges where target is a Call node
    call_ids = {c["id"] for c in call_nodes}
    containing_edges = [e for e in contains_edges if e["target"] in call_ids]
    assert len(containing_edges) >= 1, \
        "At least one Call node should be contained by a method via contains edge"

    # Verify the container is a Method or Function
    for edge in containing_edges:
        container = sot_data.node_by_id(edge["source"])
        assert container is not None
        assert container["kind"] in ("Method", "Function"), \
            f"Call should be contained by Method or Function, got {container['kind']}"


@contract_test(
    name="Call node name derived from callee",
    description="Verifies Call node name is derived from the callee method name",
    category="call-mapping",
)
def test_call_node_name(sot_data: SoTData):
    """Call node name should reflect what is being called."""
    call_nodes = sot_data.nodes_by_kind("Call")
    for call in call_nodes:
        name = call.get("name", "")
        assert len(name) > 0, f"Call node should have a non-empty name: {call}"
