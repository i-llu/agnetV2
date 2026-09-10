from playsound3 import playsound
from pathlib import Path

SOUND_DIR = Path(__file__).parent.parent / "sounds"

class AgentService:

  def __init__(self):
    self.MODELS = [
      "qwen2.5:3b-instruct",
      "qwen3:4b",

    ]
    self.current = self.MODELS[0]

  def current_model(self):
    return self.current

  def change_model(self, num: int):
    self.current = self.MODELS[num]

    return self.current

  def show_models(self):
    return self.MODELS

  def clarify(self, content: str):
    playsound(f"{SOUND_DIR}/ter_sound.mp3")
    answer = yield content
    return answer
