import time
import threading
import subprocess
from rich.text import Text
from rich.markup import escape

from textual import work
from textual.app import App, ComposeResult
from textual.containers import VerticalScroll
from textual.reactive import reactive
from textual.widgets import Footer, Input, Static

from .agent import Agent

BANNER = subprocess.check_output(["figlet", "KIWI - AGENT"], text=True)

SLASH_COMMANDS = {
    "/help": "Shows available commands\n\n",
    "/clear": "Clear conversation memory (keeps personality)",
    "/clear -a": "Clears all memory with the persona\n",
    "/memory": "Shows current memory\n",
    "/tools": "Shows available tools\n",
    "/persona": "Shows personality of the agent\n",
    "/scr -c": "Clears the screen\n",
    "/todos": "Shows current todo list",
    "/todo -c": "Clear all todos\n",
    "/model -c":"Change the model starting with the index 0 -> type /model -c {index}",
    "/models":"Show current models that are available"
}

BUSY_FACES = ["( ◕‿◕)", "( ◕ᴗ◕)", "(◕‿◕ )", "( ◕ᴗ◕)"]


class TextualAgentCallbacks:
    """Translates Agent events into Textual widget updates. No chat logic here."""

    def __init__(self, app: "AgentApp"):
        self.app = app
        self.thinking_widget = None
        self.response_widget = None

    def on_thinking_chunk(self, thinking_text: str) -> None:
        rendered = (
            f"[bold #DA3450]::[/bold #DA3450] "
            f"[bold #DE4861]{escape(thinking_text)}[/bold #DE4861]"
        )
        if self.thinking_widget is None:
            self.thinking_widget = self.app.call_from_thread(self.app._add_message, rendered)
        else:
            self.app.call_from_thread(self.thinking_widget.update, rendered)
        self.app.call_from_thread(self.app._scroll_chat_end)

    def on_text_chunk(self, answer_text: str) -> None:
        rendered = f"[bold #DA3450]●[/bold #DA3450] {escape(answer_text)}"
        if self.response_widget is None:
            self.response_widget = self.app.call_from_thread(self.app._add_message, rendered)
        else:
            self.app.call_from_thread(self.response_widget.update, rendered)
        self.app.call_from_thread(self.app._scroll_chat_end)

    def on_tool_call(self, tool_name: str, arguments: dict, tool_emoji: dict) -> None:
        emoji = tool_emoji.get(tool_name, "⚙️")
        self.app.call_from_thread(
            self.app._add_message,
            f"[#DA3450]{emoji} {tool_name}[/#DA3450] "
            f"[#DA3450]{escape(str(arguments))}[/#DA3450]",
        )

    def on_turn_done(self, answer_text: str, elapsed: float) -> None:
        text = (
            f"[bold #DA3450]●[/bold #DA3450] {escape(answer_text)}  "
            f"[#DA3450]({elapsed:.2f}s)[/#DA3450]"
        )
        if self.response_widget is not None:
            self.app.call_from_thread(self.response_widget.update, text)
        else:
            self.app.call_from_thread(self.app._add_message, text)
        self.app.call_from_thread(self.app._finish_turn)

    def ask_confirmation(self, question: str) -> str:
        return self.app.ask_confirmation(question)

    def ask_open_question(self, question: str) -> str:
        return self.app.ask_open_question(question)


class AgentApp(App):

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
        self.agent = Agent()
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
        colors = ["#DA3450", "#DE4861", "#FF6B81", "#FF8FA3"]
        for i, line in enumerate(BANNER.splitlines()):
            text.append(line + "\n", style=colors[i % len(colors)])
        return text

    def _status_text(self) -> str:
        elapsed_min = (time.perf_counter() - self.session_start) / 60 if self.session_start else 0
        face = BUSY_FACES[self.busy_frame % len(BUSY_FACES)] if self.busy else "⚕"
        bar_filled = min(10, self.turn_count)
        bar = "█" * bar_filled + "░" * (10 - bar_filled)
        model = self.agent.service.agent.current_model()
        return (
            f"{face} [#DA3450]{model}[/#DA3450]  │  "
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

    def _scroll_chat_end(self) -> None:
        self.query_one("#chat-scroll", VerticalScroll).scroll_end(animate=False)

    def ask_confirmation(self, question: str) -> str:
        self._pending_confirmation = threading.Event()
        self.call_from_thread(self._add_message, f"[bold #DA3450]⚠ {escape(question)}[/bold #DA3450]")
        self.call_from_thread(lambda: setattr(self.query_one(Input), "placeholder", "y/n..."))
        self._pending_confirmation.wait()
        return self._confirmation_answer

    def ask_open_question(self, question: str) -> str:
        self._pending_confirmation = threading.Event()
        self.call_from_thread(self._add_message, f"[bold #DA3450]❓ {escape(question)}[/bold #DA3450]")
        self.call_from_thread(lambda: setattr(self.query_one(Input), "placeholder", "Type your answer..."))
        self._pending_confirmation.wait()
        return self._confirmation_answer

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
            self._add_message(f"[bold #DA3450]›[/bold #DA3450] {escape(user_input)}")
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
            f"[bold #DA3450]›[/bold #DA3450] [bold #c9d1d9]{escape(user_input)}[/bold #c9d1d9]"
        )

        if user_input.startswith("/"):
            self.slash_commands(user_input)
            return

        self.busy = True
        self.query_one("#statusbar", Static).update(self._status_text())
        self.run_agent(user_input)

    def _clear_chat_screen(self) -> None:
        self.query_one("#chat-scroll", VerticalScroll).remove_children()

    def slash_commands(self, user_input: str) -> None:
        service = self.agent.service
        command = user_input.strip().lower()


        if command.startswith("/model -c "):
            try:
                num = int(command.split()[-1])

                model = service.agent.change_model(num)

                self._add_message(
                    f"[bold #DA3450][✓][/bold #DA3450] Model changed to {model}"
                )
                self.query_one("#statusbar", Static).update(
                    self._status_text()
                )

            except ValueError:
                self._add_message(
                    "[bold #DA3450][!][/bold #DA3450] Usage: /model -c <number>"
                )

            return
        match user_input.strip().lower():
            case "/help":
                lines = [f"{cmd} — {desc}" for cmd, desc in SLASH_COMMANDS.items()]
                self._add_message("[bold #DA3450][!][/bold #DA3450] Available commands:\n" + "\n".join(lines))
            case "/clear":
                service.commands.clear_memory()
                self._add_message("[bold #DA3450][✓][/bold #DA3450] Memory cleared.")
            case "/clear -a":
                service.commands.clear_fully()
                self._add_message("[bold #DA3450][✓][/bold #DA3450] Memory with the persona are cleared / switching to default ai.")
            case "/memory":
                mem = service.commands.show_memory()
                count = len(service.commands.memory)
                self._add_message("[bold #DA3450][✓][/bold #DA3450] Showing memory")
                self._add_message(f"[bold #DA3450][/bold #DA3450] {escape(mem)}")
                self._add_message(f"[bold #DA3450][✓][/bold #DA3450] found: {count} item/s")
            case "/tools":
                tool_list = service.commands.show_tools()
                self._add_message("[bold #DA3450][✓] Available tools:[/bold #DA3450]\n" + escape(tool_list))
            case "/persona":
                self._add_message(f"[bold #DA3450] ♆ [/bold #DA3450] {escape(service.commands.personality())}")
            case "/scr -c":
                self._clear_chat_screen()
            case "/todos":
                self._add_message(f"[bold #DA3450] ♆ [/bold #DA3450] {escape(service.todos.show_todos())}")
            case "/todo -c":
                service.todos.clear_todos()
                self._add_message("[bold #DA3450][✓][/bold #DA3450] TODOS cleared")
            case "/models":
                models = service.agent.show_models()
                self._add_message(f"[bold #DA3450][✓][/bold #DA3450]MODELS -> {models}")
            case _:
                self._add_message(
                    f"[bold #DA3450]✓[/bold #DA3450] Unknown command {escape(user_input)}, try /help to see all commands"
                )

    @work(thread=True)
    def run_agent(self, user_input: str) -> None:
        callbacks = TextualAgentCallbacks(self)
        self.agent.run_turn(user_input, callbacks)
        self.turn_count = self.agent.turn_count

    def _finish_turn(self) -> None:
        self.busy = False
        self.query_one("#statusbar", Static).update(self._status_text())


def main():
    AgentApp().run()


if __name__ == "__main__":
    main()