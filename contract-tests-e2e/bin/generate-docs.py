#!/usr/bin/env python3
"""Generate documentation from @contract_test decorators.

Scans test files for functions decorated with @contract_test and produces
either markdown or JSON documentation grouped by category.
"""

import argparse
import ast
import json
import sys
from pathlib import Path


def extract_contract_tests(test_dir: Path) -> list[dict]:
    """Extract @contract_test metadata from all test files."""
    tests = []

    for test_file in sorted(test_dir.glob("test_*.py")):
        source = test_file.read_text()
        tree = ast.parse(source)

        for node in ast.walk(tree):
            if not isinstance(node, ast.FunctionDef):
                continue
            for decorator in node.decorator_list:
                if not isinstance(decorator, ast.Call):
                    continue
                func = decorator.func
                name = func.id if isinstance(func, ast.Name) else getattr(func, "attr", "")
                if name != "contract_test":
                    continue

                metadata = {}
                for kw in decorator.keywords:
                    if isinstance(kw.value, ast.Constant):
                        metadata[kw.arg] = kw.value.value

                metadata["function"] = node.name
                metadata["file"] = test_file.name
                tests.append(metadata)

    return tests


def generate_markdown(tests: list[dict]) -> str:
    """Generate markdown documentation from test metadata."""
    lines = [
        "# E2E Integration Contract Tests",
        "",
        f"Total tests: {len(tests)}",
        "",
    ]

    # Group by category
    categories: dict[str, list[dict]] = {}
    for t in tests:
        cat = t.get("category", "uncategorized")
        categories.setdefault(cat, []).append(t)

    for category in sorted(categories):
        cat_tests = categories[category]
        lines.append(f"## {category.replace('-', ' ').title()} ({len(cat_tests)} tests)")
        lines.append("")

        for t in cat_tests:
            lines.append(f"### {t.get('name', t['function'])}")
            lines.append("")
            if "description" in t:
                lines.append(t["description"])
                lines.append("")
            status = t.get("status", "active")
            if status != "active":
                lines.append(f"**Status:** {status}")
                lines.append("")
            lines.append(f"- Function: `{t['function']}`")
            lines.append(f"- File: `{t['file']}`")
            lines.append("")

    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Generate contract test documentation")
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown")
    parser.add_argument("--output", help="Output file path (default: stdout)")
    args = parser.parse_args()

    test_dir = Path(__file__).resolve().parents[1] / "tests"
    tests = extract_contract_tests(test_dir)

    if args.format == "json":
        output = json.dumps(tests, indent=2)
    else:
        output = generate_markdown(tests)

    if args.output:
        Path(args.output).write_text(output)
        print(f"Documentation written to {args.output}", file=sys.stderr)
    else:
        print(output)


if __name__ == "__main__":
    main()
