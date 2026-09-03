tools = [
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
                    },
                    "content": {
                        "type": "string",
                        "description": "The text content to write into the file",
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
          "description": "write or rewrite the file.",
          "parameters": {
              "type": "object",
              "properties": {
                  "path": {
                      "type": "string",
                      "description": "The path to the file to write or rewrite",
                  }
              },
              "required": ["path","content"],
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
                    "items": {
                        "type": "string"
                    },
                    "description": "Optional command-line arguments to pass to the Python file."
                }
            },
            "required": ["path"]
        }
    }
},
{
    "type": "function",
    "function": {
        "name": "web_search",
        "description": "Search the web for current information.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "The search query.",
                }
            },
            "required": ["query"],
        },
    },
},
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