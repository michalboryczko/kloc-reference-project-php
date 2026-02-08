"""OutputValidator for kloc-cli contract tests.

Runs kloc-cli commands and validates JSON output.
Works against a sot.json fixture file on disk.
"""

import json
import subprocess
import sys
from pathlib import Path


class CliError(Exception):
    """Raised when kloc-cli exits with non-zero status."""

    def __init__(self, returncode: int, stderr: str, cmd: list[str]):
        self.returncode = returncode
        self.stderr = stderr
        self.cmd = cmd
        super().__init__(f"kloc-cli exited with code {returncode}: {stderr}")


class OutputValidator:
    """Runs kloc-cli commands and validates JSON output.

    Uses the Python module directly (python -m src.cli) to avoid
    requiring a compiled binary. Runs from the kloc-cli directory
    so module resolution works.
    """

    def __init__(self, sot_path: str | Path, cli_module: str = "src.cli",
                 cli_dir: str | Path | None = None, python_exe: str | None = None):
        """Initialize with path to sot.json fixture.

        Args:
            sot_path: Path to the sot.json file.
            cli_module: Python module path for the CLI (default: src.cli).
            cli_dir: Directory containing the CLI module (cwd for subprocess).
            python_exe: Python executable to use (default: same as current).
        """
        self.sot_path = str(sot_path)
        self.cli_module = cli_module
        self.cli_dir = str(cli_dir) if cli_dir else None
        self.python_exe = python_exe or sys.executable

    def _run(self, cmd: str, *args: str, expect_error: bool = False) -> subprocess.CompletedProcess:
        """Run a kloc-cli command.

        Args:
            cmd: Command name (resolve, usages, deps, etc.)
            *args: Additional arguments
            expect_error: If True, don't raise on non-zero exit

        Returns:
            CompletedProcess result
        """
        full_cmd = [
            self.python_exe, "-m", self.cli_module,
            cmd,
            "--sot", self.sot_path,
            *args,
        ]
        result = subprocess.run(
            full_cmd,
            capture_output=True,
            text=True,
            timeout=30,
            cwd=self.cli_dir,
        )
        if not expect_error and result.returncode != 0:
            raise CliError(result.returncode, result.stderr, full_cmd)
        return result

    def json_output(self, cmd: str, *args: str) -> dict:
        """Run a command with --json flag and return parsed JSON.

        Args:
            cmd: Command name
            *args: Additional arguments (--json is added automatically)

        Returns:
            Parsed JSON dict
        """
        result = self._run(cmd, "--json", *args)
        return json.loads(result.stdout)

    def json_output_allow_error(self, cmd: str, *args: str) -> tuple[dict | None, int]:
        """Run a command with --json, allowing non-zero exit.

        Returns:
            Tuple of (parsed JSON or None, return code)
        """
        result = self._run(cmd, "--json", *args, expect_error=True)
        try:
            data = json.loads(result.stdout)
        except (json.JSONDecodeError, ValueError):
            data = None
        return data, result.returncode

    def run_help(self, cmd: str = "") -> str:
        """Run --help for a command (or the root CLI).

        Returns:
            Help text (stdout + stderr since typer writes help to stdout)
        """
        if cmd:
            full_cmd = [self.python_exe, "-m", self.cli_module, cmd, "--help"]
        else:
            full_cmd = [self.python_exe, "-m", self.cli_module, "--help"]
        result = subprocess.run(
            full_cmd, capture_output=True, text=True, timeout=10, cwd=self.cli_dir
        )
        return result.stdout + result.stderr

    def run_raw(self, cmd: str, *args: str, expect_error: bool = False) -> subprocess.CompletedProcess:
        """Run a command and return raw result without parsing.

        Args:
            cmd: Command name
            *args: Additional arguments
            expect_error: If True, don't raise on non-zero exit

        Returns:
            CompletedProcess with stdout/stderr
        """
        return self._run(cmd, *args, expect_error=expect_error)

    @staticmethod
    def expect_node(result: dict, fqn: str | None = None, kind: str | None = None,
                    file: str | None = None) -> dict | None:
        """Find a node in a result dict by matching criteria.

        Searches in various result structures (tree entries, chain items, etc.)

        Args:
            result: JSON result from kloc-cli
            fqn: Expected FQN (substring match)
            kind: Expected kind
            file: Expected file

        Returns:
            Matching entry dict or None
        """
        entries = _collect_entries(result)
        for entry in entries:
            if fqn and fqn not in entry.get("fqn", ""):
                continue
            if kind and entry.get("kind") != kind:
                continue
            if file and entry.get("file") != file:
                continue
            return entry
        return None

    @staticmethod
    def expect_edge(result: dict, source: str | None = None, target: str | None = None,
                    edge_type: str | None = None) -> dict | None:
        """Find an edge in result by matching criteria.

        Searches in tree children/used_by/uses entries for edge-like patterns.

        Args:
            result: JSON result from kloc-cli
            source: Expected source FQN (substring)
            target: Expected target FQN (substring)
            edge_type: Expected edge type

        Returns:
            Matching entry dict or None
        """
        entries = _collect_entries(result)
        for entry in entries:
            if target and target not in entry.get("fqn", ""):
                continue
            if edge_type and entry.get("type") != edge_type:
                continue
            return entry
        return None

    @staticmethod
    def expect_tree_depth(result: dict, depth: int) -> bool:
        """Assert result tree has entries at the given depth.

        Args:
            result: JSON result from kloc-cli
            depth: Expected depth level

        Returns:
            True if entries exist at that depth
        """
        entries = _collect_entries(result)
        return any(e.get("depth") == depth for e in entries)

    @staticmethod
    def expect_count(result: dict, count: int) -> bool:
        """Assert result has expected total count.

        Args:
            result: JSON result from kloc-cli
            count: Expected count

        Returns:
            True if total matches
        """
        total = result.get("total")
        if total is not None:
            return total == count

        # For owners, count chain length
        chain = result.get("chain")
        if chain is not None:
            return len(chain) == count

        # For context, count combined entries
        used_by = result.get("used_by", [])
        uses = result.get("uses", [])
        return (len(used_by) + len(uses)) == count


def _collect_entries(result: dict) -> list[dict]:
    """Collect all entry-like dicts from a result structure.

    Handles various kloc-cli output formats:
    - tree: [{depth, fqn, children}, ...]
    - chain: [{kind, fqn, file, line}, ...]
    - used_by / uses: [{depth, fqn, children}, ...]
    - Direct node: {fqn, kind, file, ...}
    """
    entries = []

    # Single node result (resolve)
    if "fqn" in result and "kind" in result:
        entries.append(result)
        return entries

    # Candidates list (resolve with multiple)
    if "candidates" in result:
        entries.extend(result["candidates"])
        return entries

    # Tree results (usages, deps, inherit, overrides)
    if "tree" in result:
        _collect_tree(result["tree"], entries)

    # Ownership chain
    if "chain" in result:
        entries.extend(result["chain"])

    # Context results (used_by + uses)
    if "used_by" in result:
        _collect_tree(result["used_by"], entries)
    if "uses" in result:
        _collect_tree(result["uses"], entries)

    return entries


def _collect_tree(tree: list[dict], entries: list[dict]) -> None:
    """Recursively collect entries from a tree structure."""
    for item in tree:
        entries.append(item)
        if "children" in item:
            _collect_tree(item["children"], entries)
        if "implementations" in item:
            _collect_tree(item["implementations"], entries)
