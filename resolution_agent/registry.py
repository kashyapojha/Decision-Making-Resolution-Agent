from __future__ import annotations

from typing import Callable, Iterable


class ToolRegistry:
    def __init__(self) -> None:
        self._tools: dict[str, Callable] = {}
        self._schemas: dict[str, dict] = {}

    def register(self, name: str, function: Callable, schema: dict) -> None:
        if not callable(function):
            raise TypeError(f"Tool '{name}' must be callable")
        self._tools[name] = function
        self._schemas[name] = schema

    def execute(self, name: str, arguments: dict) -> dict:
        if name not in self._tools:
            return {
                "success": False,
                "error": "unknown_tool",
                "message": f"Tool '{name}' is not registered.",
            }
        if not isinstance(arguments, dict):
            return {
                "success": False,
                "error": "invalid_arguments",
                "message": "Tool arguments must be a JSON object.",
            }
        try:
            return self._tools[name](**arguments)
        except TypeError as exc:
            return {
                "success": False,
                "error": "invalid_arguments",
                "message": f"Invalid arguments for tool '{name}': {exc}",
            }
        except Exception as exc:
            return {
                "success": False,
                "error": "tool_execution_failed",
                "message": f"Tool '{name}' failed: {exc}",
            }

    def schemas(self) -> list[dict]:
        return [dict(schema) for schema in self._schemas.values()]
