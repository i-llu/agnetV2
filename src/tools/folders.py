from pathlib import Path

PARENT_DIR = Path.cwd()

class FolderService:
  def create_folder(self, path: str) -> str:
    folder_path = PARENT_DIR / path
    try:
        folder_path.mkdir(parents=True, exist_ok=True)
        return f"Successfully created folder: {path}"
    except OSError as e:
        return f"Failed to create folder {path}: {e}"