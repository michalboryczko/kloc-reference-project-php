#!/usr/bin/env python3
"""Generate documentation from @contract_test metadata.

Collects test metadata via pytest collection and produces a markdown or JSON report.
"""

import argparse
import importlib
import inspect
import json
import os
import sys
from pathlib import Path


def collect_tests(tests_dir: Path) -> list[dict]:
    """Collect all test functions with @contract_test metadata."""
    results = []

    # Add parent dir to path so imports work
    sys.path.insert(0, str(tests_dir.parent))

    for test_file in sorted(tests_dir.glob("test_*.py")):
        module_name = f"tests.{test_file.stem}"
        try:
            spec = importlib.util.spec_from_file_location(module_name, test_file)
            module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(module)
        except Exception as e:
            print(f"Warning: Could not load {test_file}: {e}", file=sys.stderr)
            continue

        for name, obj in inspect.getmembers(module, inspect.isfunction):
            if not name.startswith("test_"):
                continue

            metadata = getattr(obj, "_contract_test", None)
            if metadata:
                results.append({
                    "function": name,
                    "module": test_file.stem,
                    **metadata,
                })

    return results


def generate_markdown(tests: list[dict]) -> str:
    """Generate markdown documentation from test metadata."""
    lines = []
    lines.append("# kloc-cli Contract Tests")
    lines.append("")
    lines.append("## Summary")
    lines.append("")

    # Count by category
    categories = {}
    for t in tests:
        cat = t.get("category", "uncategorized")
        categories.setdefault(cat, []).append(t)

    lines.append(f"**Total tests:** {len(tests)}")
    lines.append("")
    lines.append("| Category | Count |")
    lines.append("|----------|-------|")
    for cat in sorted(categories.keys()):
        lines.append(f"| {cat} | {len(categories[cat])} |")
    lines.append("")

    # Tests by category
    for cat in sorted(categories.keys()):
        lines.append(f"## {cat}")
        lines.append("")
        for t in categories[cat]:
            status = t.get("status", "active")
            status_icon = {"active": "PASS", "skipped": "SKIP", "pending": "PEND"}.get(
                status, status
            )
            lines.append(f"### [{status_icon}] {t['name']}")
            lines.append("")
            lines.append(f"**Description:** {t['description']}")
            lines.append("")
            lines.append(f"**Code reference:** `{t['module']}::{t['function']}`")
            lines.append("")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Generate contract test documentation")
    parser.add_argument(
        "--format", choices=["markdown", "json"], default="markdown", help="Output format"
    )
    parser.add_argument("--output", help="Output file path (default: stdout)")
    args = parser.parse_args()

    tests_dir = Path(__file__).parent.parent / "tests"
    tests = collect_tests(tests_dir)

    if args.format == "json":
        output = json.dumps({"tests": tests}, indent=2)
    else:
        output = generate_markdown(tests)

    if args.output:
        Path(args.output).write_text(output)
        print(f"Documentation written to {args.output}")
    else:
        print(output)


if __name__ == "__main__":
    main()
