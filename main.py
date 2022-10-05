import discord
from discord.ext import commands
import asyncio
import logging
import jsonfuncs
from os import getenv
import misc

logging.basicConfig(level=logging.INFO)

intents = discord.Intents.all()
bot = commands.Bot(command_prefix='.', intents=intents, help_command=None)

@bot.event
async def on_ready():
  print('Graham Bot is online.')

async def main():
  async with bot:
    token = getenv('TOKEN') if getenv('TOKEN') else jsonfuncs.get_from_db('bot_token.json', 'TOKEN')
      
    await bot.load_extension('yahtzeecommands')
    await bot.load_extension('misccommands')
    await bot.load_extension('bjcommands')
    await bot.start(token)
    

asyncio.run(main())
