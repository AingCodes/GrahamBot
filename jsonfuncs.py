import json

def get_from_db(file, key):
  with open(file, 'r') as f:
    data = json.load(f)
  return data[key]

def update_db(file, key, value):
  with open(file, 'r') as f:
    data = json.load(f)
    data[key] = value
    data = json.dumps(data)
  with open (file, 'w') as f:
    f.write(data)