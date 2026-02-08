"""Smoke tests for kloc-cli.

Validates basic CLI operations: help text, JSON output, error handling.
"""

import json
import subprocess
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent))
from src.decorators import contract_test
from src.output_validator import OutputValidator, CliError


@contract_test(
    name="CLI --help produces output",
    description="Verifies that kloc-cli --help produces usage text without errors",
    category="smoke",
)
@pytest.mark.smoke
def test_help_produces_output(cli: OutputValidator):
    """--help should produce usage text."""
    help_text = cli.run_help()
    assert len(help_text) > 0
    assert "kloc-cli" in help_text.lower() or "usage" in help_text.lower()


@contract_test(
    name="resolve --help works",
    description="Verifies that kloc-cli resolve --help shows resolve command documentation",
    category="smoke",
)
@pytest.mark.smoke
def test_resolve_help(cli: OutputValidator):
    """resolve --help should show command documentation."""
    help_text = cli.run_help("resolve")
    assert "symbol" in help_text.lower() or "resolve" in help_text.lower()


@contract_test(
    name="usages --help works",
    description="Verifies that kloc-cli usages --help shows usages command documentation",
    category="smoke",
)
@pytest.mark.smoke
def test_usages_help(cli: OutputValidator):
    """usages --help should show command documentation."""
    help_text = cli.run_help("usages")
    assert "usage" in help_text.lower() or "symbol" in help_text.lower()


@contract_test(
    name="--json flag produces valid JSON",
    description="Verifies that the --json flag on resolve produces valid JSON output",
    category="smoke",
)
@pytest.mark.smoke
def test_json_output_valid(cli: OutputValidator):
    """--json should produce valid, parseable JSON."""
    result = cli.json_output("resolve", "App\\Entity\\Order")
    assert isinstance(result, dict)
    # Should have standard result fields
    assert "fqn" in result or "candidates" in result or "error" in result


def _make_validator(sot_path) -> OutputValidator:
    """Create an OutputValidator with the correct kloc-cli directory."""
    kloc_cli_dir = Path(__file__).parent.parent.parent.parent / "kloc-cli"
    if not kloc_cli_dir.exists():
        kloc_cli_dir = Path("/app/kloc-cli")
    venv_python = kloc_cli_dir / ".venv" / "bin" / "python"
    python_exe = str(venv_python) if venv_python.exists() else sys.executable
    return OutputValidator(sot_path=sot_path, cli_dir=str(kloc_cli_dir), python_exe=python_exe)


@contract_test(
    name="Missing sot file produces error",
    description="Verifies that pointing to a non-existent sot file produces an error, not a crash",
    category="smoke",
)
@pytest.mark.smoke
def test_missing_sot_error(tmp_path):
    """Missing sot file should produce a meaningful error, not a crash."""
    bad_path = tmp_path / "nonexistent.json"
    validator = _make_validator(bad_path)
    result = validator.run_raw("resolve", "Foo", expect_error=True)
    assert result.returncode != 0
    # Should mention the file not being found
    combined = result.stdout + result.stderr
    assert "not found" in combined.lower() or "error" in combined.lower()


@contract_test(
    name="Invalid sot JSON produces parse error",
    description="Verifies that a malformed sot.json file produces a parse error, not a crash",
    category="smoke",
)
@pytest.mark.smoke
def test_invalid_sot_json(tmp_path):
    """Malformed sot.json should produce a parse error."""
    bad_sot = tmp_path / "bad.json"
    bad_sot.write_text("{invalid json content")
    validator = _make_validator(bad_sot)
    result = validator.run_raw("resolve", "Foo", expect_error=True)
    assert result.returncode != 0
