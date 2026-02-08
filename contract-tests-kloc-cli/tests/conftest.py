"""Global fixtures for kloc-cli contract tests.

Provides a realistic sot.json fixture representing a layered PHP architecture:
- OrderController -> OrderService -> OrderRepository -> Order
- EmailSenderInterface -> EmailSender (interface implementation)
- AbstractOrderProcessor -> StandardOrderProcessor (inheritance)
- Method overrides, properties, constants, containment chains
"""

import json
import os
import sys
import tempfile
from pathlib import Path

import pytest

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.fixture_generator import SoTFixtureBuilder
from src.output_validator import OutputValidator


@pytest.fixture(scope="session")
def reference_sot_builder() -> SoTFixtureBuilder:
    """Build a realistic sot.json fixture representing the reference project.

    This fixture mirrors the layered architecture in kloc-reference-project-php:
    - Entity layer: Order
    - Repository layer: OrderRepository
    - Service layer: OrderService, AbstractOrderProcessor, StandardOrderProcessor
    - Controller layer: OrderController
    - Component layer: EmailSenderInterface, EmailSender
    """
    b = SoTFixtureBuilder()

    # ===== Files =====
    f_order = b.add_file("src/Entity/Order.php")
    f_repo = b.add_file("src/Repository/OrderRepository.php")
    f_service = b.add_file("src/Service/OrderService.php")
    f_controller = b.add_file("src/Ui/Rest/Controller/OrderController.php")
    f_email_iface = b.add_file("src/Component/EmailSenderInterface.php")
    f_email_impl = b.add_file("src/Component/EmailSender.php")
    f_abstract_proc = b.add_file("src/Service/AbstractOrderProcessor.php")
    f_std_proc = b.add_file("src/Service/StandardOrderProcessor.php")

    # ===== Entity: Order =====
    c_order = b.add_class("App\\Entity\\Order", "src/Entity/Order.php", 5, 40)
    b.add_contains_edge(f_order, c_order)

    m_order_get_id = b.add_method(
        "App\\Entity\\Order::getId()", "src/Entity/Order.php", 10, 13,
        documentation=["```php\npublic function getId(): int\n```"],
    )
    b.add_contains_edge(c_order, m_order_get_id)

    p_order_id = b.add_property("App\\Entity\\Order::$id", "src/Entity/Order.php", 7)
    b.add_contains_edge(c_order, p_order_id)

    m_order_get_status = b.add_method(
        "App\\Entity\\Order::getStatus()", "src/Entity/Order.php", 15, 18,
        documentation=["```php\npublic function getStatus(): string\n```"],
    )
    b.add_contains_edge(c_order, m_order_get_status)

    p_order_status = b.add_property("App\\Entity\\Order::$status", "src/Entity/Order.php", 8)
    b.add_contains_edge(c_order, p_order_status)

    # ===== Repository: OrderRepository =====
    c_repo = b.add_class("App\\Repository\\OrderRepository", "src/Repository/OrderRepository.php", 5, 35)
    b.add_contains_edge(f_repo, c_repo)

    m_repo_save = b.add_method(
        "App\\Repository\\OrderRepository::save()", "src/Repository/OrderRepository.php", 10, 18,
        documentation=["```php\npublic function save(Order $order): Order\n```"],
    )
    b.add_contains_edge(c_repo, m_repo_save)
    b.add_uses_edge(m_repo_save, c_order, "src/Repository/OrderRepository.php", 12)

    m_repo_find = b.add_method(
        "App\\Repository\\OrderRepository::findById()", "src/Repository/OrderRepository.php", 20, 28,
        documentation=["```php\npublic function findById(int $id): ?Order\n```"],
    )
    b.add_contains_edge(c_repo, m_repo_find)
    b.add_uses_edge(m_repo_find, c_order, "src/Repository/OrderRepository.php", 22)

    # ===== Service: OrderService =====
    c_service = b.add_class("App\\Service\\OrderService", "src/Service/OrderService.php", 5, 50)
    b.add_contains_edge(f_service, c_service)

    m_svc_create = b.add_method(
        "App\\Service\\OrderService::createOrder()", "src/Service/OrderService.php", 15, 30,
        documentation=["```php\npublic function createOrder(CreateOrderInput $input): Order\n```"],
    )
    b.add_contains_edge(c_service, m_svc_create)
    b.add_uses_edge(m_svc_create, c_repo, "src/Service/OrderService.php", 18)
    b.add_uses_edge(m_svc_create, c_order, "src/Service/OrderService.php", 20)

    p_svc_repo = b.add_property("App\\Service\\OrderService::$orderRepository", "src/Service/OrderService.php", 8)
    b.add_contains_edge(c_service, p_svc_repo)
    b.add_type_hint_edge(p_svc_repo, c_repo)

    p_svc_email = b.add_property("App\\Service\\OrderService::$emailSender", "src/Service/OrderService.php", 9)
    b.add_contains_edge(c_service, p_svc_email)

    # ===== Controller: OrderController =====
    c_controller = b.add_class(
        "App\\Ui\\Rest\\Controller\\OrderController", "src/Ui/Rest/Controller/OrderController.php", 5, 40,
    )
    b.add_contains_edge(f_controller, c_controller)

    m_ctrl_create = b.add_method(
        "App\\Ui\\Rest\\Controller\\OrderController::create()",
        "src/Ui/Rest/Controller/OrderController.php", 12, 25,
        documentation=["```php\npublic function create(CreateOrderRequest $request): JsonResponse\n```"],
    )
    b.add_contains_edge(c_controller, m_ctrl_create)
    b.add_uses_edge(m_ctrl_create, c_service, "src/Ui/Rest/Controller/OrderController.php", 15)

    # ===== Interface: EmailSenderInterface =====
    c_email_iface = b.add_interface(
        "App\\Component\\EmailSenderInterface", "src/Component/EmailSenderInterface.php", 5, 15,
    )
    b.add_contains_edge(f_email_iface, c_email_iface)

    m_email_send_iface = b.add_method(
        "App\\Component\\EmailSenderInterface::send()",
        "src/Component/EmailSenderInterface.php", 8, 8,
        documentation=["```php\npublic function send(string $to, string $subject): void\n```"],
    )
    b.add_contains_edge(c_email_iface, m_email_send_iface)

    # Service uses EmailSenderInterface
    b.add_uses_edge(c_service, c_email_iface, "src/Service/OrderService.php", 9)
    b.add_type_hint_edge(p_svc_email, c_email_iface)

    # ===== Concrete: EmailSender implements EmailSenderInterface =====
    c_email_impl = b.add_class("App\\Component\\EmailSender", "src/Component/EmailSender.php", 5, 25)
    b.add_contains_edge(f_email_impl, c_email_impl)
    b.add_implements_edge(c_email_impl, c_email_iface)

    m_email_send_impl = b.add_method(
        "App\\Component\\EmailSender::send()",
        "src/Component/EmailSender.php", 10, 20,
        documentation=["```php\npublic function send(string $to, string $subject): void\n```"],
    )
    b.add_contains_edge(c_email_impl, m_email_send_impl)
    b.add_overrides_edge(m_email_send_impl, m_email_send_iface)

    # ===== Abstract: AbstractOrderProcessor =====
    c_abstract_proc = b.add_class(
        "App\\Service\\AbstractOrderProcessor", "src/Service/AbstractOrderProcessor.php", 5, 25,
    )
    b.add_contains_edge(f_abstract_proc, c_abstract_proc)

    m_proc_process_abstract = b.add_method(
        "App\\Service\\AbstractOrderProcessor::process()",
        "src/Service/AbstractOrderProcessor.php", 10, 15,
        documentation=["```php\npublic function process(Order $order): void\n```"],
    )
    b.add_contains_edge(c_abstract_proc, m_proc_process_abstract)

    # ===== Concrete: StandardOrderProcessor extends AbstractOrderProcessor =====
    c_std_proc = b.add_class(
        "App\\Service\\StandardOrderProcessor", "src/Service/StandardOrderProcessor.php", 5, 30,
    )
    b.add_contains_edge(f_std_proc, c_std_proc)
    b.add_extends_edge(c_std_proc, c_abstract_proc)

    m_proc_process_std = b.add_method(
        "App\\Service\\StandardOrderProcessor::process()",
        "src/Service/StandardOrderProcessor.php", 10, 20,
        documentation=["```php\npublic function process(Order $order): void\n```"],
    )
    b.add_contains_edge(c_std_proc, m_proc_process_std)
    b.add_overrides_edge(m_proc_process_std, m_proc_process_abstract)
    b.add_uses_edge(m_proc_process_std, c_order, "src/Service/StandardOrderProcessor.php", 12)

    return b


@pytest.fixture(scope="session")
def reference_sot_data(reference_sot_builder) -> dict:
    """Return the built sot.json dict."""
    return reference_sot_builder.build()


@pytest.fixture(scope="session")
def reference_sot_path(reference_sot_data, tmp_path_factory) -> Path:
    """Write the reference sot.json to a temp file and return its path."""
    tmp_dir = tmp_path_factory.mktemp("fixtures")
    sot_path = tmp_dir / "reference.json"
    with open(sot_path, "w") as f:
        json.dump(reference_sot_data, f, indent=2)
    return sot_path


@pytest.fixture(scope="session")
def cli(reference_sot_path) -> OutputValidator:
    """Return an OutputValidator configured with the reference sot.json.

    The CLI module path points to kloc-cli's src.cli module.
    Runs subprocess from the kloc-cli directory so module resolution works.
    """
    # Determine the kloc-cli directory
    kloc_cli_dir = Path(__file__).parent.parent.parent.parent / "kloc-cli"
    if not kloc_cli_dir.exists():
        # In Docker, kloc-cli is at /app/kloc-cli
        kloc_cli_dir = Path("/app/kloc-cli")

    # Use kloc-cli's venv Python if available (has typer/rich/msgspec)
    venv_python = kloc_cli_dir / ".venv" / "bin" / "python"
    python_exe = str(venv_python) if venv_python.exists() else sys.executable

    return OutputValidator(
        sot_path=reference_sot_path,
        cli_module="src.cli",
        cli_dir=str(kloc_cli_dir),
        python_exe=python_exe,
    )
