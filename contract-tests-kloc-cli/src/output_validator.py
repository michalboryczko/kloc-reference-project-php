"""OutputValidator for kloc-cli contract tests.

Runs kloc-cli commands and validates JSON output.
Works against a sot.json fixture file on disk.
"""

import json
import os
import shutil
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

    Supports two execution modes:
    - Installed binary: uses 'kloc-cli' from PATH (preferred in Docker)
    - Python module: uses 'python -m src.cli' from kloc-cli directory (local dev)
    """

    def __init__(self, sot_path: str | Path, cli_dir: str | Path | None = None,
                 python_exe: str | None = None):
        """Initialize with path to sot.json fixture.

        Args:
            sot_path: Path to the sot.json file.
            cli_dir: Directory containing the CLI source (cwd for module mode).
            python_exe: Python executable to use for module mode.
        """
        self.sot_path = str(sot_path)
        self.cli_dir = str(cli_dir) if cli_dir else None
        self.python_exe = python_exe or sys.executable

        # Prefer installed binary; fall back to python -m src.cli
        self._use_binary = shutil.which("kloc-cli") is not None

    def _build_cmd(self, cmd: str, *args: str) -> list[str]:
        """Build the command list for subprocess."""
        if self._use_binary:
            return ["kloc-cli", cmd, "--sot", self.sot_path, *args]
        return [self.python_exe, "-m", "src.cli", cmd, "--sot", self.sot_path, *args]

    def _build_help_cmd(self, cmd: str = "") -> list[str]:
        """Build the --help command list."""
        if self._use_binary:
            if cmd:
                return ["kloc-cli", cmd, "--help"]
            return ["kloc-cli", "--help"]
        if cmd:
            return [self.python_exe, "-m", "src.cli", cmd, "--help"]
        return [self.python_exe, "-m", "src.cli", "--help"]

    def _run(self, cmd: str, *args: str, expect_error: bool = False) -> subprocess.CompletedProcess:
        """Run a kloc-cli command.

        Args:
            cmd: Command name (resolve, usages, deps, etc.)
            *args: Additional arguments
            expect_error: If True, don't raise on non-zero exit

        Returns:
            CompletedProcess result
        """
        full_cmd = self._build_cmd(cmd, *args)
        result = subprocess.run(
            full_cmd,
            capture_output=True,
            text=True,
            timeout=30,
            cwd=self.cli_dir if not self._use_binary else None,
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
        full_cmd = self._build_help_cmd(cmd)
        result = subprocess.run(
            full_cmd,
            capture_output=True,
            text=True,
            timeout=10,
            cwd=self.cli_dir if not self._use_binary else None,
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
        """Find an edge-like entry in result by matching criteria.

        kloc-cli outputs tree structures, not raw edges. This searches
        tree entries where the parent-child relationship implies an edge.
        The 'source' is matched against parent context, while 'target'
        is matched against the entry's FQN.

        Args:
            result: JSON result from kloc-cli
            source: Expected source FQN (substring match against parent or target context)
            target: Expected target FQN (substring match against entry fqn)
            edge_type: Expected edge type (matched against entry 'kind' or 'type' field)

        Returns:
            Matching entry dict or None
        """
        entries = _collect_entries(result)
        for entry in entries:
            if target and target not in entry.get("fqn", ""):
                continue
            if source and source not in entry.get("fqn", ""):
                # Also check if source matches the target context (for context results)
                target_fqn = result.get("target", {}).get("fqn", "")
                if source not in target_fqn:
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
