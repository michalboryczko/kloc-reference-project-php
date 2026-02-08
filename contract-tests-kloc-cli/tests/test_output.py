"""Output format contract tests.

Validates JSON output structure, required fields, and tree depth accuracy
across kloc-cli commands.
"""

import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))
from src.decorators import contract_test
from src.output_validator import OutputValidator


@contract_test(
    name="Usages JSON has required top-level fields",
    description="Verifies that usages --json output contains target, max_depth, total, and tree fields",
    category="output",
)
@pytest.mark.output
def test_usages_json_structure(cli: OutputValidator):
    """Usages JSON must contain target, max_depth, total, tree."""
    result = cli.json_output("usages", "App\\Entity\\Order", "--depth", "1")

    assert "target" in result, "Missing 'target' field"
    assert "max_depth" in result, "Missing 'max_depth' field"
    assert "total" in result, "Missing 'total' field"
    assert "tree" in result, "Missing 'tree' field"

    # target should have fqn
    assert "fqn" in result["target"], "target missing 'fqn'"

    # tree entries should have depth, fqn, file, line
    for entry in result["tree"]:
        assert "depth" in entry, f"Tree entry missing 'depth': {entry}"
        assert "fqn" in entry, f"Tree entry missing 'fqn': {entry}"
        assert "file" in entry, f"Tree entry missing 'file': {entry}"


@contract_test(
    name="Tree depth values match requested depth",
    description="Verifies that tree entries have correct depth values (1-based) matching the requested max_depth",
    category="output",
)
@pytest.mark.output
def test_tree_depth_values_accurate(cli: OutputValidator):
    """Tree entry depth values must be within requested range."""
    max_depth = 2
    result = cli.json_output(
        "usages", "App\\Entity\\Order", "--depth", str(max_depth)
    )

    def check_depths(entries, max_d):
        for entry in entries:
            assert 1 <= entry["depth"] <= max_d, (
                f"Entry depth {entry['depth']} outside range [1, {max_d}]: {entry['fqn']}"
            )
            if entry.get("children"):
                check_depths(entry["children"], max_d)

    check_depths(result["tree"], max_depth)


@contract_test(
    name="Context JSON has used_by and uses sections",
    description="Verifies that context --json output has target, used_by, and uses fields with correct entry structure",
    category="output",
)
@pytest.mark.output
def test_context_json_structure(cli: OutputValidator):
    """Context JSON must have target, used_by, uses with proper entry structure."""
    result = cli.json_output(
        "context", "App\\Service\\OrderService", "--depth", "1"
    )

    assert "target" in result, "Missing 'target' field"
    assert "used_by" in result, "Missing 'used_by' field"
    assert "uses" in result, "Missing 'uses' field"
    assert isinstance(result["used_by"], list), "'used_by' should be a list"
    assert isinstance(result["uses"], list), "'uses' should be a list"

    # Verify entry structure in both sections
    for section_name in ("used_by", "uses"):
        for entry in result[section_name]:
            assert "fqn" in entry, f"{section_name} entry missing 'fqn': {entry}"
            assert "depth" in entry, f"{section_name} entry missing 'depth': {entry}"
