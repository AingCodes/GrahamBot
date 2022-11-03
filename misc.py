import discord
from discord.ext import commands
import json

def get_name(user):
  name = user.nick if user.nick else user.name
  return name

async def cvt_member(ctx, tag):
  converter = commands.MemberConverter()
  member = await converter.convert(ctx, tag)
  return member

def create_buttons(**kwargs):
  view = discord.ui.View()
  for type in ("labels", "emojis"):
    if not kwargs.get(type):
      kwargs[type] = (None for _ in kwargs["ids"])
  items = [
    discord.ui.Button(
      custom_id=custom_id,
      label=label,
      emoji=emoji,
    ) for custom_id, label, emoji in zip(kwargs["ids"], kwargs["labels"], kwargs["emojis"])
  ]
  for item in items:
    view.add_item(item)
  return view

def create_dropdown(**kwargs):
  view = discord.ui.View()
  custom_id = kwargs.get("custom_id")
  placeholder = kwargs.get("placeholder")
  options = [option for option in kwargs.get("options")]
  
  dropdown = discord.ui.Select(custom_id=custom_id, placeholder=placeholder)
  
  for option in options:
    dropdown.add_option(label=option)
    
  view.add_item(dropdown)
  return view

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

def new_bank(user):
  with open("bank_of_graham.json", "r") as f:
    data = json.load(f)
    if user not in data:
      update_db("bank_of_graham.json", user, 1000)

def already_playing(game_list, ids):
  for game in game_list:
    for id in ids:
      if id in game.players:
        return id
  return None

def intify(arg):
  try: 
    return int(arg)
  except ValueError:
    return None