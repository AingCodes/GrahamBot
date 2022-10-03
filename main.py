import discord
from discord.ext import commands
import asyncio
import logging
import jsonfuncs

logging.basicConfig(level=logging.INFO)

intents = discord.Intents.all()
bot = commands.Bot(command_prefix='.', intents=intents, help_command=None)

@bot.event
async def on_ready():
  print('Graham Bot is online.')

async def main():
  async with bot:
    await bot.load_extension('yahtzeecommands')
    await bot.load_extension('misccommands')
    await bot.load_extension('bjcommands')
    await bot.start(jsonfuncs.get_from_db('bot_token.json', 'TOKEN'))
    

asyncio.run(main())
