files_tools = [
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read a text file and return its contents.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "The path to the text file to read.",
                    }
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Write or rewrite a file with the given content.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "The path to the file to write or rewrite",
                    },
                    "content": {
                        "type": "string",
                        "description": "The text content to write into the file",
                    }
                },
                "required": ["path", "content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "rename_file",
            "description": "Rename a file or folder, keeping it in the same directory.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "The current path of the file or folder, relative to the home directory.",
                    },
                    "name": {
                        "type": "string",
                        "description": "The new name for the file or folder (name only, not a full path).",
                    }
                },
                "required": ["path", "name"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "copy_file",
            "description": "Copy a file to a new location, leaving the original in place.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "The path of the file to copy, relative to the home directory.",
                    },
                    "dest": {
                        "type": "string",
                        "description": "The destination path where the copy should be created, relative to the home directory.",
                    }
                },
                "required": ["path", "dest"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "move_file",
            "description": "Move a file to a new location, optionally renaming it in the process.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "The current path of the file to move, relative to the home directory.",
                    },
                    "dest": {
                        "type": "string",
                        "description": "The destination path for the file, relative to the home directory.",
                    }
                },
                "required": ["path", "dest"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "delete_file",
            "description": "Delete a file. Only works on files, not folders.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "The path of the file to delete, relative to the home directory.",
                    }
                },
                "required": ["path"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "execute_python",
            "description": "Execute a Python file with optional command-line arguments and return its output and errors.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {
                        "type": "string",
                        "description": "Path to the Python file to execute."
                    },
                    "args": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Optional command-line arguments to pass to the Python file."
                    }
                },
                "required": ["path"]
            }
        }
    },

]