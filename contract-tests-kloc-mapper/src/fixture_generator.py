"""SCIP protobuf fixture builder for kloc-mapper contract tests.

Generates .kloc archives (ZIP files containing index.scip + calls.json)
programmatically for testing kloc-mapper without depending on scip-php.

Uses scip_pb2 protobuf bindings from kloc-mapper/src/ for SCIP generation.
"""

import json
import tempfile
import zipfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional

import importlib.util

# Import scip_pb2 from kloc-mapper by file path to avoid name collision
# with our own src/ package
_scip_pb2_path = Path(__file__).resolve().parents[3] / "kloc-mapper" / "src" / "scip_pb2.py"
_spec = importlib.util.spec_from_file_location("scip_pb2", _scip_pb2_path)
scip_pb2 = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(scip_pb2)


@dataclass
class SymbolDef:
    """A symbol definition to include in a SCIP document."""
    symbol: str
    documentation: list[str] = field(default_factory=list)
    relationships: list[dict] = field(default_factory=list)
    kind: int = 0  # scip_pb2.SymbolInformation.Kind value


@dataclass
class OccurrenceDef:
    """An occurrence to include in a SCIP document."""
    symbol: str
    range: list[int]  # [line, start_col, end_col] or [start_line, start_col, end_line, end_col]
    symbol_roles: int = 0  # 0=Reference, 1=Definition
    enclosing_range: list[int] = field(default_factory=list)


@dataclass
class DocumentDef:
    """A document to include in the SCIP index."""
    relative_path: str
    language: str = "PHP"
    symbols: list[SymbolDef] = field(default_factory=list)
    occurrences: list[OccurrenceDef] = field(default_factory=list)


@dataclass
class ValueDef:
    """A value entry for calls.json."""
    id: str
    kind: str  # parameter, local, result, literal, constant
    symbol: str = ""
    type: str = ""
    location: dict = field(default_factory=dict)
    source_value_id: str = ""


@dataclass
class CallArgDef:
    """An argument reference in a call."""
    position: int
    value_id: str


@dataclass
class CallDef:
    """A call entry for calls.json."""
    id: str
    kind: str  # method, method_static, constructor, access, access_static, function
    callee: str = ""
    caller: str = ""
    return_type: str = ""
    location: dict = field(default_factory=dict)
    receiver_value_id: str = ""
    arguments: list[CallArgDef] = field(default_factory=list)


# SCIP symbol role constants
ROLE_DEFINITION = 1
ROLE_REFERENCE = 0


def _scip_symbol(manager: str, package: str, version: str, descriptor: str) -> str:
    """Build a SCIP symbol string."""
    return f"scip-php {manager} {package} {version} {descriptor}"


def php_class_symbol(namespace: str, class_name: str) -> str:
    """Create a SCIP symbol for a PHP class.

    Example: php_class_symbol("App/Entity", "Order") -> "scip-php composer pkg 1.0.0 App/Entity/Order#"
    """
    descriptor = f"{namespace}/{class_name}#" if namespace else f"{class_name}#"
    return _scip_symbol("composer", "pkg", "1.0.0", descriptor)


def php_interface_symbol(namespace: str, name: str) -> str:
    """Create a SCIP symbol for a PHP interface."""
    descriptor = f"{namespace}/{name}#" if namespace else f"{name}#"
    return _scip_symbol("composer", "pkg", "1.0.0", descriptor)


def php_trait_symbol(namespace: str, name: str) -> str:
    """Create a SCIP symbol for a PHP trait."""
    descriptor = f"{namespace}/{name}#" if namespace else f"{name}#"
    return _scip_symbol("composer", "pkg", "1.0.0", descriptor)


def php_enum_symbol(namespace: str, name: str) -> str:
    """Create a SCIP symbol for a PHP enum."""
    descriptor = f"{namespace}/{name}#" if namespace else f"{name}#"
    return _scip_symbol("composer", "pkg", "1.0.0", descriptor)


def php_method_symbol(class_symbol: str, method_name: str) -> str:
    """Create a SCIP symbol for a PHP method.

    Example: php_method_symbol(class_sym, "save") -> "scip-php composer pkg 1.0.0 App/Entity/Order#save()."
    """
    # Extract descriptor from class symbol and append method
    parts = class_symbol.split(" ")
    class_descriptor = parts[-1]  # e.g., "App/Entity/Order#"
    return _scip_symbol(parts[1], parts[2], parts[3], f"{class_descriptor}{method_name}().")


def php_property_symbol(class_symbol: str, prop_name: str) -> str:
    """Create a SCIP symbol for a PHP property (with $ prefix in descriptor)."""
    parts = class_symbol.split(" ")
    class_descriptor = parts[-1]
    return _scip_symbol(parts[1], parts[2], parts[3], f"{class_descriptor}${prop_name}.")


def php_const_symbol(class_symbol: str, const_name: str) -> str:
    """Create a SCIP symbol for a PHP class constant."""
    parts = class_symbol.split(" ")
    class_descriptor = parts[-1]
    return _scip_symbol(parts[1], parts[2], parts[3], f"{class_descriptor}{const_name}.")


def php_enum_case_symbol(enum_symbol: str, case_name: str) -> str:
    """Create a SCIP symbol for a PHP enum case."""
    parts = enum_symbol.split(" ")
    enum_descriptor = parts[-1]
    return _scip_symbol(parts[1], parts[2], parts[3], f"{enum_descriptor}{case_name}.")


def php_argument_symbol(method_symbol: str, arg_name: str) -> str:
    """Create a SCIP symbol for a PHP method argument/parameter.

    Example: php_argument_symbol(method_sym, "order") -> "...#save().($order)"
    """
    # Remove trailing dot from method symbol descriptor
    parts = method_symbol.split(" ")
    method_descriptor = parts[-1].rstrip(".")
    return _scip_symbol(parts[1], parts[2], parts[3], f"{method_descriptor}.(${ arg_name})")


def php_function_symbol(namespace: str, func_name: str) -> str:
    """Create a SCIP symbol for a standalone PHP function."""
    descriptor = f"{namespace}/{func_name}()." if namespace else f"{func_name}()."
    return _scip_symbol("composer", "pkg", "1.0.0", descriptor)


class KlocFixtureBuilder:
    """Builds .kloc archives for testing kloc-mapper.

    Usage:
        builder = KlocFixtureBuilder()
        builder.add_document(DocumentDef(...))
        builder.add_value(ValueDef(...))
        builder.add_call(CallDef(...))
        path = builder.build("/tmp/test.kloc")
    """

    def __init__(self):
        self.documents: list[DocumentDef] = []
        self.values: list[ValueDef] = []
        self.calls: list[CallDef] = []

    def add_document(self, doc: DocumentDef) -> "KlocFixtureBuilder":
        """Add a SCIP document to the fixture."""
        self.documents.append(doc)
        return self

    def add_value(self, value: ValueDef) -> "KlocFixtureBuilder":
        """Add a value entry to calls.json."""
        self.values.append(value)
        return self

    def add_call(self, call: CallDef) -> "KlocFixtureBuilder":
        """Add a call entry to calls.json."""
        self.calls.append(call)
        return self

    def _build_scip_index(self) -> bytes:
        """Build SCIP protobuf index from document definitions."""
        index = scip_pb2.Index()

        # Set metadata
        metadata = scip_pb2.Metadata()
        metadata.version = scip_pb2.UnspecifiedProtocolVersion
        tool_info = scip_pb2.ToolInfo()
        tool_info.name = "contract-test-fixture"
        tool_info.version = "1.0.0"
        metadata.tool_info.CopyFrom(tool_info)
        metadata.project_root = "file:///app/project"
        metadata.text_document_encoding = scip_pb2.UTF8
        index.metadata.CopyFrom(metadata)

        for doc_def in self.documents:
            doc = scip_pb2.Document()
            doc.relative_path = doc_def.relative_path
            doc.language = doc_def.language

            # Add symbol information
            for sym_def in doc_def.symbols:
                sym_info = scip_pb2.SymbolInformation()
                sym_info.symbol = sym_def.symbol
                for doc_str in sym_def.documentation:
                    sym_info.documentation.append(doc_str)

                if sym_def.kind:
                    sym_info.kind = sym_def.kind

                for rel_def in sym_def.relationships:
                    rel = scip_pb2.Relationship()
                    rel.symbol = rel_def["symbol"]
                    rel.is_reference = rel_def.get("is_reference", False)
                    rel.is_implementation = rel_def.get("is_implementation", False)
                    rel.is_type_definition = rel_def.get("is_type_definition", False)
                    rel.is_definition = rel_def.get("is_definition", False)
                    sym_info.relationships.append(rel)

                doc.symbols.append(sym_info)

            # Add occurrences
            for occ_def in doc_def.occurrences:
                occ = scip_pb2.Occurrence()
                occ.symbol = occ_def.symbol
                for r in occ_def.range:
                    occ.range.append(r)
                occ.symbol_roles = occ_def.symbol_roles
                if occ_def.enclosing_range:
                    for r in occ_def.enclosing_range:
                        occ.enclosing_range.append(r)
                doc.occurrences.append(occ)

            index.documents.append(doc)

        return index.SerializeToString()

    def _build_calls_json(self) -> dict:
        """Build calls.json data from value and call definitions."""
        values_list = []
        for v in self.values:
            entry = {
                "id": v.id,
                "kind": v.kind,
            }
            if v.symbol:
                entry["symbol"] = v.symbol
            if v.type:
                entry["type"] = v.type
            if v.location:
                entry["location"] = v.location
            if v.source_value_id:
                entry["source_value_id"] = v.source_value_id
            values_list.append(entry)

        calls_list = []
        for c in self.calls:
            entry = {
                "id": c.id,
                "kind": c.kind,
            }
            if c.callee:
                entry["callee"] = c.callee
            if c.caller:
                entry["caller"] = c.caller
            if c.return_type:
                entry["return_type"] = c.return_type
            if c.location:
                entry["location"] = c.location
            if c.receiver_value_id:
                entry["receiver_value_id"] = c.receiver_value_id
            if c.arguments:
                entry["arguments"] = [
                    {"position": a.position, "value_id": a.value_id}
                    for a in c.arguments
                ]
            calls_list.append(entry)

        return {
            "version": "3.2",
            "values": values_list,
            "calls": calls_list,
        }

    def build(self, output_path: str | Path) -> Path:
        """Build the .kloc archive at the given path.

        Returns:
            Path to the created .kloc archive.
        """
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        scip_data = self._build_scip_index()
        calls_data = self._build_calls_json()

        with zipfile.ZipFile(output_path, "w", zipfile.ZIP_DEFLATED) as zf:
            zf.writestr("index.scip", scip_data)
            zf.writestr("calls.json", json.dumps(calls_data, indent=2))

        return output_path

    def build_temp(self) -> Path:
        """Build the .kloc archive in a temporary location.

        Returns:
            Path to the created .kloc archive.
        """
        tmp = tempfile.NamedTemporaryFile(suffix=".kloc", delete=False)
        tmp.close()
        return self.build(tmp.name)


def build_minimal_fixture() -> KlocFixtureBuilder:
    """Create a minimal fixture with one class and one method.

    Returns a pre-configured builder with:
    - File: src/Service/OrderService.php
    - Class: App\\Service\\OrderService
    - Method: App\\Service\\OrderService::createOrder()
    """
    builder = KlocFixtureBuilder()

    class_sym = php_class_symbol("App/Service", "OrderService")
    method_sym = php_method_symbol(class_sym, "createOrder")

    doc = DocumentDef(
        relative_path="src/Service/OrderService.php",
        symbols=[
            SymbolDef(
                symbol=class_sym,
                documentation=["```php\nclass OrderService\n```"],
            ),
            SymbolDef(
                symbol=method_sym,
                documentation=["```php\npublic function createOrder()\n```"],
            ),
        ],
        occurrences=[
            OccurrenceDef(
                symbol=class_sym,
                range=[4, 6, 18],  # line 4, col 6-18
                symbol_roles=ROLE_DEFINITION,
                enclosing_range=[4, 0, 30, 1],
            ),
            OccurrenceDef(
                symbol=method_sym,
                range=[6, 21, 32],  # line 6, col 21-32
                symbol_roles=ROLE_DEFINITION,
                enclosing_range=[6, 4, 20, 5],
            ),
        ],
    )

    builder.add_document(doc)
    return builder


def build_full_fixture() -> KlocFixtureBuilder:
    """Create a comprehensive fixture with all 13 node kinds and key edge types.

    Models the reference project patterns:
    - Order entity, OrderService, OrderRepository, OrderController
    - EmailSenderInterface, EmailSender (implementation)
    - AbstractOrderProcessor, StandardOrderProcessor (inheritance)
    - OrderStatus enum, LoggableTrait
    """
    builder = KlocFixtureBuilder()

    # --- Symbols ---
    order_class = php_class_symbol("App/Entity", "Order")
    order_id_prop = php_property_symbol(order_class, "id")
    order_status_const = php_const_symbol(order_class, "DEFAULT_STATUS")
    order_get_id = php_method_symbol(order_class, "getId")

    order_service = php_class_symbol("App/Service", "OrderService")
    create_order = php_method_symbol(order_service, "createOrder")
    create_order_arg = php_argument_symbol(create_order, "order")

    order_repo = php_class_symbol("App/Repository", "OrderRepository")
    repo_save = php_method_symbol(order_repo, "save")
    repo_save_order_arg = php_argument_symbol(repo_save, "order")

    controller = php_class_symbol("App/Ui/Rest/Controller", "OrderController")

    email_iface = php_interface_symbol("App/Component", "EmailSenderInterface")
    email_send = php_method_symbol(email_iface, "send")

    email_sender = php_class_symbol("App/Component", "EmailSender")
    email_sender_send = php_method_symbol(email_sender, "send")

    abstract_processor = php_class_symbol("App/Service", "AbstractOrderProcessor")
    abstract_process = php_method_symbol(abstract_processor, "process")

    std_processor = php_class_symbol("App/Service", "StandardOrderProcessor")
    std_process = php_method_symbol(std_processor, "process")

    order_status_enum = php_enum_symbol("App/Entity", "OrderStatus")
    enum_case_pending = php_enum_case_symbol(order_status_enum, "Pending")

    loggable_trait = php_trait_symbol("App/Component", "LoggableTrait")

    helper_func = php_function_symbol("App/Helper", "formatPrice")

    # --- Document 1: Order entity ---
    doc_order = DocumentDef(
        relative_path="src/Entity/Order.php",
        symbols=[
            SymbolDef(
                symbol=order_class,
                documentation=["```php\nclass Order\n```"],
            ),
            SymbolDef(
                symbol=order_id_prop,
                documentation=["```php\nprivate int $id\n```"],
            ),
            SymbolDef(
                symbol=order_status_const,
                documentation=["```php\nconst DEFAULT_STATUS = 'new'\n```"],
            ),
            SymbolDef(
                symbol=order_get_id,
                documentation=["```php\npublic function getId(): int\n```"],
            ),
        ],
        occurrences=[
            OccurrenceDef(symbol=order_class, range=[5, 6, 11], symbol_roles=ROLE_DEFINITION, enclosing_range=[5, 0, 40, 1]),
            OccurrenceDef(symbol=order_id_prop, range=[7, 16, 19], symbol_roles=ROLE_DEFINITION),
            OccurrenceDef(symbol=order_status_const, range=[9, 10, 24], symbol_roles=ROLE_DEFINITION),
            OccurrenceDef(symbol=order_get_id, range=[11, 21, 26], symbol_roles=ROLE_DEFINITION, enclosing_range=[11, 4, 14, 5]),
        ],
    )

    # --- Document 2: OrderService ---
    doc_service = DocumentDef(
        relative_path="src/Service/OrderService.php",
        symbols=[
            SymbolDef(
                symbol=order_service,
                documentation=["```php\nclass OrderService\n```"],
            ),
            SymbolDef(
                symbol=create_order,
                documentation=["```php\npublic function createOrder(Order $order): Order\n```"],
            ),
            SymbolDef(
                symbol=create_order_arg,
                documentation=["```php\nOrder $order\n```"],
                relationships=[
                    {"symbol": order_class, "is_type_definition": True, "is_reference": False, "is_implementation": False, "is_definition": False},
                ],
            ),
        ],
        occurrences=[
            OccurrenceDef(symbol=order_service, range=[6, 6, 18], symbol_roles=ROLE_DEFINITION, enclosing_range=[6, 0, 30, 1]),
            OccurrenceDef(symbol=create_order, range=[8, 21, 32], symbol_roles=ROLE_DEFINITION, enclosing_range=[8, 4, 25, 5]),
            OccurrenceDef(symbol=create_order_arg, range=[8, 39, 45], symbol_roles=ROLE_DEFINITION),
            # Reference to OrderRepository::save() inside createOrder
            OccurrenceDef(symbol=repo_save, range=[12, 25, 29], symbol_roles=ROLE_REFERENCE),
            # Reference to Order class (type hint)
            OccurrenceDef(symbol=order_class, range=[8, 33, 38], symbol_roles=ROLE_REFERENCE),
        ],
    )

    # --- Document 3: OrderRepository ---
    doc_repo = DocumentDef(
        relative_path="src/Repository/OrderRepository.php",
        symbols=[
            SymbolDef(
                symbol=order_repo,
                documentation=["```php\nclass OrderRepository\n```"],
            ),
            SymbolDef(
                symbol=repo_save,
                documentation=["```php\npublic function save(Order $order): Order\n```"],
            ),
            SymbolDef(
                symbol=repo_save_order_arg,
                documentation=["```php\nOrder $order\n```"],
                relationships=[
                    {"symbol": order_class, "is_type_definition": True, "is_reference": False, "is_implementation": False, "is_definition": False},
                ],
            ),
        ],
        occurrences=[
            OccurrenceDef(symbol=order_repo, range=[5, 6, 21], symbol_roles=ROLE_DEFINITION, enclosing_range=[5, 0, 25, 1]),
            OccurrenceDef(symbol=repo_save, range=[7, 21, 25], symbol_roles=ROLE_DEFINITION, enclosing_range=[7, 4, 15, 5]),
            OccurrenceDef(symbol=repo_save_order_arg, range=[7, 32, 38], symbol_roles=ROLE_DEFINITION),
            # Reference to Order inside save()
            OccurrenceDef(symbol=order_class, range=[7, 26, 31], symbol_roles=ROLE_REFERENCE),
        ],
    )

    # --- Document 4: EmailSenderInterface + EmailSender ---
    doc_email = DocumentDef(
        relative_path="src/Component/EmailSenderInterface.php",
        symbols=[
            SymbolDef(
                symbol=email_iface,
                documentation=["```php\ninterface EmailSenderInterface\n```"],
            ),
            SymbolDef(
                symbol=email_send,
                documentation=["```php\npublic function send(string $to, string $subject): void\n```"],
            ),
        ],
        occurrences=[
            OccurrenceDef(symbol=email_iface, range=[5, 10, 30], symbol_roles=ROLE_DEFINITION, enclosing_range=[5, 0, 10, 1]),
            OccurrenceDef(symbol=email_send, range=[7, 21, 25], symbol_roles=ROLE_DEFINITION, enclosing_range=[7, 4, 7, 60]),
        ],
    )

    doc_email_impl = DocumentDef(
        relative_path="src/Component/EmailSender.php",
        symbols=[
            SymbolDef(
                symbol=email_sender,
                documentation=["```php\nclass EmailSender implements EmailSenderInterface\n```"],
                relationships=[
                    {"symbol": email_iface, "is_implementation": True, "is_reference": False, "is_type_definition": False, "is_definition": False},
                ],
            ),
            SymbolDef(
                symbol=email_sender_send,
                documentation=["```php\npublic function send(string $to, string $subject): void\n```"],
                relationships=[
                    {"symbol": email_send, "is_implementation": True, "is_reference": True, "is_type_definition": False, "is_definition": False},
                ],
            ),
        ],
        occurrences=[
            OccurrenceDef(symbol=email_sender, range=[5, 6, 17], symbol_roles=ROLE_DEFINITION, enclosing_range=[5, 0, 20, 1]),
            OccurrenceDef(symbol=email_sender_send, range=[7, 21, 25], symbol_roles=ROLE_DEFINITION, enclosing_range=[7, 4, 12, 5]),
        ],
    )

    # --- Document 5: Abstract + Standard processor (extends) ---
    doc_abstract = DocumentDef(
        relative_path="src/Service/AbstractOrderProcessor.php",
        symbols=[
            SymbolDef(
                symbol=abstract_processor,
                documentation=["```php\nabstract class AbstractOrderProcessor\n```"],
            ),
            SymbolDef(
                symbol=abstract_process,
                documentation=["```php\nabstract public function process(Order $order): void\n```"],
            ),
        ],
        occurrences=[
            OccurrenceDef(symbol=abstract_processor, range=[5, 16, 38], symbol_roles=ROLE_DEFINITION, enclosing_range=[5, 0, 15, 1]),
            OccurrenceDef(symbol=abstract_process, range=[7, 30, 37], symbol_roles=ROLE_DEFINITION, enclosing_range=[7, 4, 7, 55]),
        ],
    )

    doc_standard = DocumentDef(
        relative_path="src/Service/StandardOrderProcessor.php",
        symbols=[
            SymbolDef(
                symbol=std_processor,
                documentation=["```php\nclass StandardOrderProcessor extends AbstractOrderProcessor\n```"],
                relationships=[
                    {"symbol": abstract_processor, "is_reference": True, "is_implementation": False, "is_type_definition": False, "is_definition": False},
                ],
            ),
            SymbolDef(
                symbol=std_process,
                documentation=["```php\npublic function process(Order $order): void\n```"],
                relationships=[
                    {"symbol": abstract_process, "is_implementation": True, "is_reference": True, "is_type_definition": False, "is_definition": False},
                ],
            ),
        ],
        occurrences=[
            OccurrenceDef(symbol=std_processor, range=[5, 6, 30], symbol_roles=ROLE_DEFINITION, enclosing_range=[5, 0, 20, 1]),
            OccurrenceDef(symbol=std_process, range=[7, 21, 28], symbol_roles=ROLE_DEFINITION, enclosing_range=[7, 4, 15, 5]),
        ],
    )

    # --- Document 6: OrderStatus enum ---
    doc_enum = DocumentDef(
        relative_path="src/Entity/OrderStatus.php",
        symbols=[
            SymbolDef(
                symbol=order_status_enum,
                documentation=["```php\nenum OrderStatus: string\n```"],
            ),
            SymbolDef(
                symbol=enum_case_pending,
                documentation=["```php\ncase Pending = 'pending'\n```"],
            ),
        ],
        occurrences=[
            OccurrenceDef(symbol=order_status_enum, range=[5, 5, 16], symbol_roles=ROLE_DEFINITION, enclosing_range=[5, 0, 12, 1]),
            OccurrenceDef(symbol=enum_case_pending, range=[7, 9, 16], symbol_roles=ROLE_DEFINITION),
        ],
    )

    # --- Document 7: LoggableTrait ---
    doc_trait = DocumentDef(
        relative_path="src/Component/LoggableTrait.php",
        symbols=[
            SymbolDef(
                symbol=loggable_trait,
                documentation=["```php\ntrait LoggableTrait\n```"],
            ),
        ],
        occurrences=[
            OccurrenceDef(symbol=loggable_trait, range=[5, 6, 19], symbol_roles=ROLE_DEFINITION, enclosing_range=[5, 0, 15, 1]),
        ],
    )

    # --- Document 8: OrderController (uses trait) ---
    doc_controller = DocumentDef(
        relative_path="src/Ui/Rest/Controller/OrderController.php",
        symbols=[
            SymbolDef(
                symbol=controller,
                documentation=["```php\nclass OrderController\n```"],
                relationships=[
                    {"symbol": loggable_trait, "is_reference": True, "is_implementation": True, "is_type_definition": False, "is_definition": False},
                ],
            ),
        ],
        occurrences=[
            OccurrenceDef(symbol=controller, range=[8, 6, 21], symbol_roles=ROLE_DEFINITION, enclosing_range=[8, 0, 50, 1]),
            # Reference to OrderService
            OccurrenceDef(symbol=order_service, range=[12, 10, 22], symbol_roles=ROLE_REFERENCE),
        ],
    )

    # --- Document 9: Helper function ---
    doc_helper = DocumentDef(
        relative_path="src/Helper/functions.php",
        symbols=[
            SymbolDef(
                symbol=helper_func,
                documentation=["```php\nfunction formatPrice(float $amount): string\n```"],
            ),
        ],
        occurrences=[
            OccurrenceDef(symbol=helper_func, range=[3, 9, 20], symbol_roles=ROLE_DEFINITION, enclosing_range=[3, 0, 8, 1]),
        ],
    )

    # Add all documents
    for doc in [doc_order, doc_service, doc_repo, doc_email, doc_email_impl,
                doc_abstract, doc_standard, doc_enum, doc_trait, doc_controller, doc_helper]:
        builder.add_document(doc)

    # --- calls.json values ---
    builder.add_value(ValueDef(
        id="src/Service/OrderService.php:8:39",
        kind="parameter",
        symbol=create_order_arg,
        type=order_class,
        location={"file": "src/Service/OrderService.php", "line": 8, "col": 39},
    ))

    builder.add_value(ValueDef(
        id="src/Repository/OrderRepository.php:7:32",
        kind="parameter",
        symbol=repo_save_order_arg,
        type=order_class,
        location={"file": "src/Repository/OrderRepository.php", "line": 7, "col": 32},
    ))

    builder.add_value(ValueDef(
        id="src/Service/OrderService.php:12:8",
        kind="local",
        symbol=f"{create_order.rstrip('.')}local$result@12",
        type=order_class,
        location={"file": "src/Service/OrderService.php", "line": 12, "col": 8},
    ))

    builder.add_value(ValueDef(
        id="src/Service/OrderService.php:12:25",
        kind="result",
        symbol="",
        type=order_class,
        location={"file": "src/Service/OrderService.php", "line": 12, "col": 25},
    ))

    builder.add_value(ValueDef(
        id="src/Entity/Order.php:9:30",
        kind="literal",
        symbol="",
        type="",
        location={"file": "src/Entity/Order.php", "line": 9, "col": 30},
    ))

    builder.add_value(ValueDef(
        id="src/Entity/Order.php:9:10",
        kind="constant",
        symbol=order_status_const,
        type="",
        location={"file": "src/Entity/Order.php", "line": 9, "col": 10},
    ))

    # --- calls.json calls ---
    builder.add_call(CallDef(
        id="src/Service/OrderService.php:12:25",
        kind="method",
        callee=repo_save,
        caller=create_order,
        return_type=order_class,
        location={"file": "src/Service/OrderService.php", "line": 12, "col": 25},
        receiver_value_id="src/Service/OrderService.php:8:39",
        arguments=[
            CallArgDef(position=0, value_id="src/Service/OrderService.php:8:39"),
        ],
    ))

    return builder
