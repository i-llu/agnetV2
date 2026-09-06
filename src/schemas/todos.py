todos_tools = [
    {
        "type": "function",
        "function": {
            "name": "add_todos",
            "description": "Add one or more todos to the todo list.",
            "parameters": {
                "type": "object",
                "properties": {
                    "todos": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "A list of todo items to add."
                    }
                },
                "required": ["todos"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "delete_todo",
            "description": "Delete a todo by its ID.",
            "parameters": {
                "type": "object",
                "properties": {
                    "id": {
                        "type": "integer",
                        "description": "The ID of the todo to delete."
                    }
                },
                "required": ["id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "show_todos",
            "description": "Show all current todos.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
    {
        "type": "function",
        "function": {
            "name": "clear_todos",
            "description": "Delete all todos from the current todo list.",
            "parameters": {"type": "object", "properties": {}},
        },
    },
]