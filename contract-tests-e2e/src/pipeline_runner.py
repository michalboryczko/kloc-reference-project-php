"""Pipeline runner for E2E integration tests.

Orchestrates the full kloc pipeline:
  1. scip-php: PHP project -> .kloc archive (index.scip + calls.json)
  2. kloc-mapper: .kloc archive -> sot.json
  3. kloc-cli: sot.json -> query results

Supports two execution modes:
  - Docker: Uses scip-php Docker image + installed binaries for mapper/cli
  - Local: Uses scip-php Docker image + venv binaries for mapper/cli

Artifacts (.kloc and sot.json) are saved for inspection and snapshot capture.
"""

import json
import shutil
import subprocess
import sys
from pathlib import Path


class PipelineError(Exception):
    """Raised when a pipeline stage fails."""

    def __init__(self, stage: str, returncode: int, stderr: str, cmd: list[str]):
        self.stage = stage
        self.returncode = returncode
        self.stderr = stderr
        self.cmd = cmd
        super().__init__(
            f"Pipeline stage '{stage}' failed (exit {returncode}):\n"
            f"  cmd: {' '.join(cmd)}\n"
            f"  stderr: {stderr[:500]}"
        )


class PipelineRunner:
    """Orchestrates the full kloc pipeline for E2E testing.

    Args:
        kloc_root: Path to the kloc monorepo root.
        reference_project: Path to the PHP reference project.
        output_dir: Directory for pipeline artifacts.
    """

    def __init__(
        self,
        kloc_root: Path,
        reference_project: Path,
        output_dir: Path,
    ):
        self.kloc_root = kloc_root
        self.reference_project = reference_project
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

        # Artifact paths
        self.kloc_path = self.output_dir / "index.kloc"
        self.scip_path = self.output_dir / "index.scip"
        self.calls_path = self.output_dir / "calls.json"
        self.sot_path = self.output_dir / "sot.json"

        # Resolved tool paths
        self._kloc_mapper_dir = self.kloc_root / "kloc-mapper"
        self._kloc_cli_dir = self.kloc_root / "kloc-cli"
        self._scip_php_dir = self.kloc_root / "scip-php"

    def run_scip_php(self, experimental: bool = False) -> Path:
        """Run scip-php indexer on the reference project.

        Uses the scip-php Docker image. Produces index.scip, calls.json,
        and index.kloc in the output directory.

        Returns:
            Path to the .kloc archive.
        """
        scip_php_sh = self._scip_php_dir / "bin" / "scip-php.sh"

        cmd = [
            str(scip_php_sh),
            "-d", str(self.reference_project),
            "-o", str(self.output_dir),
        ]
        if experimental:
            cmd.append("--experimental")

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            timeout=120,
        )

        if result.returncode != 0:
            raise PipelineError("scip-php", result.returncode, result.stderr, cmd)

        if not self.kloc_path.exists():
            raise PipelineError(
                "scip-php", 1,
                f".kloc archive not found at {self.kloc_path}. "
                f"Files in output: {list(self.output_dir.iterdir())}",
                cmd,
            )

        return self.kloc_path

    def run_kloc_mapper(self, kloc_path: Path | None = None) -> Path:
        """Run kloc-mapper on a .kloc archive.

        Args:
            kloc_path: Path to .kloc archive. Defaults to self.kloc_path.

        Returns:
            Path to the generated sot.json.
        """
        kloc_path = kloc_path or self.kloc_path
        python_exe = self._find_python(self._kloc_mapper_dir)

        cmd = [
            python_exe, "-m", "src.cli",
            "map", str(kloc_path),
            "-o", str(self.sot_path),
            "--pretty",
        ]

        result = subprocess.run(
            cmd,
            cwd=str(self._kloc_mapper_dir),
            capture_output=True,
            text=True,
            timeout=60,
        )

        if result.returncode != 0:
            raise PipelineError("kloc-mapper", result.returncode, result.stderr, cmd)

        if not self.sot_path.exists():
            raise PipelineError(
                "kloc-mapper", 1,
                f"sot.json not found at {self.sot_path}",
                cmd,
            )

        return self.sot_path

    def run_kloc_cli(self, command: str, *args: str) -> dict:
        """Run a kloc-cli query command and return parsed JSON output.

        Args:
            command: CLI command (resolve, usages, deps, inherit, context, overrides, owners).
            *args: Additional arguments.

        Returns:
            Parsed JSON dict from kloc-cli output.
        """
        python_exe = self._find_python(self._kloc_cli_dir)

        cmd = [
            python_exe, "-m", "src.cli",
            command, "--sot", str(self.sot_path), "--json",
            *args,
        ]

        result = subprocess.run(
            cmd,
            cwd=str(self._kloc_cli_dir),
            capture_output=True,
            text=True,
            timeout=30,
        )

        if result.returncode != 0:
            raise PipelineError("kloc-cli", result.returncode, result.stderr, cmd)

        return json.loads(result.stdout)

    def run_full_pipeline(self, experimental: bool = False) -> dict:
        """Run the complete pipeline: scip-php -> kloc-mapper -> kloc-cli resolve.

        Returns:
            Dict with paths and basic validation info.
        """
        kloc_path = self.run_scip_php(experimental=experimental)
        sot_path = self.run_kloc_mapper(kloc_path)

        # Load sot.json for validation
        with open(sot_path) as f:
            sot_data = json.load(f)

        return {
            "kloc_path": str(kloc_path),
            "sot_path": str(sot_path),
            "node_count": len(sot_data.get("nodes", [])),
            "edge_count": len(sot_data.get("edges", [])),
            "version": sot_data.get("version"),
        }

    def load_sot(self) -> dict:
        """Load and return the sot.json data."""
        with open(self.sot_path) as f:
            return json.load(f)

    def _find_python(self, project_dir: Path) -> str:
        """Find the best Python executable for a project.

        Checks for:
        1. Project's .venv/bin/python (local dev)
        2. System python (Docker)
        """
        venv_python = project_dir / ".venv" / "bin" / "python"
        if venv_python.exists():
            return str(venv_python)
        return sys.executable
