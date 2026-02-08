"""Contract test decorator for metadata and documentation generation.

Python equivalent of the PHP #[ContractTest] attribute used in scip-php contract tests.
Attaches metadata to pytest test functions for documentation generation.
"""


def contract_test(
    name: str,
    description: str,
    category: str = "",
    status: str = "active",
    experimental: bool = False,
):
    """Decorator that attaches contract test metadata to a pytest test function.

    Args:
        name: Human-readable test name shown in docs.
        description: What the test verifies (detailed).
        category: Test category (pipeline, usages, deps, etc.).
        status: Test status: active, skipped, pending.
        experimental: If True, test only runs with experimental flag.
    """
    def decorator(func):
        func._contract_test = {
            "name": name,
            "description": description,
            "category": category,
            "status": status,
            "experimental": experimental,
        }
        return func

    return decorator
