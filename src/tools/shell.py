import subprocess
from playsound3 import playsound
from pathlib import Path

PARENT_DIR = Path.cwd()

class ShellService:

  def open_tabs(self, urls: list[str]) -> str:
    command = ["google-chrome", "--new-window", *urls]

    try:
        subprocess.Popen(command)
        return f"Opened {len(urls)} tabs"
    except OSError as e:
        return f"Failed to open tabs: {e}"

  def run_shell_command(self, command: str):
    playsound("sounds/ter_sound.mp3")
    answer = yield f"The agent wants to run: {command}\nAllow it? (y/n)"

    if answer is None or answer.strip().lower() != "y":
        yield "Command cancelled by user."
        return

    try:
        result = subprocess.run(
            command,
            shell=True,
            cwd=PARENT_DIR,
            capture_output=True,
            text=True,
            timeout=120,
        )
        yield (
            f"Exit code: {result.returncode}\n"
            f"STDOUT:\n{result.stdout}\n"
            f"STDERR:\n{result.stderr}"
        )
    except subprocess.TimeoutExpired:
        yield "Command timed out after 120 seconds."
    except OSError as e:
        yield f"Failed to run command: {e}"