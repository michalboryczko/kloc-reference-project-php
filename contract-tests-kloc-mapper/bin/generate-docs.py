#!/usr/bin/env python3
"""Generate documentation from @contract_test metadata.

Collects test metadata from all test functions decorated with @contract_test
and produces a markdown or JSON report grouped by category.
"""

import argparse
import importlib
import inspect
import json
import sys
from pathlib import Path


def collect_tests(tests_dir: Path) -> list[dict]:
    """Collect all @contract_test metadata from test files."""
    tests = []

    # Add parent to sys.path so imports work
    sys.path.insert(0, str(tests_dir.parent))

    for test_file in sorted(tests_dir.glob("test_*.py")):
        module_name = f"tests.{test_file.stem}"
        try:
            module = importlib.import_module(module_name)
        except Exception as e:
            print(f"Warning: Could not import {module_name}: {e}", file=sys.stderr)
            continue

        for name, obj in inspect.getmembers(module, inspect.isfunction):
            if not name.startswith("test_"):
                continue

            metadata = getattr(obj, "_contract_test", None)
            if metadata:
                tests.append({
                    "function": f"{test_file.stem}::{name}",
                    **metadata,
                })

    return tests


def generate_markdown(tests: list[dict]) -> str:
    """Generate markdown report from test metadata."""
    lines = []
    lines.append("# kloc-mapper Contract Tests")
    lines.append("")
    lines.append("## Summary")
    lines.append("")

    # Count by category
    categories: dict[str, list[dict]] = {}
    for test in tests:
        cat = test.get("category", "uncategorized")
        categories.setdefault(cat, []).append(test)

    total = len(tests)
    active = sum(1 for t in tests if t.get("status") == "active")
    skipped = sum(1 for t in tests if t.get("status") == "skipped")
    pending = sum(1 for t in tests if t.get("status") == "pending")

    lines.append(f"| Metric | Count |")
    lines.append(f"|--------|-------|")
    lines.append(f"| Total tests | {total} |")
    lines.append(f"| Active | {active} |")
    lines.append(f"| Skipped | {skipped} |")
    lines.append(f"| Pending | {pending} |")
    lines.append(f"| Categories | {len(categories)} |")
    lines.append("")

    # Tests by category
    for cat_name in sorted(categories.keys()):
        cat_tests = categories[cat_name]
        lines.append(f"## {cat_name}")
        lines.append("")
        lines.append(f"| Test | Description | Status |")
        lines.append(f"|------|-------------|--------|")
        for test in cat_tests:
            name = test.get("name", test.get("function", ""))
            desc = test.get("description", "")
            status = test.get("status", "active")
            lines.append(f"| {name} | {desc} | {status} |")
        lines.append("")

    return "\n".join(lines)


def generate_json(tests: list[dict]) -> str:
    """Generate JSON report from test metadata."""
    return json.dumps({"tests": tests}, indent=2)


def main():
    parser = argparse.ArgumentParser(description="Generate contract test documentation")
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown")
    parser.add_argument("--output", type=str, default=None)
    args = parser.parse_args()

    tests_dir = Path(__file__).parent.parent / "tests"
    tests = collect_tests(tests_dir)

    if args.format == "json":
        output = generate_json(tests)
    else:
        output = generate_markdown(tests)

    if args.output:
        output_path = Path(args.output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_text(output)
        print(f"Documentation written to {args.output}")
    else:
        print(output)


if __name__ == "__main__":
    main()
