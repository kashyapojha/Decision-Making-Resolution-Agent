TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "order_lookup",
            "description": "Retrieve an order's customer, item, status, and exchange eligibility using its exact order identifier.",
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {
                        "type": "string",
                        "description": "Exact order identifier, for example ORD-1001.",
                    }
                },
                "required": ["order_id"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "inventory_inspection",
            "description": "Check the real-time stock count and replacement availability for an item identifier.",
            "parameters": {
                "type": "object",
                "properties": {
                    "item_id": {
                        "type": "string",
                        "description": "Exact item identifier retrieved from order_lookup.",
                    }
                },
                "required": ["item_id"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "refund_processing",
            "description": "Issue a financial refund only when an exchange is unavailable or ineligible.",
            "parameters": {
                "type": "object",
                "properties": {
                    "order_id": {
                        "type": "string",
                        "description": "Exact order identifier to refund.",
                    },
                    "reason": {
                        "type": "string",
                        "description": "Clear reason for the refund, such as damaged or replacement unavailable.",
                    },
                },
                "required": ["order_id", "reason"],
                "additionalProperties": False,
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "customer_notification",
            "description": "Dispatch the official resolution confirmation by email to the customer.",
            "parameters": {
                "type": "object",
                "properties": {
                    "email": {
                        "type": "string",
                        "description": "Customer email address retrieved from order_lookup.",
                    },
                    "message": {
                        "type": "string",
                        "description": "Clear, polite resolution summary for the customer.",
                    },
                },
                "required": ["email", "message"],
                "additionalProperties": False,
            },
        },
    },
]
