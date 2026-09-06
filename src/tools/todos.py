

class TodoService:

  def __init__(self):
    self.todos = []
    self.next_id = 1

  def delete_todo_by_id(self,id:int):
    self.todos = [todo for todo in self.todos if todo["id"] != id]

  def add_todos(self,todos:list[str]):
    for todo in todos:
      self.todos.append(
          {
              "id":self.next_todo_id,
              "content":todo,
          }
      )
      self.next_todo_id += 1

  def clear_todos(self):
      return self.todos.clear()

  def show_todos(self):
      return self.todos