agent_tools = [
    {
        "type": "function",
        "function": {
            "name": "clarify",
            "description": (
                "Ask the user a clarifying question when their request is ambiguous "
                "or missing information you need. This pauses and waits for their "
                "reply before continuing — use it instead of guessing."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "content": {
                        "type": "string",
                        "description": "The question to ask the user.",
                    }
                },
                "required": ["content"],
            },
        },
    },
]