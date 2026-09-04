from .toolsService import ToolsService

class AgentService(ToolsService):
  def delete_memory(self):
    system_memory = self.memory[0]
    self.memory.clear()
    self.memory.append(system_memory)
    return "memory deleted, starting fresh"