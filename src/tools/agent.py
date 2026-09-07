from playsound3 import playsound

class AgentService:
  def clarify(self, content: str):
    playsound("sounds/ter_sound.mp3")
    answer = yield content
    return answer