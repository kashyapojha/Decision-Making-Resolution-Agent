import unittest

from resolution_agent.agent import ResolutionAgent
from resolution_agent.providers import DeterministicFallbackProvider
from resolution_agent.registry import ToolRegistry
from resolution_agent.tools import ResolutionTools


class ResolutionAgentTests(unittest.TestCase):
    def test_refund_branch_when_replacement_is_unavailable(self):
        agent = ResolutionAgent(DeterministicFallbackProvider())

        result = agent.run("My headphones from ORD-1002 arrived damaged.")

        self.assertEqual(result["status"], "resolved")
        self.assertIn("Refund confirmed", result["message"])
        self.assertTrue(agent.tools.refunds["ORD-1002"]["transaction_reference"].startswith("RFND-"))
        self.assertEqual(len(agent.tools.notifications), 1)
        self.assertIn("ORD-1002", agent.tools.notifications[0]["message"])

    def test_exchange_branch_when_replacement_is_available(self):
        agent = ResolutionAgent(DeterministicFallbackProvider())

        result = agent.run("My laptop in ORD-1001 is damaged.")

        self.assertEqual(result["status"], "resolved")
        self.assertIn("exchange is available", result["message"])
        self.assertEqual(agent.tools.refunds, {})
        self.assertEqual(agent.tools.notifications, [])

    def test_invalid_order_is_explained(self):
        agent = ResolutionAgent(DeterministicFallbackProvider())

        result = agent.run("ORD-9999 has a damaged item.")

        self.assertEqual(result["status"], "resolved")
        self.assertIn("No order was found", result["message"])
        self.assertIn("verify", result["message"].lower())

    def test_unknown_tool_is_rejected_by_dispatcher(self):
        registry = ToolRegistry()

        result = registry.execute("delete_database", {})

        self.assertFalse(result["success"])
        self.assertEqual(result["error"], "unknown_tool")

    def test_argument_validation_reports_type_errors(self):
        tools = ResolutionTools()
        registry = ToolRegistry()
        registry.register("order_lookup", tools.order_lookup, {})

        result = registry.execute("order_lookup", {"unexpected": "value"})

        self.assertFalse(result["success"])
        self.assertEqual(result["error"], "invalid_arguments")

    def test_execution_ceiling_escalates(self):
        class LoopProvider:
            def generate(self, messages, tool_schemas):
                from resolution_agent.providers import ModelResponse

                return ModelResponse(tool_calls=[{
                    "id": "unknown",
                    "name": "not_registered",
                    "arguments": {},
                }])

        agent = ResolutionAgent(LoopProvider(), max_iterations=2)
        result = agent.run("Keep calling tools")

        self.assertEqual(result["status"], "escalated")
        self.assertIn("Execution ceiling", result["message"])


if __name__ == "__main__":
    unittest.main()
