from __future__ import annotations

import json
import os
import re
import urllib.request


class ModelResponse:
    def __init__(self, content: str | None = None, tool_calls: list[dict] | None = None) -> None:
        self.content = content
        self.tool_calls = tool_calls or []


class ModelProvider:
    def generate(self, messages: list[dict], tool_schemas: list[dict]) -> ModelResponse:
        raise NotImplementedError


class OpenAICompatibleProvider(ModelProvider):
    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        base_url: str | None = None,
    ) -> None:
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model = model or os.getenv("OPENAI_MODEL", "gpt-4o-mini")
        self.base_url = (
            base_url or os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1")
        ).rstrip("/")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY is required for OpenAICompatibleProvider")

    def generate(self, messages: list[dict], tool_schemas: list[dict]) -> ModelResponse:
        payload = {
            "model": self.model,
            "messages": messages,
            "tools": tool_schemas,
            "tool_choice": "auto",
        }
        request = urllib.request.Request(
            f"{self.base_url}/chat/completions",
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=30) as response:
            result = json.loads(response.read().decode("utf-8"))
        message = result["choices"][0]["message"]
        tool_calls = []
        for call in message.get("tool_calls", []):
            raw_arguments = call.get("function", {}).get("arguments", "{}")
            try:
                arguments = json.loads(raw_arguments)
            except json.JSONDecodeError:
                arguments = {"__malformed_json__": raw_arguments}
            tool_calls.append(
                {
                    "id": call["id"],
                    "name": call["function"]["name"],
                    "arguments": arguments,
                }
            )
        return ModelResponse(content=message.get("content"), tool_calls=tool_calls)


class DeterministicFallbackProvider(ModelProvider):
    """Offline provider used by the demo and tests; it follows an order-resolution workflow."""

    def __init__(self) -> None:
        self._step = 0
        self._order_id: str | None = None

    def generate(self, messages: list[dict], tool_schemas: list[dict]) -> ModelResponse:
        if self._step == 0:
            text = next(
                (message["content"] for message in reversed(messages) if message["role"] == "user"),
                "",
            )
            match = re.search(r"\bORD-[A-Z0-9-]+\b", text, re.IGNORECASE)
            self._order_id = match.group(0).upper() if match else None
            self._step = 1
            if self._order_id is None:
                return ModelResponse(content="Please provide a valid order identifier, such as ORD-1001.")
            return ModelResponse(tool_calls=[{
                "id": "call-order",
                "name": "order_lookup",
                "arguments": {"order_id": self._order_id},
            }])

        if self._step == 1:
            order_message = next(
                (
                    message
                    for message in reversed(messages)
                    if message["role"] == "tool" and message.get("name") == "order_lookup"
                ),
                None,
            )
            if order_message is None:
                return ModelResponse(content="The order lookup did not return a result.")
            payload = json.loads(order_message["content"])
            if not payload["success"]:
                self._step = 99
                return ModelResponse(
                    content=f"{payload['message']} Please verify the identifier and try again."
                )
            self._step = 2
            return ModelResponse(tool_calls=[{
                "id": "call-inventory",
                "name": "inventory_inspection",
                "arguments": {"item_id": payload["item_id"]},
            }])

        if self._step == 2:
            inventory_message = next(
                (
                    message
                    for message in reversed(messages)
                    if message["role"] == "tool" and message.get("name") == "inventory_inspection"
                ),
                None,
            )
            if inventory_message is None:
                return ModelResponse(content="The inventory inspection did not return a result.")
            payload = json.loads(inventory_message["content"])
            if not payload["success"]:
                self._step = 99
                return ModelResponse(content=payload["message"] + " Human escalation is recommended.")
            order_payload = next(
                (
                    json.loads(entry["content"])
                    for entry in reversed(messages)
                    if entry["role"] == "tool" and entry.get("name") == "order_lookup"
                ),
                None,
            )
            if payload["available"]:
                self._step = 99
                return ModelResponse(
                    content=(
                        f"An exchange is available for order {order_payload['order_id']}. "
                        "The replacement unit is ready to be dispatched."
                    )
                )
            self._step = 3
            return ModelResponse(tool_calls=[{
                "id": "call-refund",
                "name": "refund_processing",
                "arguments": {
                    "order_id": order_payload["order_id"],
                    "reason": "Damaged item and replacement unavailable",
                },
            }])

        if self._step == 3:
            refund_message = next(
                (
                    message
                    for message in reversed(messages)
                    if message["role"] == "tool" and message.get("name") == "refund_processing"
                ),
                None,
            )
            if refund_message is None:
                return ModelResponse(content="The refund processing did not return a result.")
            refund = json.loads(refund_message["content"])
            if not refund["success"]:
                self._step = 99
                return ModelResponse(content=refund["message"])
            order_payload = next(
                (
                    json.loads(entry["content"])
                    for entry in reversed(messages)
                    if entry["role"] == "tool" and entry.get("name") == "order_lookup"
                ),
                None,
            )
            self._step = 4
            return ModelResponse(tool_calls=[{
                "id": "call-notify",
                "name": "customer_notification",
                "arguments": {
                    "email": order_payload["customer_email"],
                    "message": (
                        f"We processed a refund of ${refund['refund_amount']:.2f} for order "
                        f"{refund['order_id']}. Your transaction reference is "
                        f"{refund['transaction_reference']}."
                    ),
                },
            }])

        if self._step == 4:
            notification_message = next(
                (
                    message
                    for message in reversed(messages)
                    if message["role"] == "tool" and message.get("name") == "customer_notification"
                ),
                None,
            )
            if notification_message is not None:
                notification = json.loads(notification_message["content"])
                if notification["success"]:
                    self._step = 99
                    return ModelResponse(
                        content=f"Refund confirmed and notification dispatched to {notification['email']}."
                    )
        return ModelResponse(content="The resolution could not be completed and was escalated.")
