import time
import threading
from rich.text import Text
import subprocess

from ollama import chat
from textual import work
from textual.app import App, ComposeResult
from textual.containers import VerticalScroll
from textual.reactive import reactive
from textual.widgets import Footer, Input, Static

from .toolsService import ToolsService
from .tools_schema import tools

BANNER = subprocess.check_output(["figlet", "KIWI - AGENT"],text=True,)
MODEL = "qwen3:4b"
#MODEL = "isotnek/qwen3.5:9B-Unsloth-UD-Q4_K_XL"

service = ToolsService()

SYSTEM_PROMPT = service.system_prompt

service.memory.append({"role": "system","content":SYSTEM_PROMPT})
overview_log = []

TOOL_EMOJI = service.tools

tool_handlers = {
# FILES
    "read_file": service.read_file,
    "write_file": service.write_file,
    "rename_file": service.rename_file,
    "copy_file": service.copy_file,
    "move_file": service.move_file,
# FOLDERS
    "create_folder": service.create_folder,

    "execute_python": service.execute_python,

    "open_tabs": service.open_tabs,
# WEB
    "web_search": service.web_search,


    # TODOs
    "add_todos": service.add_todos,
    "delete_todo": service.delete_todo_by_id,
    "clear_todos":service.clear_todos,
    "show_todos": service.show_todos,
}

SLASH_COMMANDS = {
    "/help": "Shows available commands",

    "/clear": "Clear conversation memory (keeps personality)",
    "/clear -a":"Clears all memory with the persona",

    "/memory":"Shows current memory",

    "/tools":"Shows available tools",

    "/persona":"Shows personality of the agent",

    "/scr -c":"Clears the screen",

    "/todos":"Shows current todo list",
    "/todo -c":"Clear all todos"
}

# Rotating busy indicator, Hermes-style
BUSY_FACES = ["( ◕‿◕)", "( ◕ᴗ◕)", "(◕‿◕ )", "( ◕ᴗ◕)"]


class AgentApp(App):
    """Terminal UI styled after the Hermes Agent CLI, in light green."""

    CSS = """
    Screen {
        layout: vertical;
        background: #0D1017;
    }

    #banner {
        height: auto;
        background: #0D1017;
        color: #DA3450;
        text-align: center;
        padding: 1 2;
    }

    #chat-scroll {
        height: 1fr;
        background: #0D1017;
        color: #c9d1d9;
        padding: 0 2;
    }

    .msg {
        height: auto;
        margin: 0 0 1 0;
    }

    #command-hint {
        height: auto;
        background: #0D1017;
        color: #8a8f98;
        padding: 0 2;
        display: none;
    }

    #statusbar {
        height: 1;
        background: #0D1017;
        color: #DA3450;
        padding: 0 2;
    }

    Input {
        dock: bottom;
        background: #0D1017;
        color: #DA3450;
        border: round #DA3450;
        margin: 0 1 1 1;
    }

    Input:focus {
        border: round #DA3450;
    }

    Input > .input--placeholder {
        color: #DA3450;
    }

    Footer {
        background: #0D1017;
        color: #DA3450;
    }
    """

    BINDINGS = [
        ("ctrl+c", "quit", "Quit"),
    ]

    tokens_used = reactive(0)
    turn_count = reactive(0)
    session_start = reactive(0.0)
    busy = reactive(False)
    busy_frame = reactive(0)

    def __init__(self):
        super().__init__()
        self._pending_confirmation: threading.Event | None = None
        self._confirmation_answer: str = ""

    def compose(self) -> ComposeResult:
        yield Static(self._banner_text(), id="banner")
        yield VerticalScroll(id="chat-scroll")
        yield Static("", id="command-hint")
        yield Static(self._status_text(), id="statusbar")
        yield Input(placeholder="Ready — type a message and press Enter (or 'exit' to quit)...")
        yield Footer()

    def _banner_text(self):
        text = Text()

        colors = [
            "#DA3450",
            "#DE4861",
            "#FF6B81",
            "#FF8FA3",
        ]

        for i, line in enumerate(BANNER.splitlines()):
            text.append(line + "\n", style=colors[i % len(colors)])

        return text

    def _status_text(self) -> str:
        elapsed_min = (time.perf_counter() - self.session_start) / 60 if self.session_start else 0
        face = BUSY_FACES[self.busy_frame % len(BUSY_FACES)] if self.busy else "⚕"
        bar_filled = min(10, self.turn_count)
        bar = "█" * bar_filled + "░" * (10 - bar_filled)
        return (
            f"{face} [#DA3450]{MODEL}[/#DA3450]  │  "
            f"turns: {self.turn_count}  │  "
            f"[{bar}]  │  {elapsed_min:.0f}m"
        )

    def on_mount(self) -> None:
        self.session_start = time.perf_counter()
        self.query_one(Input).focus()
        self.set_interval(0.4, self._tick_busy_indicator)

    def _tick_busy_indicator(self) -> None:
        if self.busy:
            self.busy_frame += 1
            self.query_one("#statusbar", Static).update(self._status_text())

    def _add_message(self, text: str) -> Static:
        chat_scroll = self.query_one("#chat-scroll", VerticalScroll)
        widget = Static(text, classes="msg")
        chat_scroll.mount(widget)
        chat_scroll.scroll_end(animate=False)
        return widget

    def ask_confirmation(self, question: str) -> str:
        self._pending_confirmation = threading.Event()
        self.call_from_thread(
            self._add_message,
            f"[bold #DA3450]⚠ {question}[/bold #DA3450]",
        )
        self.call_from_thread(
            lambda: setattr(self.query_one(Input), "placeholder", "y/n...")
        )
        self._pending_confirmation.wait()
        return self._confirmation_answer

    # NEW: live slash-command suggestions as you type "/"
    def on_input_changed(self, event: Input.Changed) -> None:
        hint = self.query_one("#command-hint", Static)
        value = event.value

        if not value.startswith("/"):
            hint.display = False
            return

        matches = [
            f"[bold #DA3450]{cmd}[/bold #DA3450] — {desc}"
            for cmd, desc in SLASH_COMMANDS.items()
            if cmd.startswith(value.lower())
        ]

        if matches:
            hint.update("\n".join(matches))
            hint.display = True
        else:
            hint.display = False

    def on_input_submitted(self, event: Input.Submitted) -> None:
        user_input = event.value.strip()
        self.query_one(Input).value = ""
        self.query_one("#command-hint", Static).display = False

        if self._pending_confirmation is not None:
            self._add_message(f"[bold #DA3450]›[/bold #DA3450] {user_input}")
            self._confirmation_answer = user_input
            self._pending_confirmation.set()
            self._pending_confirmation = None
            self.query_one(Input).placeholder = "Ready — type a message and press Enter (or 'exit' to quit)..."
            return

        if not user_input:
            return

        if user_input.lower() in ("exit", "quit"):
            self.exit()
            return

        self._add_message(
            f"[bold #DA3450]›[/bold #DA3450] [bold #c9d1d9]{user_input}[/bold #c9d1d9]"
        )

        # Slash commands handled locally, instantly, no model call
        if user_input.startswith("/"):
            self.slash_commands(user_input)
            return

        service.memory.append({
            "role": "user",
            "content": user_input,
        })

        self.busy = True
        self.query_one("#statusbar", Static).update(self._status_text())
        self.run_agent(user_input)

    def ask_open_question(self, question: str) -> str:
        self._pending_confirmation = threading.Event()
        self.call_from_thread(
            self._add_message,
            f"[bold #DA3450]❓ {question}[/bold #DA3450]",
        )
        self.call_from_thread(
            lambda: setattr(self.query_one(Input), "placeholder", "Type your answer...")
        )
        self._pending_confirmation.wait()
        return self._confirmation_answer

    def _clear_chat_screen(self) -> None:
        chat_scroll = self.query_one("#chat-scroll", VerticalScroll)
        chat_scroll.remove_children()

    def slash_commands(self, user_input: str) -> None:
        match user_input.strip().lower():
            case "/help":
                lines = [f"{cmd} — {desc}" for cmd, desc in SLASH_COMMANDS.items()]
                self._add_message("[bold #DA3450][!][/bold #DA3450] Available commands:\n" + "\n".join(lines))
            case "/clear":
                service.clear_memory()
                self._add_message("[bold #DA3450][✓][/bold #DA3450] Memory cleared.")
            case "/clear -a":
                service.clear_fully()
                self._add_message("[bold #DA3450][✓][/bold #DA3450] Memory with the persona are cleared / switching to default ai.")
            case "/memory":
                mem = service.show_memory()
                count = len(service.memory)
                self._add_message("[bold #DA3450][✓][/bold #DA3450] Showing memory")
                self._add_message(f"[bold #DA3450][/bold #DA3450] {mem}")
                self._add_message(f"[bold #DA3450][✓][/bold #DA3450] found: {count} item/s")
            case "/tools":
                tools = service.show_tools()
                self._add_message("[bold #DA3450][✓] Available tools:[/bold #DA3450]\n"+ tools)
            case "/persona":
                self._add_message(f"[bold #DA3450] ♆ [/bold #DA3450] {service.personality()}")
            case "/scr -c":
                self._clear_chat_screen()

            case "/todos":
                self._add_message(f"[bold #DA3450] ♆ [/bold #DA3450] {service.show_todos()}")

            case "/todo -c":
                service.clear_todos()
                self._add_message("[bold #DA3450][✓][/bold #DA3450] TODOS cleared")

            case _:
                self._add_message(
                    f"[bold #DA3450]✓[/bold #DA3450] Unknown command {user_input}, try /help to see all commands"
                )

    @work(thread=True)
    def run_agent(self, user_input: str) -> None:
        chat_scroll = self.query_one("#chat-scroll", VerticalScroll)

        while True:
            start = time.perf_counter()

            response_stream = chat(
                model=MODEL,
                messages=service.memory,
                tools=tools,
                stream=True,
            )
            tool_calls = None

            thinking_text = ""
            answer_text = ""

            thinking_widget = None
            response_widget = None

            for chunk in response_stream:

                # -------------------------
                # THINKING
                # -------------------------
                piece_thinking = chunk.message.thinking or ""

                if piece_thinking:
                    thinking_text += piece_thinking

                    rendered = (
                        f"[bold #DA3450]::[/bold #DA3450] "
                        f"[bold #DE4861]{thinking_text}[/bold #DE4861]"
                    )

                    if thinking_widget is None:
                        thinking_widget = self.call_from_thread(
                            self._add_message,
                            rendered,
                        )
                    else:
                        self.call_from_thread(
                            thinking_widget.update,
                            rendered,
                        )

                    self.call_from_thread(
                        lambda: chat_scroll.scroll_end(animate=False)
                    )

                # -------------------------
                # FINAL ANSWER
                # -------------------------
                piece = chunk.message.content or ""

                if piece:
                    answer_text += piece

                    rendered = (
                        f"[bold #DA3450]●[/bold #DA3450] "
                        f"{answer_text}"
                    )

                    if response_widget is None:
                        response_widget = self.call_from_thread(
                            self._add_message,
                            rendered,
                        )
                    else:
                        self.call_from_thread(
                            response_widget.update,
                            rendered,
                        )

                    self.call_from_thread(
                        lambda: chat_scroll.scroll_end(animate=False)
                    )

                if chunk.message.tool_calls:
                    tool_calls = chunk.message.tool_calls

            elapsed = time.perf_counter() - start
            self.turn_count += 1

            service.memory.append({
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
                overview_log.append({
                    "user_input": user_input,
                    "tool": None,
                    "time": elapsed,
                })
                if response_widget is not None:
                    self.call_from_thread(
                        response_widget.update,
                        f"[bold #DA3450]●[/bold #DA3450] {answer_text}  "
                        f"[#DA3450]({elapsed:.2f}s)[/#DA3450]",
                    )
                else:
                    self.call_from_thread(
                        self._add_message,
                        f"[bold #DA3450]●[/bold #DA3450] {answer_text}  "
                        f"[#DA3450]({elapsed:.2f}s)[/#DA3450]",
                    )
                self.call_from_thread(self._finish_turn)
                break

            for tool_call in tool_calls:
                tool_name = tool_call.function.name
                arguments = tool_call.function.arguments
                emoji = TOOL_EMOJI.get(tool_name, "⚙️")

                self.call_from_thread(
                    self._add_message,
                    f"[#DA3450]{emoji} {tool_name}[/#DA3450] "
                    f"[#DA3450]{arguments}[/#DA3450]",
                )

                handler = tool_handlers.get(tool_name)

                if handler:
                    result = handler(**arguments)

                elif tool_name == "delete_file":
                    gen = service.delete_file(**arguments)
                    msg = next(gen)
                    if msg.startswith("Are you sure"):
                        answer = self.ask_confirmation(msg)
                        try:
                            result = gen.send(answer)
                        except StopIteration:
                            result = "Deletion flow ended unexpectedly"
                    else:
                        result = msg

                elif tool_name == "clarify":
                    gen = service.clarify(**arguments)

                    question = next(gen)

                    answer = self.ask_open_question(question)

                    try:
                        result = gen.send(answer)
                    except StopIteration as e:
                        result = e.value

                    service.memory.append({"role": "assistant","content": question, })
                    service.memory.append({"role": "user","content": answer,})

                elif tool_name == "run_shell_command":
                    gen = service.run_shell_command(**arguments)
                    msg = next(gen)
                    if msg.startswith("The agent wants to run:"):
                        answer = self.ask_confirmation(msg)
                        try:
                            result = gen.send(answer)
                        except StopIteration:
                            result = "Command flow ended unexpectedly"
                    else:
                        result = msg

                else:
                    result = f"Unknown tool: {tool_name}"

                service.memory.append({
                    "role": "tool",
                    "content": str(result),  # safety net: tool content must be a string
                })

                overview_log.append({
                    "user_input": user_input,
                    "tool": tool_name,
                    "time": elapsed,
                })

    def _finish_turn(self) -> None:
        self.busy = False
        self.query_one("#statusbar", Static).update(self._status_text())


def main():
    AgentApp().run()


if __name__ == "__main__":
    main()