"""Global fixtures for E2E integration tests.

Runs the full pipeline once per session:
  scip-php -> kloc-mapper -> sot.json

Provides the PipelineRunner as a fixture for all tests.
"""

import sys
from pathlib import Path

import pytest

# Add src to path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from pipeline_runner import PipelineRunner


@pytest.fixture(scope="session")
def kloc_root() -> Path:
    """Resolve the kloc monorepo root directory.

    Path hierarchy from this file:
      [0] = tests/
      [1] = contract-tests-e2e/
      [2] = kloc-reference-project-php/
      [3] = kloc/  (monorepo root)
    """
    root = Path(__file__).resolve().parents[3]
    assert (root / "kloc-mapper").exists(), f"kloc-mapper not found at {root / 'kloc-mapper'}"
    assert (root / "kloc-cli").exists(), f"kloc-cli not found at {root / 'kloc-cli'}"
    assert (root / "scip-php").exists(), f"scip-php not found at {root / 'scip-php'}"
    return root


@pytest.fixture(scope="session")
def reference_project() -> Path:
    """Resolve the reference PHP project directory.

    Path hierarchy: [0]=tests, [1]=contract-tests-e2e, [2]=kloc-reference-project-php
    """
    project = Path(__file__).resolve().parents[2]
    assert (project / "src").exists(), f"Reference project src/ not found at {project}"
    assert (project / "composer.json").exists(), f"composer.json not found at {project}"
    return project


@pytest.fixture(scope="session")
def pipeline(kloc_root, reference_project, tmp_path_factory) -> PipelineRunner:
    """Create and return the PipelineRunner (does not run the pipeline yet)."""
    output_dir = tmp_path_factory.mktemp("e2e_pipeline")
    return PipelineRunner(
        kloc_root=kloc_root,
        reference_project=reference_project,
        output_dir=output_dir,
    )


@pytest.fixture(scope="session")
def pipeline_result(pipeline) -> dict:
    """Run the full pipeline once and return the result summary.

    This is the main session fixture. It runs scip-php and kloc-mapper
    once, then all query tests use the same sot.json.
    """
    return pipeline.run_full_pipeline()


@pytest.fixture(scope="session")
def sot_data(pipeline) -> dict:
    """Return the sot.json dict after pipeline has run."""
    return pipeline.load_sot()


@pytest.fixture(scope="session")
def cli(pipeline, pipeline_result):
    """Provide a function to run kloc-cli queries.

    Usage in tests:
        result = cli("usages", "App\\Entity\\Order", "--depth", "1")
    """
    return pipeline.run_kloc_cli
