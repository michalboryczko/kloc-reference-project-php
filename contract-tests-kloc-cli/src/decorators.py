"""Contract test decorator for metadata and documentation generation."""


def contract_test(
    name: str,
    description: str,
    category: str = "",
    status: str = "active",
    experimental: bool = False,
):
    """Decorator that attaches metadata to a pytest test function.

    Mirrors the PHP #[ContractTest] attribute used in the scip-php contract tests.

    Args:
        name: Human-readable test name shown in docs.
        description: What the test verifies (detailed).
        category: Test category (smoke, resolve, usages, deps, context, owners, inherit, overrides).
        status: Test status -- active, skipped, or pending.
        experimental: If True, test only runs in experimental mode.
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
