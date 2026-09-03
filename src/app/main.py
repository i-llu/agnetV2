from ollama import chat
from .toolsService import ToolsService
import time

from .tools import tools

MODEL = "isotnek/qwen3.5:9B-Unsloth-UD-Q4_K_XL"

service = ToolsService()

memory = []
overview = []

tools = tools


while True:
    user_input = input("(exit , quit to stop):> ")

    if user_input.strip().lower() in ("exit", "quit"):
        break

    print("\nExecuting ...\n ")
    memory.append({
        "role": "user",
        "content": user_input,
    })

    while True:
        # Start timer for this model request
        start = time.perf_counter()

        response = chat(
            model=MODEL,
            messages=memory,
            tools=tools,
        )

        # Stop timer
        elapsed = time.perf_counter() - start

        memory.append(response.message)

        print(f"Response took: {elapsed:.2f} seconds")

        # No tool call
        if not response.message.tool_calls:

            overview.append({
                "user_input": user_input,
                "tool": None,
                "time": elapsed,
            })

            print(response.message.content)
            break

        # Model requested a tool
        for tool_call in response.message.tool_calls:

            tool_name = tool_call.function.name
            arguments = tool_call.function.arguments

            print(
                f"Model wants to run: "
                f"{tool_name}({arguments})"
            )

            # Execute tool
            if tool_name == "read_file":
                result = service.read_file(**arguments)

            elif tool_name == "write_file":
                result = service.write_file(**arguments)

            elif tool_name == "execute_python":
                result = service.execute_python(**arguments)

            elif tool_name == "web_search":
                result = service.web_search(**arguments)

            elif tool_name == "create_folder":
                result = service.create_folder(**arguments)
            else:
                result = f"Unknown tool: {tool_name}"

            memory.append({
                "role": "tool",
                "content": result,
            })

            # Save overview
            overview.append({
                "user_input": user_input,
                "tool": tool_name,
                "time": elapsed,
            })

    # Print overview
    print("\nOverview:")

    for item in overview:
        print(
            f"User: {item['user_input']} | "
            f"Tool: {item['tool']} | "
            f"Time: {item['time']:.2f}s"
        )

    print("-" * 50)