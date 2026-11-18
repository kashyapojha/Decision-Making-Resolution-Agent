from __future__ import annotations

from copy import deepcopy
from datetime import datetime, timezone
import uuid


class ResolutionTools:
    def __init__(
        self,
        orders: dict | None = None,
        inventory: dict | None = None,
        notifications: list | None = None,
    ) -> None:
        self.orders = orders if orders is not None else {
            "ORD-1001": {
                "customer_name": "Avery Chen",
                "customer_email": "avery@example.com",
                "item_id": "ITEM-LAPTOP-01",
                "item_name": "Laptop",
                "order_status": "delivered",
                "exchange_eligible": True,
            },
            "ORD-1002": {
                "customer_name": "Jordan Lee",
                "customer_email": "jordan@example.com",
                "item_id": "ITEM-HEADPHONE-02",
                "item_name": "Headphones",
                "order_status": "delivered",
                "exchange_eligible": True,
            },
        }
        self.inventory = inventory if inventory is not None else {
            "ITEM-LAPTOP-01": 1,
            "ITEM-HEADPHONE-02": 0,
        }
        self.notifications = notifications if notifications is not None else []
        self.refunds: dict[str, dict] = {}

    def order_lookup(self, order_id: str) -> dict:
        order = self.orders.get(order_id)
        if order is None:
            return {
                "success": False,
                "error": "order_not_found",
                "message": f"No order was found for order identifier '{order_id}'.",
            }
        return {
            "success": True,
            "order_id": order_id,
            **deepcopy(order),
        }

    def inventory_inspection(self, item_id: str) -> dict:
        if item_id not in self.inventory:
            return {
                "success": False,
                "error": "item_not_found",
                "message": f"No inventory record was found for item '{item_id}'.",
            }
        quantity = max(0, int(self.inventory[item_id]))
        return {
            "success": True,
            "item_id": item_id,
            "stock_count": quantity,
            "available": quantity > 0,
        }

    def refund_processing(self, order_id: str, reason: str) -> dict:
        order = self.orders.get(order_id)
        if order is None:
            return {
                "success": False,
                "error": "order_not_found",
                "message": f"No order was found for order identifier '{order_id}'.",
            }
        if not reason.strip():
            return {
                "success": False,
                "error": "invalid_reason",
                "message": "A non-empty refund reason is required.",
            }
        if order_id in self.refunds:
            return {"success": True, "duplicate": True, **deepcopy(self.refunds[order_id])}

        refund_amount = float(order.get("refundable_amount", 99.99))
        reference = f"RFND-{uuid.uuid4().hex[:12].upper()}"
        transaction = {
            "transaction_reference": reference,
            "order_id": order_id,
            "refund_amount": refund_amount,
            "reason": reason.strip(),
            "status": "processed",
            "processed_at": datetime.now(timezone.utc).isoformat(),
        }
        self.refunds[order_id] = deepcopy(transaction)
        return {"success": True, "duplicate": False, **deepcopy(transaction)}

    def customer_notification(self, email: str, message: str) -> dict:
        if "@" not in email or not email.strip():
            return {
                "success": False,
                "error": "invalid_email",
                "message": "A valid customer email address is required.",
            }
        if not message.strip():
            return {
                "success": False,
                "error": "invalid_message",
                "message": "The notification message cannot be empty.",
            }
        notification = {
            "notification_id": f"NOTIFY-{uuid.uuid4().hex[:12].upper()}",
            "email": email.strip(),
            "message": message.strip(),
            "status": "dispatched",
            "dispatched_at": datetime.now(timezone.utc).isoformat(),
        }
        self.notifications.append(deepcopy(notification))
        return {"success": True, **deepcopy(notification)}
