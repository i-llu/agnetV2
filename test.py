from src.app.toolsService import ToolsService

service = ToolsService()

result = service.delete_file("agent/text.txt")

print(result)