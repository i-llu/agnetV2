class AgentService:
  def delete_memory(self):
    system_memory = self.memory[0]
    self.memory.clear()
    self.memory.append(system_memory)

    print("memory deleted, starting fresh")