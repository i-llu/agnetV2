class AgentService:
  def __init__(self):
    self.memory = []

  def clear_memory(self):
    sys_mem = self.memory[0]
    self.memory.clear()
    self.memory.append(sys_mem)
    print("cleared the memory , starting fresh")