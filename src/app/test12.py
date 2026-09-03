from ollama import chat
from .toolsService import ToolsService
import time

from .tools import tools

MODEL = "isotnek/qwen3.5:9B-Unsloth-UD-Q4_K_XL"

service = ToolsService()

memory = []
overview_log = []


def run_agent(user_input):
  while True:
    start = time.perf_counter()

    response = chat(
        model=MODEL,
        messages=memory,
        tools=tools,
    )

    elapsed = time.perf_counter() - start
    memory.append(response.message)

    print(f"Response took: {elapsed:.2f} seconds")

    # No tool call — final answer
    if not response.message.tool_calls:
        overview_log.append({
            "user_input": user_input,
            "tool": None,
            "time": elapsed,
        })
        print(response.message.content)
        break

    # Model requested tool(s)
    for tool_call in response.message.tool_calls:
        tool_name = tool_call.function.name
        arguments = tool_call.function.arguments

        print(f"Model wants to run: {tool_name}({arguments})")

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
            "content": str(result),   # safety net, as discussed earlier
        })

        overview_log.append({
            "user_input": user_input,
            "tool": tool_name,
            "time": elapsed,
        })


def print_overview():
  print("\nOverview:")
  for item in overview_log:
      print(
          f"User: {item['user_input']} | "
          f"Tool: {item['tool']} | "
          f"Time: {item['time']:.2f}s"
      )
  print("-" * 50)


def main():
  while True:
      user_input = input("(exit , quit to stop):> ")

      if user_input.strip().lower() in ("exit", "quit"):
          break

      print("\nExecuting ...\n ")
      memory.append({
          "role": "user",
          "content": user_input,
      })

      run_agent(user_input)
      print_overview()