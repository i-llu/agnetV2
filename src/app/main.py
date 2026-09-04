import time
import threading

from ollama import chat
from textual import work
from textual.app import App, ComposeResult
from textual.containers import VerticalScroll
from textual.reactive import reactive
from textual.widgets import Footer, Input, Static

from .toolsService import ToolsService
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
memory = [{"role": "system","content":SYSTEM_PROMPT}]
overview_log = []

TOOL_EMOJI = {
    "read_file": "📖 ",
    "write_file": "📝 ",
    "execute_python": "🐍 ",
    "web_search": "🔎 ",
    "create_folder": "📁 ",
    "rename_file":"📄 ",
    "copy_file":"📄-📄 ",
    "move_file":"📁-➡️ ",
    "delete_file":"🗑️ "
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
        padding: 1 2;
        border-bottom: solid #DA3450;
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
        yield Static(self._status_text(), id="statusbar")
        yield Input(placeholder="Ready — type a message and press Enter (or 'exit' to quit)...")
        yield Footer()

    def _banner_text(self) -> str:
        tool_names = ", ".join(TOOL_EMOJI.keys())
        return (
            f"[bold #DA3450]Kiwi AGENT[/bold #DA3450]  "
            f"[#DA3450]│[/#DA3450]  model: [#DA3450]{MODEL}[/#DA3450]\n"
            f"[#DA3450]tools:[/#DA3450] {tool_names}"
        )

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

    # NEW: blocks the worker thread until the user types a y/n answer
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

    def on_input_submitted(self, event: Input.Submitted) -> None:
        user_input = event.value.strip()
        self.query_one(Input).value = ""

        # NEW: route the answer to the waiting confirmation instead of chat
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

        memory.append({
            "role": "user",
            "content": user_input,
        })

        self.busy = True
        self.query_one("#statusbar", Static).update(self._status_text())
        self.run_agent(user_input)

    @work(thread=True)
    def run_agent(self, user_input: str) -> None:
        chat_scroll = self.query_one("#chat-scroll", VerticalScroll)

        while True:
            start = time.perf_counter()

            response_stream = chat(
                model=MODEL,
                messages=memory,
                tools=tools,
                stream=True,
            )

            accumulated_text = ""
            tool_calls = None
            response_widget = None

            for chunk in response_stream:
                piece = chunk.message.content or ""
                if piece:
                    accumulated_text += piece

                    if response_widget is None:
                        response_widget = self.call_from_thread(
                            self._add_message,
                            f"[bold #DA3450]●[/bold #DA3450] {accumulated_text}",
                        )
                    else:
                        self.call_from_thread(
                            response_widget.update,
                            f"[bold #DA3450]●[/bold #DA3450] {accumulated_text}",
                        )
                        self.call_from_thread(
                            lambda: chat_scroll.scroll_end(animate=False)
                        )

                if chunk.message.tool_calls:
                    tool_calls = chunk.message.tool_calls

            elapsed = time.perf_counter() - start
            self.turn_count += 1

            memory.append({
                "role": "assistant",
                "content": accumulated_text,
                "tool_calls": tool_calls,
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
                        f"[bold #DA3450]●[/bold #DA3450] {accumulated_text}  "
                        f"[#DA3450]({elapsed:.2f}s)[/#DA3450]",
                    )
                else:
                    self.call_from_thread(
                        self._add_message,
                        f"[bold #DA3450]●[/bold #DA3450] {accumulated_text}  "
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
                else:
                    result = f"Unknown tool: {tool_name}"

                memory.append({
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