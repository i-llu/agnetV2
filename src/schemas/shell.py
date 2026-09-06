shell_tools = [
  {
        "type": "function",
        "function": {
            "name": "open_tabs",
            "description": "Open multiple URLs as tabs in one new Google Chrome window.",
            "parameters": {
                "type": "object",
                "properties": {
                    "urls": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of complete URLs to open."
                    }
                },
                "required": ["urls"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "run_shell_command",
            "description": (
                "Run an arbitrary shell command inside the current project directory. "
                "This project uses uv for Python package management — prefer 'uv add <package>' "
                "over 'pip install <package>', and 'uv remove <package>' over 'pip uninstall'."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {
                        "type": "string",
                        "description": "The full shell command to run.",
                    }
                },
                "required": ["command"],
            },
        },
    },
]