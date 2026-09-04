from ollama import chat
from .toolsService import ToolsService
from .agentService import AgentService
import time
from .tools import tools

MODEL = "isotnek/qwen3.5:9B-Unsloth-UD-Q4_K_XL"
service = ToolsService()

SYSTEM_PROMPT = (
    "You are Kiwi, a witty and sharp AI assistant with a warm, personable style — "
    "think Jarvis or Friday from Iron Man: quick, capable, a little playful, and "
    "genuinely on the user's side, like a close friend who happens to be brilliant "
    "at getting things done. You speak naturally and conversationally, not like a "
    "generic assistant — you can be dry, a bit cheeky, and confident, while always "
    "being helpful and clear.\n\n"
    "You have access to tools for reading files, writing files, creating folders, "
    "executing Python scripts, and searching the web. Use tools when they help "
    "answer the user's request accurately, and narrate what you're doing the way "
    "a capable friend would — briefly and naturally, not robotically.\n\n"
    "Keep responses concise and clear. Skip unnecessary formality, but never "
    "sacrifice accuracy or usefulness for personality — the charm is a bonus, not "
    "a replacement for actually helping."
)

service.memory.append({"role": "system","content":SYSTEM_PROMPT})
overview_log = []


def run_agent(user_input):

    while True:

        start = time.perf_counter()

        response = chat(model=MODEL,messages=service.memory,tools=tools,stream=True,)

        full_content = ""
        full_thinking = ""
        tool_calls = []

        print("\n")

        for chunk in response:

            message = chunk.message

            if message.thinking:
                print(f"\033[90m{message.thinking}\033[0m", end="",flush=True)
                full_thinking += message.thinking

            if message.content:
                print(message.content, end="",flush=True)
                full_content += message.content

            if message.tool_calls:
                tool_calls.extend(message.tool_calls)

        elapsed = time.perf_counter() - start

        print(f"\n\nResponse took: {elapsed:.2f} seconds")

        assistant_message = {"role": "assistant","content": full_content, }

        if tool_calls:
            assistant_message["tool_calls"] = tool_calls

        service.memory.append(assistant_message)

        if not tool_calls:

            overview_log.append({"user_input": user_input,"tool": None,"time": elapsed,})
            break

        for tool_call in tool_calls:

            tool_name = tool_call.function.name
            arguments = tool_call.function.arguments

            print(
                f"\n\n\033[93m[Tool] "
                f"{tool_name}({arguments})\033[0m"
            )

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

            elif tool_name == "rename_file":
                result = service.rename_file(**arguments)

            elif tool_name == "copy_file":
                result = service.copy_file(**arguments)

            elif tool_name == "move_file":
                result = service.move_file(**arguments)

            elif tool_name == "delete_file":
                result = "not working at the moment ..."

            else:
                result = f"Unknown tool: {tool_name}"

            print(f"\033[92m[Tool result]\033[0m {result}")

            service.memory.append({ "role": "tool", "content": str(result),})

            overview_log.append({"user_input": user_input,"tool": tool_name,"time": elapsed,})

def print_overview():
  print("\nOverview:")
  for item in overview_log:
      print(
          f"User: {item['user_input']} | "
          f"Tool: {item['tool']} | "
          f"Time: {item['time']:.2f}s"
      )
  print("-" * 50)

def handle_slash_commd(command:str):

    match command:

        case "/help":
            print("showing commands")

        case "/clear":
            service.clear_memory()

        case _:
            print(f"Unknown command: {command}")



def main():
  while True:
      user_input = input("(exit , quit to stop):> ")

      if user_input.strip().lower() in ("exit", "quit"):
          break

      if user_input.startswith("/"):
         handle_slash_commd(user_input)
         continue

      print("\nExecuting ...\n ")
      service.memory.append({
          "role": "user",
          "content": user_input,
      })

      run_agent(user_input)
      print_overview()

main()