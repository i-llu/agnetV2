from pathlib import Path
from difflib import get_close_matches
import os
import subprocess
import requests
from src.config import Config

PARENT_DIR = Path.home()

class ToolsService:

  def __init__(self):
     self.files = []
     self.serpapi_key = Config.SERPAPI_KEY

  def get_similar(self,path:str,possibilities:list[str],n:int,cutoff:float):
     similar_files = get_close_matches(path,possibilities,n,cutoff)

     if similar_files:
      return (
          f"file: {path} was not found. "
          f"Did you mean: {', '.join(similar_files)}?"
      )

  def see_all_files(self,path:str):
     for file in (PARENT_DIR / path).parent.iterdir():

        if file.name.startswith("."):
          continue

        if file.is_file():
          self.files.append(file)
          print(file.name)

  def write_file(self, path: str, content: str) -> bool:
    file_path = PARENT_DIR / path
    try:
        os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        return "success"
    except OSError as e:
        print(f"Failed to write {path}: {e}")
        return False

  def create_folder(self, path: str) -> str:
    folder_path = PARENT_DIR / path
    try:
        folder_path.mkdir(parents=True, exist_ok=True)
        return f"Successfully created folder: {path}"
    except OSError as e:
        return f"Failed to create folder {path}: {e}"

  def read_file(self, path: str):
    self.see_all_files(path)

    file_path = PARENT_DIR / path

    if file_path.is_file():
       with open(file_path, "r", encoding="utf-8") as file:
          return file.read()

    file_names = [file.name for file in self.files]

    similar_files = self.get_similar(path,file_names,3,0.4)

    if not similar_files:
      return f'files {path} was not found and no similar files were found'

  def execute_python(self, path: str, args:list[str] | None = None) -> str:
    try:
      command = ["python3", str(PARENT_DIR / path)]

      if args:
         command.extend(args)

      result = subprocess.run(
          command,
          capture_output=True,
          text=True,
          timeout=30,
      )

      return (
          f"Exit code: {result.returncode}\n"
          f"STDOUT:\n{result.stdout}\n"
          f"STDERR:\n{result.stderr}"
      )

    except subprocess.TimeoutExpired:
      return f"Execution timed out after 30 seconds."

    except OSError as e:
      return f"Failed to execute {path}: {e}"

  def web_search(self, query: str) -> str:
    try:
        response = requests.get(
            "https://serpapi.com/search",
            params={
                "q": query,
                "api_key": self.serpapi_key,
                "engine": "google",
            },
            timeout=10,
        )
        response.raise_for_status()
        data = response.json()

        results = data.get("organic_results", [])[:5]
        if not results:
            return "No results found."

        formatted = "\n\n".join(
            f"{r.get('title')}\n{r.get('link')}\n{r.get('snippet', '')}"
            for r in results
        )
        return formatted
    except Exception as e:
        return f"Search failed: {e}"