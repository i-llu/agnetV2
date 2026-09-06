class AgentService:
  def clarify(self, content: str):
    answer = yield content
    return answer