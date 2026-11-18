from __future__ import annotations

import json

from .providers import ModelProvider
from .registry import ToolRegistry
from .schemas import TOOLS
from .tools import ResolutionTools


class ResolutionAgent:
    def __init__(
        self,
        provider: ModelProvider,
        tools: ResolutionTools | None = None,
        max_iterations: int = 5,
    ) -> None:
        if max_iterations < 1:
            raise ValueError("max_iterations must be at least 1")
        self.provider = provider
        self.tools = tools or ResolutionTools()
        self.max_iterations = max_iterations
        self.registry = ToolRegistry()
        for schema in TOOLS:
            name = schema["function"]["name"]
            self.registry.register(name, getattr(self.tools, name), schema)

    def run(self, customer_request: str) -> dict:
        messages = [
            {
                "role": "system",
                "content": (
                    "You are an order resolution specialist. Investigate the issue with tools. "
                    "If the order is missing or malformed, explain it and ask for verification. "
                    "Check inventory after an order lookup. Refund only for ineligible or unavailable "
                    "replacements. Dispatch exactly one customer notification after a resolution."
                ),
            },
            {"role": "user", "content": customer_request},
        ]

        for iteration in range(1, self.max_iterations + 1):
            response = self.provider.generate(messages, self.registry.schemas())
            if response.tool_calls:
                if iteration == self.max_iterations:
                    return {
                        "status": "escalated",
                        "message": "Execution ceiling reached before resolution completed.",
                        "iterations": iteration,
                        "messages": messages,
                    }

                for call in response.tool_calls:
                    name = call["name"]
                    arguments = call["arguments"]
                    result = self.registry.execute(name, arguments)
                    messages.append({
                        "role": "assistant",
                        "content": response.content,
                        "tool_calls": [{
                            "id": call["id"],
                            "type": "function",
                            "function": {
                                "name": name,
                                "arguments": json.dumps(arguments),
                            },
                        }],
                    })
                    messages.append({
                        "role": "tool",
                        "tool_call_id": call["id"],
                        "name": name,
                        "content": json.dumps(result),
                    })
                continue

            messages.append({"role": "assistant", "content": response.content})
            return {
                "status": "resolved",
                "message": response.content,
                "iterations": iteration,
                "messages": messages,
            }

        return {
            "status": "escalated",
            "message": "Execution ceiling reached before resolution completed.",
            "iterations": self.max_iterations,
            "messages": messages,
        }
