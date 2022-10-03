from discord.ext import commands

def get_name(user):
  name = user.nick if user.nick else user.name
  return name

def cvt_member(ctx, tag):
  converter = commands.MemberConverter()
  member = converter.convert(ctx, tag)
  return member