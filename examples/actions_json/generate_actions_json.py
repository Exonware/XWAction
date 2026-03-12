from __future__ import annotations
import sys
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _find_monorepo_root(start: Path) -> Path:
    for p in [start] + list(start.parents):
        if (p / "xwaction").is_dir() and (p / "xwsystem").is_dir():
            return p
    return start


def _add_monorepo_src_paths() -> None:
    monorepo_root = _find_monorepo_root(Path(__file__).resolve())
    for pkg in ("xwaction", "xwsystem", "xwschema", "xwdata", "xwnode", "xwformats", "xwsyntax", "xwquery"):
        src = monorepo_root / pkg / "src"
        if src.is_dir():
            sys.path.insert(0, str(src))
_add_monorepo_src_paths()
from exonware.xwaction import XWAction, ActionRegistry  # noqa: E402
from exonware.xwschema import XWSchema  # noqa: E402
from exonware.xwsystem import JsonSerializer, YamlSerializer, TomlSerializer, XmlSerializer  # noqa: E402
@dataclass


class UserEntityActions:
    # CRUD
    @XWAction(profile="command", tags=["user", "crud"], roles=["admin"])

    def create_user(self, user: dict[str, Any]) -> dict[str, Any]:
        return {"status": "created", "user": user}
    @XWAction(profile="query", tags=["user", "crud"], roles=["*"])

    def get_user(self, user_id: str) -> dict[str, Any]:
        return {"id": user_id}
    @XWAction(profile="command", tags=["user", "crud"], roles=["admin"])

    def update_user(self, user_id: str, patch: dict[str, Any]) -> dict[str, Any]:
        return {"status": "updated", "id": user_id, "patch": patch}
    @XWAction(profile="command", tags=["user", "crud"], roles=["admin"])

    def delete_user(self, user_id: str) -> dict[str, Any]:
        return {"status": "deleted", "id": user_id}
    # Advanced
    @XWAction(profile="query", tags=["user", "advanced"], roles=["*"])

    def list_users(self, limit: int = 50, offset: int = 0) -> list[dict[str, Any]]:
        users = [{"id": "u1"}, {"id": "u2"}, {"id": "u3"}]
        return users[offset : offset + limit]
    @XWAction(profile="query", tags=["user", "advanced"], roles=["*"])

    def search_users(self, q: str) -> list[dict[str, Any]]:
        return [{"id": "u1", "q": q}]
    @XWAction(profile="command", tags=["user", "advanced"], roles=["admin"])

    def patch_user(self, user_id: str, json_patch: list[dict[str, Any]]) -> dict[str, Any]:
        return {"status": "patched", "id": user_id, "patch": json_patch}
    @XWAction(profile="command", tags=["user", "advanced"], roles=["admin"])

    def upsert_user(self, user: dict[str, Any]) -> dict[str, Any]:
        return {"status": "upserted", "user": user}
    @XWAction(profile="task", tags=["user", "advanced"], roles=["admin"])

    def export_users(self, format: str = "json") -> dict[str, Any]:
        return {"status": "export_started", "format": format}
    @XWAction(profile="task", tags=["user", "advanced"], roles=["admin"])

    def import_users(self, source: str) -> dict[str, Any]:
        return {"status": "import_started", "source": source}
    @XWAction(profile="command", tags=["user", "advanced"], roles=["admin"])

    def disable_user(self, user_id: str, reason: str | None = None) -> dict[str, Any]:
        return {"status": "disabled", "id": user_id, "reason": reason}
    @XWAction(profile="command", tags=["user", "advanced"], roles=["admin"])

    def restore_user(self, user_id: str) -> dict[str, Any]:
        return {"status": "restored", "id": user_id}
    @XWAction(profile="command", tags=["user", "advanced"], roles=["admin"])

    def bulk_create_users(self, users: list[dict[str, Any]]) -> dict[str, Any]:
        return {"status": "bulk_created", "count": len(users)}
    @XWAction(profile="query", tags=["user", "advanced"], roles=["admin"])

    def user_audit_trail(self, user_id: str, limit: int = 50) -> list[dict[str, Any]]:
        return [{"event": "created", "id": user_id}][:limit]
@dataclass


class OrderEntityActions:
    # CRUD
    @XWAction(profile="command", tags=["order", "crud"], roles=["admin"])

    def create_order(self, order: dict[str, Any]) -> dict[str, Any]:
        return {"status": "created", "order": order}
    @XWAction(profile="query", tags=["order", "crud"], roles=["*"])

    def get_order(self, order_id: str) -> dict[str, Any]:
        return {"id": order_id}
    @XWAction(profile="command", tags=["order", "crud"], roles=["admin"])

    def update_order(self, order_id: str, patch: dict[str, Any]) -> dict[str, Any]:
        return {"status": "updated", "id": order_id, "patch": patch}
    @XWAction(profile="command", tags=["order", "crud"], roles=["admin"])

    def cancel_order(self, order_id: str) -> dict[str, Any]:
        return {"status": "canceled", "id": order_id}
    # Advanced
    @XWAction(profile="query", tags=["order", "advanced"], roles=["*"])

    def list_orders(self, limit: int = 50, offset: int = 0) -> list[dict[str, Any]]:
        orders = [{"id": "o1"}, {"id": "o2"}, {"id": "o3"}]
        return orders[offset : offset + limit]
    @XWAction(profile="workflow", tags=["order", "advanced"], roles=["admin"])

    def batch_close_orders(self, order_ids: list[str]) -> dict[str, Any]:
        return {"status": "batch_close_started", "count": len(order_ids), "order_ids": order_ids}
    @XWAction(profile="command", tags=["order", "advanced"], roles=["admin"])

    def refund_order(self, order_id: str, amount: float, reason: str | None = None) -> dict[str, Any]:
        return {"status": "refund_started", "id": order_id, "amount": amount, "reason": reason}
    @XWAction(profile="query", tags=["order", "advanced"], roles=["*"])

    def order_history(self, order_id: str) -> list[dict[str, Any]]:
        return [{"id": order_id, "event": "created"}, {"id": order_id, "event": "paid"}]
@dataclass


class ProductEntityActions:
    # CRUD
    @XWAction(profile="command", tags=["product", "crud"], roles=["admin"])

    def create_product(self, product: dict[str, Any]) -> dict[str, Any]:
        return {"status": "created", "product": product}
    @XWAction(profile="query", tags=["product", "crud"], roles=["*"])

    def get_product(self, product_id: str) -> dict[str, Any]:
        return {"id": product_id}
    @XWAction(profile="command", tags=["product", "crud"], roles=["admin"])

    def update_product(self, product_id: str, patch: dict[str, Any]) -> dict[str, Any]:
        return {"status": "updated", "id": product_id, "patch": patch}
    @XWAction(profile="command", tags=["product", "crud"], roles=["admin"])

    def delete_product(self, product_id: str) -> dict[str, Any]:
        return {"status": "deleted", "id": product_id}
    # Advanced
    @XWAction(profile="query", tags=["product", "advanced"], roles=["*"])

    def list_products(self, limit: int = 50, offset: int = 0) -> list[dict[str, Any]]:
        products = [{"id": "p1"}, {"id": "p2"}, {"id": "p3"}]
        return products[offset : offset + limit]
    @XWAction(profile="query", tags=["product", "advanced"], roles=["*"])

    def search_products(self, q: str) -> list[dict[str, Any]]:
        return [{"id": "p1", "q": q}]
    @XWAction(profile="command", tags=["product", "advanced"], roles=["admin"])

    def bulk_update_products(self, patches: list[dict[str, Any]]) -> dict[str, Any]:
        return {"status": "bulk_update_started", "count": len(patches)}
    @XWAction(profile="task", tags=["product", "advanced"], roles=["admin"])

    def export_products(self, format: str = "json") -> dict[str, Any]:
        return {"status": "export_started", "format": format}
@dataclass


class InventoryEntityActions:
    # CRUD-ish (inventory is often keyed by sku/location)
    @XWAction(profile="command", tags=["inventory", "crud"], roles=["admin"])

    def upsert_stock(self, sku: str, location: str, qty: int) -> dict[str, Any]:
        return {"status": "upserted", "sku": sku, "location": location, "qty": qty}
    @XWAction(profile="query", tags=["inventory", "crud"], roles=["*"])

    def get_stock(self, sku: str, location: str) -> dict[str, Any]:
        return {"sku": sku, "location": location, "qty": 0}
    @XWAction(profile="command", tags=["inventory", "crud"], roles=["admin"])

    def delete_stock(self, sku: str, location: str) -> dict[str, Any]:
        return {"status": "deleted", "sku": sku, "location": location}
    # Advanced
    @XWAction(profile="command", tags=["inventory", "advanced"], roles=["admin"])

    def reserve_stock(self, sku: str, location: str, qty: int, order_id: str) -> dict[str, Any]:
        return {"status": "reserved", "sku": sku, "location": location, "qty": qty, "order_id": order_id}
    @XWAction(profile="command", tags=["inventory", "advanced"], roles=["admin"])

    def release_stock(self, reservation_id: str) -> dict[str, Any]:
        return {"status": "released", "reservation_id": reservation_id}
    @XWAction(profile="query", tags=["inventory", "advanced"], roles=["admin"])

    def stock_movements(self, sku: str, limit: int = 100) -> list[dict[str, Any]]:
        return [{"sku": sku, "delta": +1}, {"sku": sku, "delta": -1}][:limit]
    @XWAction(profile="workflow", tags=["inventory", "advanced"], roles=["admin"])

    def reconcile_inventory(self, location: str) -> dict[str, Any]:
        return {"status": "reconcile_started", "location": location}
@dataclass


class PaymentEntityActions:
    # CRUD
    @XWAction(profile="command", tags=["payment", "crud"], roles=["admin"])

    def create_payment(self, payment: dict[str, Any]) -> dict[str, Any]:
        return {"status": "created", "payment": payment}
    @XWAction(profile="query", tags=["payment", "crud"], roles=["*"])

    def get_payment(self, payment_id: str) -> dict[str, Any]:
        return {"id": payment_id}
    # Advanced
    @XWAction(profile="command", tags=["payment", "advanced"], roles=["admin"])

    def authorize_payment(self, payment_id: str) -> dict[str, Any]:
        return {"status": "authorized", "id": payment_id}
    @XWAction(profile="command", tags=["payment", "advanced"], roles=["admin"])

    def capture_payment(self, payment_id: str, amount: float | None = None) -> dict[str, Any]:
        return {"status": "captured", "id": payment_id, "amount": amount}
    @XWAction(profile="command", tags=["payment", "advanced"], roles=["admin"])

    def void_payment(self, payment_id: str, reason: str | None = None) -> dict[str, Any]:
        return {"status": "voided", "id": payment_id, "reason": reason}
    @XWAction(profile="query", tags=["payment", "advanced"], roles=["admin"])

    def list_payments(self, limit: int = 50, offset: int = 0) -> list[dict[str, Any]]:
        items = [{"id": "pay1"}, {"id": "pay2"}, {"id": "pay3"}]
        return items[offset : offset + limit]
@dataclass


class AuditLogEntityActions:
    @XWAction(profile="query", tags=["audit", "advanced"], roles=["admin"])

    def list_audit_events(self, entity_type: str | None = None, limit: int = 100) -> list[dict[str, Any]]:
        events = [
            {"entity_type": "User", "event": "create"},
            {"entity_type": "Order", "event": "refund"},
            {"entity_type": "Product", "event": "update"},
        ]
        if entity_type:
            events = [e for e in events if e.get("entity_type") == entity_type]
        return events[:limit]
    @XWAction(profile="query", tags=["audit", "advanced"], roles=["admin"])

    def get_audit_event(self, event_id: str) -> dict[str, Any]:
        return {"id": event_id}
    @XWAction(profile="task", tags=["audit", "advanced"], roles=["admin"])

    def export_audit_events(self, format: str = "json") -> dict[str, Any]:
        return {"status": "export_started", "format": format}
@dataclass


class FileAssetEntityActions:
    # CRUD
    @XWAction(profile="command", tags=["file", "crud"], roles=["admin"])

    def create_file_asset(self, asset: dict[str, Any]) -> dict[str, Any]:
        return {"status": "created", "asset": asset}
    @XWAction(profile="query", tags=["file", "crud"], roles=["*"])

    def get_file_asset(self, asset_id: str) -> dict[str, Any]:
        return {"id": asset_id}
    @XWAction(profile="command", tags=["file", "crud"], roles=["admin"])

    def delete_file_asset(self, asset_id: str) -> dict[str, Any]:
        return {"status": "deleted", "id": asset_id}
    # Advanced
    @XWAction(profile="task", tags=["file", "advanced"], roles=["admin"])

    def upload_file(self, filename: str, content_type: str) -> dict[str, Any]:
        return {"status": "upload_started", "filename": filename, "content_type": content_type}
    @XWAction(profile="query", tags=["file", "advanced"], roles=["*"])

    def download_file(self, asset_id: str) -> dict[str, Any]:
        return {"status": "download_url_created", "id": asset_id}
    @XWAction(profile="command", tags=["file", "advanced"], roles=["admin"])

    def rotate_file_key(self, asset_id: str) -> dict[str, Any]:
        return {"status": "key_rotated", "id": asset_id}


def _register_entity(entity_name: str, cls: type) -> list[str]:
    names: list[str] = []
    for name, attr in cls.__dict__.items():
        if hasattr(attr, "xwaction"):
            ActionRegistry.register(entity_name, attr.xwaction)  # type: ignore[attr-defined]
            names.append(name)
    return sorted(names)


def _build_matrix_from_registry(entity_name: str) -> dict[str, list[str]]:
    actions = ActionRegistry.get_actions_for(entity_name)
    crud: list[str] = []
    advanced: list[str] = []
    other: list[str] = []
    for a in actions.values():
        tags = getattr(a, "tags", None)
        if isinstance(tags, list):
            if "crud" in tags:
                crud.append(a.api_name)
                continue
            if "advanced" in tags:
                advanced.append(a.api_name)
                continue
        other.append(a.api_name)
    return {
        "crud": sorted(set(crud)),
        "advanced": sorted(set(advanced)),
        "other": sorted(set(other)),
    }


def build_actions_catalog() -> dict[str, Any]:
    ActionRegistry.clear()
    entities: list[tuple[str, type, list[str]]] = [
        ("User", UserEntityActions, ["user"]),
        ("Order", OrderEntityActions, ["order"]),
        ("Product", ProductEntityActions, ["product"]),
        ("Inventory", InventoryEntityActions, ["inventory"]),
        ("Payment", PaymentEntityActions, ["payment"]),
        ("AuditLog", AuditLogEntityActions, ["audit"]),
        ("FileAsset", FileAssetEntityActions, ["file"]),
    ]
    entity_methods: dict[str, list[str]] = {}
    for entity_name, cls, _ in entities:
        entity_methods[entity_name] = _register_entity(entity_name, cls)
    # attach a schema sample so it shows up in to_native()
    UserEntityActions.create_user.xwaction._in_types = {  # type: ignore[attr-defined]
        "user": XWSchema(
            {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "email": {"type": "string"},
                },
                "required": ["email"],
            }
        )
    }
    OrderEntityActions.create_order.xwaction._in_types = {  # type: ignore[attr-defined]
        "order": XWSchema(
            {
                "type": "object",
                "properties": {
                    "id": {"type": "string"},
                    "total": {"type": "number"},
                    "currency": {"type": "string"},
                },
                "required": ["total", "currency"],
            }
        )
    }
    ProductEntityActions.create_product.xwaction._in_types = {  # type: ignore[attr-defined]
        "product": XWSchema(
            {
                "type": "object",
                "properties": {
                    "sku": {"type": "string"},
                    "name": {"type": "string"},
                    "price": {"type": "number"},
                },
                "required": ["sku", "name"],
            }
        )
    }
    actions_native_by_entity: dict[str, list[dict[str, Any]]] = {}
    for entity_name, _, _ in entities:
        actions = ActionRegistry.get_actions_for(entity_name)
        actions_native_by_entity[entity_name] = [a.to_native() for a in actions.values()]
    entity_action_matrix: dict[str, dict[str, list[str]]] = {}
    for entity_name, _, _ in entities:
        entity_action_matrix[entity_name] = _build_matrix_from_registry(entity_name)
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "entities": {k: {"actions": v} for k, v in entity_methods.items()},
        "entity_action_matrix": entity_action_matrix,
        "actions_native_by_entity": actions_native_by_entity,
    }


def main() -> None:
    out_dir = Path(__file__).parent / "out"
    out_dir.mkdir(parents=True, exist_ok=True)
    catalog = build_actions_catalog()
    JsonSerializer().save_file(catalog, out_dir / "actions.json", indent=2)
    YamlSerializer().save_file(catalog, out_dir / "actions.yaml")
    TomlSerializer().save_file(catalog, out_dir / "actions.toml")
    XmlSerializer().save_file(catalog, out_dir / "actions.xml", root="xwaction_actions")
    print("Wrote:")
    for p in ["actions.json", "actions.yaml", "actions.toml", "actions.xml"]:
        print(f"- {out_dir / p}")
if __name__ == "__main__":
    main()
