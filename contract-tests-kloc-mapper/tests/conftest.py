"""Global fixtures for kloc-mapper contract tests.

Generates a realistic .kloc archive once and runs kloc-mapper to produce sot.json.
The SoTData wrapper is shared across all integration tests.
"""

import json
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

# Add src to path for fixture_generator, sot_data, decorators
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from fixture_generator import (
    KlocFixtureBuilder, build_full_fixture, build_minimal_fixture,
    DocumentDef, SymbolDef, OccurrenceDef, ValueDef, CallDef, CallArgDef,
    php_class_symbol, php_interface_symbol, php_trait_symbol, php_enum_symbol,
    php_method_symbol, php_property_symbol, php_const_symbol,
    php_enum_case_symbol, php_argument_symbol, php_function_symbol,
    ROLE_DEFINITION, ROLE_REFERENCE,
)
from sot_data import SoTData


def run_kloc_mapper(kloc_path: Path, output_path: Path) -> dict:
    """Run kloc-mapper on a .kloc archive and return parsed sot.json.

    Tries multiple strategies:
    1. kloc-mapper binary in PATH
    2. Python module invocation via kloc-mapper source
    """
    # parents[0]=tests, [1]=contract-tests-kloc-mapper, [2]=kloc-reference-project-php, [3]=kloc
    kloc_mapper_dir = Path(__file__).resolve().parents[3] / "kloc-mapper"

    # Strategy: Run as Python module
    cmd = [
        sys.executable, "-m", "src.cli",
        "map", str(kloc_path),
        "-o", str(output_path),
        "--pretty",
    ]

    result = subprocess.run(
        cmd,
        cwd=str(kloc_mapper_dir),
        capture_output=True,
        text=True,
        timeout=30,
    )

    if result.returncode != 0:
        raise RuntimeError(
            f"kloc-mapper failed (exit {result.returncode}):\n"
            f"stdout: {result.stdout}\n"
            f"stderr: {result.stderr}"
        )

    with open(output_path) as f:
        return json.load(f)


@pytest.fixture(scope="session")
def full_kloc_path(tmp_path_factory) -> Path:
    """Generate the full .kloc fixture archive once per session."""
    tmp = tmp_path_factory.mktemp("fixtures")
    builder = build_full_fixture()
    return builder.build(tmp / "full.kloc")


@pytest.fixture(scope="session")
def full_sot_json(full_kloc_path, tmp_path_factory) -> dict:
    """Run kloc-mapper on the full fixture and return raw sot.json dict."""
    tmp = tmp_path_factory.mktemp("output")
    output_path = tmp / "sot.json"
    return run_kloc_mapper(full_kloc_path, output_path)


@pytest.fixture(scope="session")
def sot_data(full_sot_json) -> SoTData:
    """SoTData query helper wrapping the full fixture output."""
    return SoTData.from_dict(full_sot_json)


@pytest.fixture(scope="session")
def minimal_kloc_path(tmp_path_factory) -> Path:
    """Generate a minimal .kloc fixture archive."""
    tmp = tmp_path_factory.mktemp("fixtures_minimal")
    builder = build_minimal_fixture()
    return builder.build(tmp / "minimal.kloc")


@pytest.fixture(scope="session")
def minimal_sot_json(minimal_kloc_path, tmp_path_factory) -> dict:
    """Run kloc-mapper on the minimal fixture."""
    tmp = tmp_path_factory.mktemp("output_minimal")
    output_path = tmp / "sot.json"
    return run_kloc_mapper(minimal_kloc_path, output_path)


@pytest.fixture(scope="session")
def minimal_sot(minimal_sot_json) -> SoTData:
    """SoTData query helper wrapping the minimal fixture output."""
    return SoTData.from_dict(minimal_sot_json)


# Re-export helpers for per-test fixture creation in test files
@pytest.fixture
def fixture_builder():
    """Fresh KlocFixtureBuilder for per-test fixtures."""
    return KlocFixtureBuilder()


@pytest.fixture
def run_mapper(tmp_path):
    """Helper to run kloc-mapper on a custom .kloc and return SoTData."""
    def _run(builder: KlocFixtureBuilder) -> SoTData:
        kloc_path = builder.build(tmp_path / "test.kloc")
        output_path = tmp_path / "sot.json"
        data = run_kloc_mapper(kloc_path, output_path)
        return SoTData.from_dict(data)
    return _run
