"""sot.json fixture builder for kloc-cli contract tests.

Generates valid sot.json v2.0 structures programmatically.
No dependency on kloc-mapper -- produces plain JSON dicts.
"""

import hashlib
import json
from pathlib import Path


def _generate_id(prefix: str, key: str) -> str:
    """Generate deterministic node ID from prefix and key."""
    h = hashlib.sha256(f"{prefix}:{key}".encode("utf-8")).hexdigest()[:16]
    return f"node:{h}"


class SoTFixtureBuilder:
    """Builds sot.json v2.0 fixtures for testing kloc-cli.

    Provides convenience methods for adding PHP-style nodes and edges,
    producing valid sot.json dicts that kloc-cli can load.
    """

    def __init__(self, version: str = "2.0"):
        self._version = version
        self._nodes: list[dict] = []
        self._edges: list[dict] = []
        self._node_ids: dict[str, str] = {}  # fqn -> node_id

    def add_file(self, path: str) -> str:
        """Add a File node. Returns the node ID."""
        node_id = _generate_id("file", path)
        self._nodes.append({
            "id": node_id,
            "kind": "File",
            "name": path.split("/")[-1],
            "fqn": path,
            "symbol": f"file:{path}",
            "file": path,
            "range": {"start_line": 0, "start_col": 0, "end_line": 100, "end_col": 0},
            "documentation": [],
        })
        self._node_ids[path] = node_id
        return node_id

    def add_class(
        self,
        fqn: str,
        file: str,
        start_line: int = 5,
        end_line: int = 50,
    ) -> str:
        """Add a Class node. Returns the node ID."""
        name = fqn.split("\\")[-1]
        node_id = _generate_id("class", fqn)
        self._nodes.append({
            "id": node_id,
            "kind": "Class",
            "name": name,
            "fqn": fqn,
            "symbol": f"php . {fqn.replace(chr(92), '/')}#",
            "file": file,
            "range": {
                "start_line": start_line,
                "start_col": 0,
                "end_line": end_line,
                "end_col": 0,
            },
            "documentation": [],
        })
        self._node_ids[fqn] = node_id
        return node_id

    def add_interface(
        self,
        fqn: str,
        file: str,
        start_line: int = 5,
        end_line: int = 30,
    ) -> str:
        """Add an Interface node. Returns the node ID."""
        name = fqn.split("\\")[-1]
        node_id = _generate_id("interface", fqn)
        self._nodes.append({
            "id": node_id,
            "kind": "Interface",
            "name": name,
            "fqn": fqn,
            "symbol": f"php . {fqn.replace(chr(92), '/')}#",
            "file": file,
            "range": {
                "start_line": start_line,
                "start_col": 0,
                "end_line": end_line,
                "end_col": 0,
            },
            "documentation": [],
        })
        self._node_ids[fqn] = node_id
        return node_id

    def add_trait(
        self,
        fqn: str,
        file: str,
        start_line: int = 5,
        end_line: int = 30,
    ) -> str:
        """Add a Trait node. Returns the node ID."""
        name = fqn.split("\\")[-1]
        node_id = _generate_id("trait", fqn)
        self._nodes.append({
            "id": node_id,
            "kind": "Trait",
            "name": name,
            "fqn": fqn,
            "symbol": f"php . {fqn.replace(chr(92), '/')}#",
            "file": file,
            "range": {
                "start_line": start_line,
                "start_col": 0,
                "end_line": end_line,
                "end_col": 0,
            },
            "documentation": [],
        })
        self._node_ids[fqn] = node_id
        return node_id

    def add_enum(
        self,
        fqn: str,
        file: str,
        start_line: int = 5,
        end_line: int = 20,
    ) -> str:
        """Add an Enum node. Returns the node ID."""
        name = fqn.split("\\")[-1]
        node_id = _generate_id("enum", fqn)
        self._nodes.append({
            "id": node_id,
            "kind": "Enum",
            "name": name,
            "fqn": fqn,
            "symbol": f"php . {fqn.replace(chr(92), '/')}#",
            "file": file,
            "range": {
                "start_line": start_line,
                "start_col": 0,
                "end_line": end_line,
                "end_col": 0,
            },
            "documentation": [],
        })
        self._node_ids[fqn] = node_id
        return node_id

    def add_method(
        self,
        fqn: str,
        file: str,
        start_line: int = 10,
        end_line: int = 20,
        documentation: list[str] | None = None,
    ) -> str:
        """Add a Method node. FQN format: 'App\\Foo::bar()'. Returns the node ID."""
        name = fqn.split("::")[-1] if "::" in fqn else fqn.split("\\")[-1]
        node_id = _generate_id("method", fqn)
        self._nodes.append({
            "id": node_id,
            "kind": "Method",
            "name": name,
            "fqn": fqn,
            "symbol": f"php . {fqn.replace(chr(92), '/').replace('::', '.')}.",
            "file": file,
            "range": {
                "start_line": start_line,
                "start_col": 4,
                "end_line": end_line,
                "end_col": 4,
            },
            "documentation": documentation or [],
        })
        self._node_ids[fqn] = node_id
        return node_id

    def add_function(
        self,
        fqn: str,
        file: str,
        start_line: int = 3,
        end_line: int = 10,
    ) -> str:
        """Add a Function node. Returns the node ID."""
        name = fqn.split("\\")[-1]
        node_id = _generate_id("function", fqn)
        self._nodes.append({
            "id": node_id,
            "kind": "Function",
            "name": name,
            "fqn": fqn,
            "symbol": f"php . {fqn.replace(chr(92), '/')}.",
            "file": file,
            "range": {
                "start_line": start_line,
                "start_col": 0,
                "end_line": end_line,
                "end_col": 0,
            },
            "documentation": [],
        })
        self._node_ids[fqn] = node_id
        return node_id

    def add_property(
        self,
        fqn: str,
        file: str,
        start_line: int = 8,
    ) -> str:
        """Add a Property node. FQN format: 'App\\Foo::$bar'. Returns the node ID."""
        name = fqn.split("::")[-1] if "::" in fqn else fqn.split("\\")[-1]
        node_id = _generate_id("property", fqn)
        self._nodes.append({
            "id": node_id,
            "kind": "Property",
            "name": name,
            "fqn": fqn,
            "symbol": f"php . {fqn.replace(chr(92), '/').replace('::', '.')}.",
            "file": file,
            "range": {
                "start_line": start_line,
                "start_col": 4,
                "end_line": start_line,
                "end_col": 40,
            },
            "documentation": [],
        })
        self._node_ids[fqn] = node_id
        return node_id

    def add_const(
        self,
        fqn: str,
        file: str,
        start_line: int = 7,
    ) -> str:
        """Add a Const node. FQN format: 'App\\Foo::BAR'. Returns the node ID."""
        name = fqn.split("::")[-1] if "::" in fqn else fqn.split("\\")[-1]
        node_id = _generate_id("const", fqn)
        self._nodes.append({
            "id": node_id,
            "kind": "Const",
            "name": name,
            "fqn": fqn,
            "symbol": f"php . {fqn.replace(chr(92), '/').replace('::', '.')}.",
            "file": file,
            "range": {
                "start_line": start_line,
                "start_col": 4,
                "end_line": start_line,
                "end_col": 40,
            },
            "documentation": [],
        })
        self._node_ids[fqn] = node_id
        return node_id

    def add_edge(self, edge_type: str, source_id: str, target_id: str, **kwargs) -> None:
        """Add an edge between two nodes.

        Args:
            edge_type: Edge type (contains, extends, implements, uses, etc.)
            source_id: Source node ID
            target_id: Target node ID
            **kwargs: Additional edge properties (location, position)
        """
        edge = {
            "type": edge_type,
            "source": source_id,
            "target": target_id,
        }
        if "location" in kwargs:
            edge["location"] = kwargs["location"]
        if "position" in kwargs:
            edge["position"] = kwargs["position"]
        self._edges.append(edge)

    def add_contains_edge(self, parent_id: str, child_id: str) -> None:
        """Add a contains edge (parent -> child)."""
        self.add_edge("contains", parent_id, child_id)

    def add_extends_edge(self, child_id: str, parent_id: str) -> None:
        """Add an extends edge (child -> parent)."""
        self.add_edge("extends", child_id, parent_id)

    def add_implements_edge(self, class_id: str, interface_id: str) -> None:
        """Add an implements edge (class -> interface)."""
        self.add_edge("implements", class_id, interface_id)

    def add_uses_edge(
        self,
        source_id: str,
        target_id: str,
        file: str | None = None,
        line: int | None = None,
    ) -> None:
        """Add a uses edge (source -> target)."""
        kwargs = {}
        if file is not None and line is not None:
            kwargs["location"] = {"file": file, "line": line, "col": 0}
        self.add_edge("uses", source_id, target_id, **kwargs)

    def add_overrides_edge(self, child_method_id: str, parent_method_id: str) -> None:
        """Add an overrides edge (child method -> parent method)."""
        self.add_edge("overrides", child_method_id, parent_method_id)

    def add_type_hint_edge(self, source_id: str, target_id: str) -> None:
        """Add a type_hint edge (source -> type target)."""
        self.add_edge("type_hint", source_id, target_id)

    def add_uses_trait_edge(self, class_id: str, trait_id: str) -> None:
        """Add a uses_trait edge (class -> trait)."""
        self.add_edge("uses_trait", class_id, trait_id)

    def get_node_id(self, fqn: str) -> str | None:
        """Look up a node ID by FQN. Returns None if not found."""
        return self._node_ids.get(fqn)

    def build(self) -> dict:
        """Build the sot.json dict."""
        return {
            "version": self._version,
            "metadata": {},
            "nodes": sorted(self._nodes, key=lambda n: n["id"]),
            "edges": sorted(
                self._edges, key=lambda e: (e["source"], e["type"], e["target"])
            ),
        }

    def write(self, path: str | Path) -> None:
        """Write the sot.json to a file."""
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w") as f:
            json.dump(self.build(), f, indent=2, ensure_ascii=False)


def create_sot(nodes: list[dict], edges: list[dict], version: str = "2.0") -> dict:
    """Create a minimal sot.json dict from raw nodes and edges.

    For simple cases where the builder pattern is overkill.
    """
    return {
        "version": version,
        "metadata": {},
        "nodes": sorted(nodes, key=lambda n: n["id"]),
        "edges": sorted(edges, key=lambda e: (e["source"], e["type"], e["target"])),
    }
