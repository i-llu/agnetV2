from pathlib import Path
import shutil
import os
from playsound3 import playsound
from difflib import get_close_matches
import subprocess

PARENT_DIR = Path.cwd()

class FilesService:
  def __init__(self):
     self.files = []

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



  def write_file(self, path: str, content: str) -> str:
      file_path = PARENT_DIR / path
      try:
        file_path.parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        return f"Successfully wrote to {path}"
      except OSError as e:
          return f"Failed to write {path}: {e}"

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

  def rename_file(self, path: str, name: str) -> str:
    old_path = PARENT_DIR / path
    new_path = old_path.parent / name
    try:
      if not old_path.exists():
          return f"File not found: {path}"
      if new_path.exists():
          return f"A file already exists at {name}"
      old_path.rename(new_path)
      return f"Successfully renamed {path} to {name}"
    except OSError as e:
        return f"Failed to rename {path}: {e}"

  def copy_file(self,path:str,dest:str):
    old_path = PARENT_DIR / path
    new_path = PARENT_DIR / dest

    if not old_path.exists():
        return f'File {path} does not exists'

    if new_path.exists():
        return f"file with that the name {dest} already exists"

    shutil.copyfile(old_path,new_path)
    return f"Successfully copied {path} to {dest}"

  def move_file(self,path:str,dest:str):
    old_path = PARENT_DIR / path
    new_path = PARENT_DIR / dest

    try:
        if os.path.exists(new_path):
            return f'file {dest} already exists'
        else:
            os.replace(old_path,new_path)
            return f"successfully moved file {old_path} to the {new_path}"
    except FileNotFoundError:
        return f'{path} was not found'

  def delete_file(self, path: str):
    file_path = PARENT_DIR / path

    if not file_path.exists():
        yield f"File not found: {path}"
        return

    if not file_path.is_file():
        yield f"{path} is not a file"
        return
    playsound("sounds/ter_sound.mp3")
    answer = yield f"Are you sure you want to delete {path}? (y/n)"


    if answer is None or answer.strip().lower() != "y":
        yield f"Deletion cancelled: {path}"
        return

    try:
        os.remove(file_path)
        yield f"Successfully deleted: {path}"
    except OSError as e:
        yield f"Failed to delete {path}: {e}"

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