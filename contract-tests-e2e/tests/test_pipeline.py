"""Pipeline smoke tests.

Validates the full pipeline runs successfully:
- scip-php produces a .kloc archive
- kloc-mapper produces a sot.json with expected structure
- kloc-cli resolves a known symbol from the reference project
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from decorators import contract_test
from pipeline_runner import PipelineRunner


pytestmark = pytest.mark.pipeline


@contract_test(
    name="Pipeline produces .kloc archive",
    description="Verifies scip-php produces a .kloc archive from the reference PHP project",
    category="pipeline",
)
def test_scip_php_produces_kloc(pipeline_result):
    """scip-php should produce a .kloc archive."""
    kloc_path = Path(pipeline_result["kloc_path"])
    assert kloc_path.exists(), f".kloc archive not found at {kloc_path}"
    assert kloc_path.stat().st_size > 0, ".kloc archive is empty"


@contract_test(
    name="Pipeline produces sot.json",
    description="Verifies kloc-mapper produces a valid sot.json from the .kloc archive",
    category="pipeline",
)
def test_kloc_mapper_produces_sot(pipeline_result):
    """kloc-mapper should produce a sot.json."""
    sot_path = Path(pipeline_result["sot_path"])
    assert sot_path.exists(), f"sot.json not found at {sot_path}"
    assert sot_path.stat().st_size > 0, "sot.json is empty"


@contract_test(
    name="sot.json has correct version",
    description="Verifies the sot.json output has version 2.0",
    category="pipeline",
)
def test_sot_version(pipeline_result):
    """sot.json should have version 2.0."""
    assert pipeline_result["version"] == "2.0", (
        f"Expected version 2.0, got {pipeline_result['version']}"
    )


@contract_test(
    name="sot.json has nodes",
    description="Verifies the sot.json output contains a non-empty list of nodes",
    category="pipeline",
)
def test_sot_has_nodes(pipeline_result):
    """sot.json should contain nodes."""
    assert pipeline_result["node_count"] > 0, "sot.json has no nodes"


@contract_test(
    name="sot.json has edges",
    description="Verifies the sot.json output contains a non-empty list of edges",
    category="pipeline",
)
def test_sot_has_edges(pipeline_result):
    """sot.json should contain edges."""
    assert pipeline_result["edge_count"] > 0, "sot.json has no edges"


@contract_test(
    name="kloc-cli resolves known symbol",
    description="Verifies kloc-cli can resolve App\\Entity\\Order from the real pipeline output",
    category="pipeline",
)
def test_cli_resolves_known_symbol(cli):
    """kloc-cli should resolve a known symbol from the reference project."""
    result = cli("resolve", "App\\Entity\\Order")
    assert result["fqn"] == "App\\Entity\\Order", (
        f"Expected App\\Entity\\Order, got {result.get('fqn')}"
    )
    assert result["kind"] == "Class", (
        f"Expected Class, got {result.get('kind')}"
    )


@contract_test(
    name="kloc-cli resolves OrderService",
    description="Verifies kloc-cli can resolve App\\Service\\OrderService from the real pipeline output",
    category="pipeline",
)
def test_cli_resolves_order_service(cli):
    """kloc-cli should resolve OrderService."""
    result = cli("resolve", "App\\Service\\OrderService")
    assert result["fqn"] == "App\\Service\\OrderService"
    assert result["kind"] == "Class"
    assert result["file"] == "src/Service/OrderService.php"


@contract_test(
    name="sot.json node kinds match expected set",
    description="Verifies the sot.json contains the expected diversity of node kinds from a real PHP project",
    category="pipeline",
)
def test_sot_node_kinds(sot_data):
    """sot.json should contain diverse node kinds."""
    kinds = {n["kind"] for n in sot_data["nodes"]}
    # At minimum, a real PHP project should produce these structural kinds
    expected = {"File", "Class", "Method", "Property"}
    missing = expected - kinds
    assert len(missing) == 0, f"Missing expected node kinds: {missing}. Got: {kinds}"
