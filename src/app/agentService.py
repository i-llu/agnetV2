class AgentService:
  def __init__(self):
    self.system_prompt = (
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
    self.memory = []
    self.tools = {
        "read_file": "📖",
        "write_file": "📝",
        "execute_python": "🐍",
        "web_search": "🔎",
        "create_folder": "📁",
        "rename_file": "📄",
        "copy_file": "📄-📄",
        "move_file": "📁-➡️",
        "delete_file": "🗑️",
        "open_tabs":"🗂️"
      }

  def clear_memory(self):
    sys_mem = self.memory[0]
    self.memory.clear()
    self.memory.append(sys_mem)

  def clear_fully(self):
    self.memory.clear()

  def show_memory(self):
    return "\n\n".join(str(message) for message in self.memory)

  def show_tools(self):
    return "\n".join(f"{emoji} {tool}\n"for tool, emoji in self.tools.items())

  def personality(self):
    return self.system_prompt

