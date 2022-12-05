import discord
from discord.ext import commands
import asyncio
import logging
from os import getenv
from misc import get_from_db

logging.basicConfig(level=logging.INFO)

intents = discord.Intents.all()
bot = commands.Bot(command_prefix='.', intents=intents, help_command=None)

@bot.event
async def on_ready():
  print('Graham Bot is online.')

async def main():
  async with bot:
    token = getenv('TOKEN') if getenv('TOKEN') else get_from_db('bot_token.json', 'TOKEN')
      
    await bot.load_extension("games.commands")
    await bot.load_extension('misccommands')
    await bot.start(token)
    

asyncio.run(main())
