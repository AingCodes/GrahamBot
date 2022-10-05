import discord
from discord.ext import commands

def get_name(user):
  name = user.nick if user.nick else user.name
  return name

def cvt_member(ctx, tag):
  converter = commands.MemberConverter()
  member = converter.convert(ctx, tag)
  return member

def create_buttons(**kwargs):
  view = discord.ui.View()
  items = [
    discord.ui.Button(
    custom_id=kwargs['ids'][i],
    label=kwargs['labels'][i] if kwargs['labels'] else None,
    emoji=kwargs['emojis'][i] if kwargs['emojis'] else None,
  ) for i, x in enumerate(kwargs['ids'])
  ]
  for item in items:
    view.add_item(item)
  return view