"""SoTData query helper for kloc-mapper contract tests.

Immutable wrapper around parsed sot.json with indexed lookups.
Follows the same pattern as CallsData.php in the scip-php contract tests.
"""

import json
from pathlib import Path
from typing import Optional


class SoTData:
    """Immutable wrapper around parsed sot.json with indexed lookups."""

    def __init__(self, data: dict):
        self._data = data
        self._version = data.get("version", "")
        self._metadata = data.get("metadata", {})
        self._nodes: list[dict] = data.get("nodes", [])
        self._edges: list[dict] = data.get("edges", [])

        # Build indices
        self._nodes_by_id: dict[str, dict] = {}
        self._nodes_by_kind: dict[str, list[dict]] = {}
        self._nodes_by_fqn: dict[str, dict] = {}
        self._edges_by_type: dict[str, list[dict]] = {}

        for node in self._nodes:
            node_id = node.get("id", "")
            kind = node.get("kind", "")
            fqn = node.get("fqn", "")

            self._nodes_by_id[node_id] = node
            self._nodes_by_kind.setdefault(kind, []).append(node)
            if fqn:
                self._nodes_by_fqn[fqn] = node

        for edge in self._edges:
            edge_type = edge.get("type", "")
            self._edges_by_type.setdefault(edge_type, []).append(edge)

    @classmethod
    def load(cls, path: str | Path) -> "SoTData":
        """Load SoTData from a JSON file."""
        path = Path(path)
        if not path.exists():
            raise FileNotFoundError(f"sot.json not found at: {path}")

        with open(path) as f:
            data = json.load(f)

        return cls(data)

    @classmethod
    def from_dict(cls, data: dict) -> "SoTData":
        """Create SoTData from a parsed dict."""
        return cls(data)

    @property
    def version(self) -> str:
        return self._version

    @property
    def metadata(self) -> dict:
        return self._metadata

    @property
    def raw(self) -> dict:
        """Access the raw sot.json dict."""
        return self._data

    def nodes(self) -> list[dict]:
        """Get all nodes."""
        return list(self._nodes)

    def edges(self) -> list[dict]:
        """Get all edges."""
        return list(self._edges)

    def node_count(self) -> int:
        """Get total number of nodes."""
        return len(self._nodes)

    def edge_count(self) -> int:
        """Get total number of edges."""
        return len(self._edges)

    def node_by_id(self, node_id: str) -> Optional[dict]:
        """Get a node by its ID."""
        return self._nodes_by_id.get(node_id)

    def node(
        self,
        kind: Optional[str] = None,
        name: Optional[str] = None,
        fqn: Optional[str] = None,
    ) -> Optional[dict]:
        """Find a single node matching the given criteria.

        Returns the first matching node, or None.
        """
        candidates = self._nodes

        if kind is not None:
            candidates = [n for n in candidates if n.get("kind") == kind]
        if name is not None:
            candidates = [n for n in candidates if n.get("name") == name]
        if fqn is not None:
            candidates = [n for n in candidates if n.get("fqn") == fqn]

        return candidates[0] if candidates else None

    def nodes_by_kind(self, kind: str) -> list[dict]:
        """Get all nodes of a specific kind."""
        return list(self._nodes_by_kind.get(kind, []))

    def edge(
        self,
        type: Optional[str] = None,
        source: Optional[str] = None,
        target: Optional[str] = None,
    ) -> Optional[dict]:
        """Find a single edge matching the given criteria.

        Returns the first matching edge, or None.
        """
        candidates = self._edges

        if type is not None:
            candidates = [e for e in candidates if e.get("type") == type]
        if source is not None:
            candidates = [e for e in candidates if e.get("source") == source]
        if target is not None:
            candidates = [e for e in candidates if e.get("target") == target]

        return candidates[0] if candidates else None

    def edges_by_type(self, type: str) -> list[dict]:
        """Get all edges of a specific type."""
        return list(self._edges_by_type.get(type, []))

    def edges_from(self, source_id: str) -> list[dict]:
        """Get all edges originating from a node."""
        return [e for e in self._edges if e.get("source") == source_id]

    def edges_to(self, target_id: str) -> list[dict]:
        """Get all edges pointing to a node."""
        return [e for e in self._edges if e.get("target") == target_id]

    def node_ids(self) -> set[str]:
        """Get all node IDs."""
        return set(self._nodes_by_id.keys())

    def has_edge(
        self,
        type: Optional[str] = None,
        source: Optional[str] = None,
        target: Optional[str] = None,
    ) -> bool:
        """Check if an edge matching the criteria exists."""
        return self.edge(type=type, source=source, target=target) is not None
