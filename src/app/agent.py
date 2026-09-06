import time
from ollama import chat

from .toolsService import ToolsService
from .tools_schema import tools

MODEL = "qwen3:4b"
#MODEL = "isotnek/qwen3.5:9B-Unsloth-UD-Q4_K_XL"


class Agent:

    def __init__(self):
        self.service = ToolsService()
        self.system_prompt = self.service.commands.system_prompt
        self.service.commands.memory.append({"role": "system", "content": self.system_prompt})
        self.overview_log = []
        self.turn_count = 0

        self.tool_emoji = self.service.commands.tools

        self.tool_handlers = {
            # FILES
            "read_file": self.service.files.read_file,
            "write_file": self.service.files.write_file,
            "rename_file": self.service.files.rename_file,
            "copy_file": self.service.files.copy_file,
            "move_file": self.service.files.move_file,
            "execute_python": self.service.files.execute_python,

            # FOLDERS
            "create_folder": self.service.folders.create_folder,
            "open_tabs": self.service.shell.open_tabs,

            # WEB
            "web_search": self.service.web.web_search,

            # TODOs
            "add_todos": self.service.todos.add_todos,
            "delete_todo": self.service.todos.delete_todo_by_id,
            "clear_todos": self.service.todos.clear_todos,
            "show_todos": self.service.todos.show_todos,
        }

    def _dispatch_tool(self, tool_name: str, arguments: dict, callbacks) -> str:
        memory = self.service.commands.memory
        handler = self.tool_handlers.get(tool_name)

        if handler:
            return handler(**arguments)

        elif tool_name == "delete_file":
            gen = self.service.files.delete_file(**arguments)
            msg = next(gen)
            if msg.startswith("Are you sure"):
                answer = callbacks.ask_confirmation(msg)
                try:
                    return gen.send(answer)
                except StopIteration:
                    return "Deletion flow ended unexpectedly"
            return msg

        elif tool_name == "clarify":
            gen = self.service.agent.clarify(**arguments)
            question = next(gen)
            answer = callbacks.ask_open_question(question)
            try:
                result = gen.send(answer)
            except StopIteration as e:
                result = e.value

            memory.append({"role": "assistant", "content": question})
            memory.append({"role": "user", "content": answer})
            return result

        elif tool_name == "run_shell_command":
            gen = self.service.shell.run_shell_command(**arguments)
            msg = next(gen)
            if msg.startswith("The agent wants to run:"):
                answer = callbacks.ask_confirmation(msg)
                try:
                    return gen.send(answer)
                except StopIteration:
                    return "Command flow ended unexpectedly"
            return msg

        else:
            return f"Unknown tool: {tool_name}"

    def run_turn(self, user_input: str, callbacks) -> None:
        memory = self.service.commands.memory
        memory.append({"role": "user", "content": user_input})

        while True:
            start = time.perf_counter()

            response_stream = chat(
                model=MODEL,
                messages=memory,
                tools=tools,
                stream=True,
            )

            tool_calls = None
            thinking_text = ""
            answer_text = ""

            for chunk in response_stream:
                piece_thinking = chunk.message.thinking or ""
                if piece_thinking:
                    thinking_text += piece_thinking
                    callbacks.on_thinking_chunk(thinking_text)

                piece = chunk.message.content or ""
                if piece:
                    answer_text += piece
                    callbacks.on_text_chunk(answer_text)

                if chunk.message.tool_calls:
                    tool_calls = chunk.message.tool_calls

            elapsed = time.perf_counter() - start
            self.turn_count += 1

            memory.append({
                "role": "assistant",
                "content": answer_text,
                "tool_calls": [
                    {
                        "function": {
                            "name": call.function.name,
                            "arguments": call.function.arguments,
                        }
                    }
                    for call in tool_calls
                ] if tool_calls else [],
            })

            if not tool_calls:
                self.overview_log.append({
                    "user_input": user_input,
                    "tool": None,
                    "time": elapsed,
                })
                callbacks.on_turn_done(answer_text, elapsed)
                return

            for tool_call in tool_calls:
                tool_name = tool_call.function.name
                arguments = tool_call.function.arguments

                callbacks.on_tool_call(tool_name, arguments, self.tool_emoji)

                result = self._dispatch_tool(tool_name, arguments, callbacks)

                memory.append({
                    "role": "tool",
                    "content": str(result),
                })

                self.overview_log.append({
                    "user_input": user_input,
                    "tool": tool_name,
                    "time": elapsed,
                })