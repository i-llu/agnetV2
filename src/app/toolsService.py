import tools

class ToolsService():

  def __init__(self):
    self.todos = tools.TodoService()
    self.files = tools.FilesService()
    self.web = tools.WebService()
    self.shell = tools.ShellService()
    self.commands = tools.CommandsService()
    self.agent = tools.AgentService()
    self.folders = tools.FolderService()

