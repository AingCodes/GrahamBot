import discord
from discord.ext import commands
from collections import defaultdict

def get_name(user):
  name = user.nick if user.nick else user.name
  return name

def cvt_member(ctx, tag):
  converter = commands.MemberConverter()
  member = converter.convert(ctx, tag)
  return member

def create_buttons(**kwargs):
  view = discord.ui.View()
  inputs = defaultdict(lambda: None, kwargs)
  items = [
    discord.ui.Button(
      custom_id=inputs['ids'][i],
      label=inputs['labels'][i] if inputs['labels'] else None,
      emoji=inputs['emojis'][i] if inputs['emojis'] else None,
    ) for i, x in enumerate(inputs['ids'])
  ]
  for item in items:
    view.add_item(item)
  return view

def create_dropdown(**kwargs):
  view = discord.ui.View()
  inputs = defaultdict(lambda: None, kwargs)
  custom_id=inputs['custom_id']
  placeholder = inputs['placeholder']
  options=[inputs['options'][i] if inputs['options'] else None for i, x in enumerate(inputs['options'])]
  
  dropdown = discord.ui.Select(custom_id=custom_id, placeholder=placeholder)
  
  for option in options:
    dropdown.add_option(label=option)
    
  view.add_item(dropdown)
  return view

