"""Integrity tests for kloc-mapper output.

Validates structural integrity:
- All node IDs unique
- All edge source/target point to existing nodes
- No orphan nodes (every non-File node reachable from some edge)
- Deterministic output (same input -> same output)
- No duplicate edges (same source+target+type)
"""

import json
import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from decorators import contract_test
from sot_data import SoTData


pytestmark = pytest.mark.integrity


@contract_test(
    name="All node IDs unique",
    description="Verifies every node in sot.json has a unique ID string",
    category="integrity",
)
def test_all_node_ids_unique(sot_data: SoTData):
    """Every node must have a unique ID."""
    ids = [n["id"] for n in sot_data.nodes()]
    duplicates = [x for x in ids if ids.count(x) > 1]
    assert len(ids) == len(set(ids)), f"Duplicate node IDs found: {set(duplicates)}"


@contract_test(
    name="All edge targets valid",
    description="Verifies all edge source and target IDs point to existing nodes",
    category="integrity",
)
def test_all_edge_references_valid(sot_data: SoTData):
    """Every edge source and target must reference an existing node."""
    valid_ids = sot_data.node_ids()

    for edge in sot_data.edges():
        source = edge["source"]
        target = edge["target"]
        assert source in valid_ids, \
            f"Edge source '{source}' not found in nodes (type={edge['type']})"
        assert target in valid_ids, \
            f"Edge target '{target}' not found in nodes (type={edge['type']})"


@contract_test(
    name="No orphan structural nodes",
    description="Verifies every structural node (non-File, non-Value) is reachable via at least one edge",
    category="integrity",
)
def test_no_orphan_nodes(sot_data: SoTData):
    """Every structural node should participate in at least one edge.

    Value nodes may be standalone (e.g., literals, constants without type symbols
    or enclosing scope info), so they are excluded from orphan checks.
    File nodes are always edge sources (contain), not targets.
    """
    # Collect all node IDs that appear in edges
    edge_participants = set()
    for edge in sot_data.edges():
        edge_participants.add(edge["source"])
        edge_participants.add(edge["target"])

    # Check structural nodes (exclude File and Value nodes)
    # Value nodes may be standalone (literals/constants without edges)
    orphans = []
    for node in sot_data.nodes():
        if node["kind"] in ("File", "Value"):
            continue
        if node["id"] not in edge_participants:
            orphans.append(f"{node['kind']}:{node.get('fqn', node.get('name', ''))}")

    assert len(orphans) == 0, f"Orphan structural nodes found (not connected to any edge): {orphans}"


@contract_test(
    name="No duplicate edges",
    description="Verifies no two edges have the same (source, target, type) triple",
    category="integrity",
)
def test_no_duplicate_edges(sot_data: SoTData):
    """No two edges should have the same source+target+type."""
    seen = set()
    duplicates = []
    for edge in sot_data.edges():
        key = (edge["source"], edge["target"], edge["type"])
        if key in seen:
            duplicates.append(key)
        seen.add(key)

    assert len(duplicates) == 0, \
        f"Duplicate edges found: {len(duplicates)} duplicates"


@contract_test(
    name="Deterministic output",
    description="Verifies same input produces identical sot.json output (same input twice -> same output)",
    category="integrity",
)
def test_deterministic_output(full_kloc_path, run_mapper, tmp_path):
    """Running kloc-mapper twice on the same input should produce identical output."""
    import subprocess
    from pathlib import Path

    # parents: [0]=tests, [1]=contract-tests-kloc-mapper, [2]=kloc-reference-project-php, [3]=kloc
    kloc_mapper_dir = Path(__file__).resolve().parents[3] / "kloc-mapper"

    output1 = tmp_path / "sot1.json"
    output2 = tmp_path / "sot2.json"

    for output_path in (output1, output2):
        cmd = [
            sys.executable, "-m", "src.cli",
            "map", str(full_kloc_path),
            "-o", str(output_path),
            "--pretty",
        ]
        result = subprocess.run(cmd, cwd=str(kloc_mapper_dir), capture_output=True, text=True, timeout=30)
        assert result.returncode == 0, f"kloc-mapper failed: {result.stderr}"

    data1 = json.loads(output1.read_text())
    data2 = json.loads(output2.read_text())

    # Compare sorted JSON for equality (ignore metadata.generated_at timestamp)
    data1.get("metadata", {}).pop("generated_at", None)
    data2.get("metadata", {}).pop("generated_at", None)

    json1 = json.dumps(data1, sort_keys=True)
    json2 = json.dumps(data2, sort_keys=True)

    assert json1 == json2, "Same input should produce identical output"


@contract_test(
    name="Edge types are valid",
    description="Verifies all edge types in the output are from the known EdgeType enum",
    category="integrity",
)
def test_valid_edge_types(sot_data: SoTData):
    """All edge types must be from the known set."""
    valid_types = {
        "contains", "extends", "implements", "uses_trait", "overrides",
        "uses", "type_hint", "calls", "receiver", "argument",
        "produces", "assigned_from", "type_of",
    }
    for edge in sot_data.edges():
        assert edge["type"] in valid_types, \
            f"Unknown edge type: {edge['type']}"


@contract_test(
    name="Node kinds are valid",
    description="Verifies all node kinds in the output are from the known NodeKind enum",
    category="integrity",
)
def test_valid_node_kinds(sot_data: SoTData):
    """All node kinds must be from the known set."""
    valid_kinds = {
        "File", "Class", "Interface", "Trait", "Enum",
        "Method", "Function", "Property", "Const",
        "Argument", "EnumCase", "Value", "Call",
    }
    for node in sot_data.nodes():
        assert node["kind"] in valid_kinds, \
            f"Unknown node kind: {node['kind']}"
