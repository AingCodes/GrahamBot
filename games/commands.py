from typing import List, Tuple, Union
from discord.ext import commands
import discord
from misc import get_name, create_buttons, get_from_db, already_playing, intify, new_bank, cvt_member
from games.blackjack import BJGame
from games.yahtzee import YahtzeeGame
import asyncio
GLOBAL_GAME_LIST: List[Union[BJGame, YahtzeeGame]] = []

async def setup(bot):
  await bot.add_cog(bjCog(bot))
  await bot.add_cog(yahtzeeCog(bot))
  """await bot.add_cog(wordleCog(bot))"""
  
class bjCog(commands.Cog):
  def __init__(self, bot):
    self.bot = bot
    
  @commands.command()
  async def blackjack(self, ctx, *args: str):
    global GLOBAL_GAME_LIST
    members: List[discord.Member] = [await cvt_member(ctx, str(ctx.author.id))]
    deck_count: int = 4
    for arg in args:
      if arg.startswith("<@"):
        try:
          members.append(await cvt_member(ctx, arg))
        except Exception:
          pass
      elif arg.startswith("decks="):
        try:
          deck_count = int(arg[6:])
        except Exception:
          pass


    names: Tuple[str, ...] = tuple(get_name(member) for member in members)
    ids: Tuple[str, ...] = tuple(str(member.id) for member in members)

    naughty_player: str | None = already_playing(GLOBAL_GAME_LIST, ids)

    if naughty_player:
      await ctx.send(f"<@{naughty_player}> is already playing a game. Finish the game before starting a new one.")
      return
  
    game = BJGame(names, ids, deck_count)
    GLOBAL_GAME_LIST.append(game)
    asyncio.create_task(game.run(ctx, self.bot))

  @commands.command(name='wager', aliases=['w'])
  async def wager(self, ctx, wager):

    id = str(ctx.author.id)
    ping = f"<@{id}>"
    game = None

    for g in GLOBAL_GAME_LIST:
      if isinstance(g, BJGame) and id in g.players:
        game: BJGame = g

    if not game:
      return

    bankroll = get_from_db('bank_of_graham.json', id)
    
    if id in game.wagers:
      await ctx.send(f"{ping} you already have a wager set.")
      return
  
    wager = intify(wager)

    if not wager or wager < 1:
      await ctx.send(f"{ping} your wager must be a positive integer.")
      return
    elif wager > bankroll:
      await ctx.send(f"{ping} you do not have enough Grahams to make that wager. You currently have {bankroll} Grahams.")
      return
    else:
      await ctx.send(f"{ping} bet {wager} Grahams on their next hand.")
      game.wagers[id] = wager

  @commands.command()
  async def abort(self, ctx):
    for game in GLOBAL_GAME_LIST:
      if (isinstance(game, BJGame) and
          str(ctx.author.id) in game.players and
          not len(game.players) == len(game.wagers)
         ):
        GLOBAL_GAME_LIST.remove(game)
        await ctx.send(f"The blackjack game involving {get_name(ctx.author)} was aborted.")

class yahtzeeCog(commands.Cog):
  def __init__(self, bot):
    self.bot = bot

  @commands.command()
  async def yahtzee(self, ctx, *args: str):
    global GLOBAL_GAME_LIST
    id = str(ctx.author.id)
    wager = None
    for arg in args:
      if arg.startswith("wager="):
        wager = intify(arg[6:])
    new_bank(id)
    balance = get_from_db('bank_of_graham.json', id)
    if wager and wager > balance:
      ctx.send("You do not have enough Grahams to start a game with this wager.")
      return
    else:
      game = YahtzeeGame(get_name(ctx.author), id, wager)
      GLOBAL_GAME_LIST.append(game)
      asyncio.create_task(game.run(ctx, self.bot))

"""class wordleCog(commands.Cog):
  def __init__(self, bot):
    self.bot = bot
    self.wordlemessage = ""
    self.guessamount = 0
    self.words = set(line.strip() for line in open('words.txt'))
    self.word = random.sample(tuple(self.words), 1)

  @commands.command()
  async def wordle(self, ctx):
    print(self.word)
    self.wordlemessage = await ctx.send("Wordle started. Please guess using '.guess <word>'")

  @commands.command()
  async def guess(self, ctx, guess):
    self.guessamount += 1
    if self.guessamount > 0:
      await self.wordlemessage.edit(content = f"You guessed the word {guess}.")
    elif self.guessamount == 6:
      self.wordlemessage = (f"You didn't guess the word. The word was {word}")
    else:
      self.wordlemessage = (f"You guessed the word {guess}.")"""