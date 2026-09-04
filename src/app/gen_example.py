class HumanApprve:
  def __init__(self, message: str):
    self.message = message

def write_file(path: str, filename:str):
  print("Before writing to files")
  # check if this path is allowed
  allowed = False
  if not allowed:
    yield HumanApprve(f'Can I write to {path}')

  print(f'After writing to file')
  if not allowed:
      yield HumanApprve(f'Can I save to {path}')

  valu = yield

  return


def main():
  tool = write_file('cool_files', 'cool_file')

  try:
    for m in tool:
      print(m.message)
      i = input('Enter yes or no: ')
      if i == 'no':
        break
  except GeneratorExit:
    print('Finish program')

main()