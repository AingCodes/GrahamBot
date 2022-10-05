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
      custom_id=inputs['ids'],
      label=inputs['labels'],
      emoji=inputs['emojis'],
    ) for i in inputs
  ]
  for item in items:
    view.add_item(item)
  return view