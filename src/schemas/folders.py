folders_tools = [
    {
        "type": "function",
        "function": {
            "name": "create_folder",
            "description": "Create a new folder (and any missing parent folders) at the given path.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "The path of the folder to create, relative to the home directory.",
                    }
                },
                "required": ["path"],
            },
        },
    },
]