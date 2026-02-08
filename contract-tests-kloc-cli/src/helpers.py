"""Shared test helpers for kloc-cli contract tests."""


def collect_fqns(tree: list[dict]) -> list[str]:
    """Recursively collect all FQNs from a tree/entry structure.

    Works with all kloc-cli JSON output formats: usages tree, deps tree,
    context used_by/uses, inherit tree, overrides tree.

    Args:
        tree: List of entry dicts with 'fqn', optional 'children' and 'implementations'.

    Returns:
        Flat list of all FQN strings found in the tree.
    """
    fqns = []
    for entry in tree:
        fqns.append(entry["fqn"])
        if entry.get("children"):
            fqns.extend(collect_fqns(entry["children"]))
        if entry.get("implementations"):
            fqns.extend(collect_fqns(entry["implementations"]))
    return fqns
