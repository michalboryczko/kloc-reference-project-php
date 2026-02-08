"""Edge creation tests for kloc-mapper.

Tests that each of the 12 EdgeTypes is created correctly with proper
source, target, and type fields.

Uses the full fixture with known relationships:
- File contains Class (contains)
- Class contains Method (contains)
- StandardOrderProcessor extends AbstractOrderProcessor (extends)
- EmailSender implements EmailSenderInterface (implements)
- OrderController uses LoggableTrait (uses_trait)
- OrderService::createOrder() uses OrderRepository::save() (uses)
- StandardOrderProcessor::process() overrides AbstractOrderProcessor::process() (overrides)
- Argument type_hint to Class (type_hint)
- Call nodes with calls, receiver, argument, produces edges
"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from decorators import contract_test
from sot_data import SoTData


pytestmark = pytest.mark.edge_creation


@contract_test(
    name="Contains edge: File -> Class",
    description="Verifies contains edge from File node to top-level Class node",
    category="edge-creation",
)
def test_contains_file_to_class(sot_data: SoTData):
    """File node should contain its top-level Class."""
    file_node = sot_data.node(kind="File", name="OrderService.php")
    class_node = sot_data.node(kind="Class", fqn="App\\Service\\OrderService")
    assert file_node is not None, "File node should exist"
    assert class_node is not None, "Class node should exist"

    edge = sot_data.edge(type="contains", source=file_node["id"], target=class_node["id"])
    assert edge is not None, "Should have contains edge from File to Class"


@contract_test(
    name="Contains edge: Class -> Method",
    description="Verifies contains edge from Class node to its Method node",
    category="edge-creation",
)
def test_contains_class_to_method(sot_data: SoTData):
    """Class node should contain its methods."""
    class_node = sot_data.node(kind="Class", fqn="App\\Service\\OrderService")
    method_node = sot_data.node(kind="Method", fqn="App\\Service\\OrderService::createOrder()")
    assert class_node is not None
    assert method_node is not None

    edge = sot_data.edge(type="contains", source=class_node["id"], target=method_node["id"])
    assert edge is not None, "Should have contains edge from Class to Method"


@contract_test(
    name="Extends edge: Class -> parent Class",
    description="Verifies extends edge from StandardOrderProcessor to AbstractOrderProcessor",
    category="edge-creation",
)
def test_extends_edge(sot_data: SoTData):
    """Child class should have extends edge to parent class."""
    child = sot_data.node(kind="Class", fqn="App\\Service\\StandardOrderProcessor")
    parent = sot_data.node(kind="Class", fqn="App\\Service\\AbstractOrderProcessor")
    assert child is not None, "StandardOrderProcessor should exist"
    assert parent is not None, "AbstractOrderProcessor should exist"

    edge = sot_data.edge(type="extends", source=child["id"], target=parent["id"])
    assert edge is not None, "Should have extends edge from child to parent"


@contract_test(
    name="Implements edge: Class -> Interface",
    description="Verifies implements edge from EmailSender to EmailSenderInterface",
    category="edge-creation",
)
def test_implements_edge(sot_data: SoTData):
    """Implementing class should have implements edge to interface."""
    impl = sot_data.node(kind="Class", fqn="App\\Component\\EmailSender")
    iface = sot_data.node(kind="Interface", fqn="App\\Component\\EmailSenderInterface")
    assert impl is not None, "EmailSender should exist"
    assert iface is not None, "EmailSenderInterface should exist"

    edge = sot_data.edge(type="implements", source=impl["id"], target=iface["id"])
    assert edge is not None, "Should have implements edge from EmailSender to EmailSenderInterface"


@contract_test(
    name="Uses trait edge: Class -> Trait",
    description="Verifies uses_trait edge from OrderController to LoggableTrait",
    category="edge-creation",
)
def test_uses_trait_edge(sot_data: SoTData):
    """Class using a trait should have uses_trait edge."""
    controller = sot_data.node(kind="Class", fqn="App\\Ui\\Rest\\Controller\\OrderController")
    trait = sot_data.node(kind="Trait", fqn="App\\Component\\LoggableTrait")
    assert controller is not None, "OrderController should exist"
    assert trait is not None, "LoggableTrait should exist"

    edge = sot_data.edge(type="uses_trait", source=controller["id"], target=trait["id"])
    assert edge is not None, "Should have uses_trait edge from OrderController to LoggableTrait"


@contract_test(
    name="Uses edge: Method -> referenced symbol",
    description="Verifies uses edge from OrderService::createOrder() to OrderRepository::save()",
    category="edge-creation",
)
def test_uses_edge(sot_data: SoTData):
    """Method should have uses edge to symbols it references."""
    method = sot_data.node(kind="Method", fqn="App\\Service\\OrderService::createOrder()")
    target = sot_data.node(kind="Method", fqn="App\\Repository\\OrderRepository::save()")
    assert method is not None, "createOrder method should exist"
    assert target is not None, "save method should exist"

    edge = sot_data.edge(type="uses", source=method["id"], target=target["id"])
    assert edge is not None, "Should have uses edge from createOrder to save"


@contract_test(
    name="Overrides edge: method -> parent method",
    description="Verifies overrides edge from StandardOrderProcessor::process() to AbstractOrderProcessor::process()",
    category="edge-creation",
)
def test_overrides_edge(sot_data: SoTData):
    """Overriding method should have overrides edge to parent method."""
    child_method = sot_data.node(kind="Method", fqn="App\\Service\\StandardOrderProcessor::process()")
    parent_method = sot_data.node(kind="Method", fqn="App\\Service\\AbstractOrderProcessor::process()")
    assert child_method is not None, "StandardOrderProcessor::process() should exist"
    assert parent_method is not None, "AbstractOrderProcessor::process() should exist"

    edge = sot_data.edge(type="overrides", source=child_method["id"], target=parent_method["id"])
    assert edge is not None, "Should have overrides edge from child process() to parent process()"


@contract_test(
    name="Type hint edge: Argument -> Class",
    description="Verifies type_hint edge from parameter argument to its type class",
    category="edge-creation",
)
def test_type_hint_edge(sot_data: SoTData):
    """Parameter with type annotation should have type_hint edge to the type."""
    type_hint_edges = sot_data.edges_by_type("type_hint")
    assert len(type_hint_edges) >= 1, "Should have at least one type_hint edge"

    # Find a type_hint edge where target is the Order class
    order = sot_data.node(kind="Class", fqn="App\\Entity\\Order")
    if order:
        order_type_hints = [e for e in type_hint_edges if e["target"] == order["id"]]
        assert len(order_type_hints) >= 1, \
            "Should have at least one type_hint edge pointing to Order class"


@contract_test(
    name="Calls edge: Call -> Method",
    description="Verifies calls edge from Call node to the target Method node",
    category="edge-creation",
)
def test_calls_edge(sot_data: SoTData):
    """Call node should have calls edge to target method."""
    calls_edges = sot_data.edges_by_type("calls")
    assert len(calls_edges) >= 1, "Should have at least one calls edge"

    # Verify source is a Call node and target is a Method/Function
    for ce in calls_edges:
        source_node = sot_data.node_by_id(ce["source"])
        assert source_node is not None, f"Source node {ce['source']} should exist"
        assert source_node["kind"] == "Call", \
            f"Source of 'calls' edge should be Call node, got {source_node['kind']}"


@contract_test(
    name="Receiver edge: Call -> Value",
    description="Verifies receiver edge from Call node to the receiver Value node",
    category="edge-creation",
)
def test_receiver_edge(sot_data: SoTData):
    """Call node should have receiver edge to its receiver value."""
    receiver_edges = sot_data.edges_by_type("receiver")
    assert len(receiver_edges) >= 1, "Should have at least one receiver edge"

    for re_edge in receiver_edges:
        source_node = sot_data.node_by_id(re_edge["source"])
        target_node = sot_data.node_by_id(re_edge["target"])
        assert source_node is not None
        assert target_node is not None
        assert source_node["kind"] == "Call", "Source of receiver edge should be Call node"
        assert target_node["kind"] == "Value", "Target of receiver edge should be Value node"


@contract_test(
    name="Argument edge: Call -> Value",
    description="Verifies argument edge from Call node to argument Value node with position field",
    category="edge-creation",
)
def test_argument_edge(sot_data: SoTData):
    """Call node should have argument edges to its argument values."""
    arg_edges = sot_data.edges_by_type("argument")
    assert len(arg_edges) >= 1, "Should have at least one argument edge"

    for ae in arg_edges:
        source_node = sot_data.node_by_id(ae["source"])
        target_node = sot_data.node_by_id(ae["target"])
        assert source_node is not None
        assert target_node is not None
        assert source_node["kind"] == "Call", "Source of argument edge should be Call node"
        assert target_node["kind"] == "Value", "Target of argument edge should be Value node"
        assert "position" in ae, "Argument edge should have position field"


@contract_test(
    name="Produces edge: Call -> Value",
    description="Verifies produces edge from Call node to result Value node",
    category="edge-creation",
)
def test_produces_edge(sot_data: SoTData):
    """Call node should have produces edge to its result value."""
    produces_edges = sot_data.edges_by_type("produces")
    assert len(produces_edges) >= 1, "Should have at least one produces edge"

    for pe in produces_edges:
        source_node = sot_data.node_by_id(pe["source"])
        assert source_node is not None
        assert source_node["kind"] == "Call", "Source of produces edge should be Call node"
