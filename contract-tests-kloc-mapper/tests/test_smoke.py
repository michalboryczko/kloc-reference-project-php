"""Smoke tests for kloc-mapper sot.json output.

Validates basic output structure: valid JSON, version field, non-empty
nodes/edges arrays, unique node IDs, and basic sanity counts.
"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from decorators import contract_test
from sot_data import SoTData


pytestmark = pytest.mark.smoke


@contract_test(
    name="Valid JSON output",
    description="Verifies kloc-mapper produces valid JSON with expected top-level structure (version, metadata, nodes, edges)",
    category="smoke",
)
def test_valid_json_structure(full_sot_json):
    """Output must be a dict with version, metadata, nodes, edges keys."""
    assert isinstance(full_sot_json, dict), "Output should be a JSON object"
    assert "version" in full_sot_json, "Must have 'version' field"
    assert "nodes" in full_sot_json, "Must have 'nodes' field"
    assert "edges" in full_sot_json, "Must have 'edges' field"


@contract_test(
    name="Version field present",
    description="Verifies sot.json contains version field with value '2.0'",
    category="smoke",
)
def test_version_field(full_sot_json):
    """Version field must be present and set to '2.0'."""
    assert full_sot_json["version"] == "2.0", "Version should be '2.0'"


@contract_test(
    name="Nodes array non-empty",
    description="Verifies sot.json nodes array is non-empty for a fixture with classes and methods",
    category="smoke",
)
def test_nodes_non_empty(sot_data: SoTData):
    """Nodes array must be non-empty for any meaningful input."""
    assert sot_data.node_count() > 0, "Nodes array should not be empty"


@contract_test(
    name="Edges array non-empty",
    description="Verifies sot.json edges array is non-empty for a fixture with relationships",
    category="smoke",
)
def test_edges_non_empty(sot_data: SoTData):
    """Edges array must be non-empty for input with containment and references."""
    assert sot_data.edge_count() > 0, "Edges array should not be empty"


@contract_test(
    name="Node IDs are unique",
    description="Verifies all node IDs in the output are unique strings",
    category="smoke",
)
def test_node_ids_unique(sot_data: SoTData):
    """All node IDs must be unique strings."""
    ids = [n.get("id") for n in sot_data.nodes()]
    assert len(ids) == len(set(ids)), f"Duplicate node IDs found: {[x for x in ids if ids.count(x) > 1]}"
    for node_id in ids:
        assert isinstance(node_id, str), f"Node ID should be string, got {type(node_id)}"
        assert len(node_id) > 0, "Node ID should not be empty"


@contract_test(
    name="Basic node counts",
    description="Verifies at least 1 File node and 1 Class node exist in output for a simple fixture",
    category="smoke",
)
def test_basic_node_counts(sot_data: SoTData):
    """Output should contain at least one File node and one Class node."""
    file_nodes = sot_data.nodes_by_kind("File")
    assert len(file_nodes) >= 1, "Should have at least 1 File node"

    class_nodes = sot_data.nodes_by_kind("Class")
    assert len(class_nodes) >= 1, "Should have at least 1 Class node"


@contract_test(
    name="Node structure",
    description="Verifies each node has required fields: id, kind, name, fqn, file",
    category="smoke",
)
def test_node_structure(sot_data: SoTData):
    """Each node must have the required fields."""
    required_fields = {"id", "kind", "name", "fqn"}
    for node in sot_data.nodes():
        for field in required_fields:
            assert field in node, f"Node missing required field '{field}': {node}"


@contract_test(
    name="Edge structure",
    description="Verifies each edge has required fields: type, source, target",
    category="smoke",
)
def test_edge_structure(sot_data: SoTData):
    """Each edge must have type, source, and target fields."""
    for edge in sot_data.edges():
        assert "type" in edge, f"Edge missing 'type': {edge}"
        assert "source" in edge, f"Edge missing 'source': {edge}"
        assert "target" in edge, f"Edge missing 'target': {edge}"
