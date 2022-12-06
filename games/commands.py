from typing import List, Tuple, Union
from discord.ext import commands
import discord
from misc import get_name, create_buttons, get_from_db, already_playing, intify, new_bank, cvt_member
from games.blackjack import BJGame
from games.yahtzee import YahtzeeGame
from games.wordle import wordlegame
import asyncio
GLOBAL_GAME_LIST: List[Union[BJGame, YahtzeeGame]] = []

async def setup(bot):
  await bot.add_cog(bjCog(bot))
  await bot.add_cog(yahtzeeCog(bot))
  await bot.add_cog(wordleCog(bot))

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

class wordleCog(commands.Cog):
  def __init__(self, bot):
    self.bot = bot
    self.game = wordlegame()

  @commands.command()
  async def guess(self, ctx, word_guess: str):
    print(self.game.word)
    guess = word_guess.lower()
    the_answer_letter_list = list(self.game.word)
    letter_list = list(guess)

    match_list = [does_shit(i, guess_letter, the_answer_letter_list) for i, guess_letter in enumerate(letter_list)]
    print(match_list)


def does_shit(i, guess_letter, the_answer_letter_list):
  if guess_letter in the_answer_letter_list:
    if guess_letter == the_answer_letter_list[i]:
      return "🟩" 
    else:
      return "🟧"
  else:
    return "🟥"