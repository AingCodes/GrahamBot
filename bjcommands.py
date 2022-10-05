import discord
from discord.ext import commands
import games
import bj
import jsonfuncs
from misc import get_name, cvt_member

async def setup(bot):
  await bot.add_cog(bjCog(bot))
  
class bjCog(commands.Cog):
  def __init__(self, bot):
    self.bot = bot
    
  @commands.command()
  async def blackjack(self, ctx, *args):
    name_list = [get_name(ctx.author)]
    id_list = [str(ctx.author.id)]

    deck_count = None
    
    for arg in args:
      if arg.startswith('decks='):
        try:
          deck_count = int(arg[6:]) if int(arg[6:]) else None
          break
        except:
          pass

    if not deck_count:
      deck_count = 4

    members = (cvt_member(ctx, tag) for tag in args if tag.startswith('<@'))
        
    name_list.extend([get_name(member) for member in members])
    id_list.extend([str(member.id) for member in members])
  
    all_players = [player.id for game in games.game_list if game for player in game.players.values()]

    for id in id_list:
      if id in all_players:
        await ctx.send(f"<@{id}> is already playing a game. Finish the game before starting a new one.")
        return
  
    games.game_list.append(games.bjgame(name_list, id_list, deck_count))
    game = games.game_list[-1]
    await bj.run(ctx, self.bot, game)

  @commands.command(name='wager', aliases=['w'])
  async def wager(self, ctx, wager):
    playing, game = await bj.is_playing(ctx)
    if not playing:
      return

    user = f"<@{ctx.author.id}>"
    bankroll = jsonfuncs.get_from_db('bank_of_graham.json', str(ctx.author.id))
    
    if str(ctx.author.id) in game.wagers.keys():
      await ctx.send(f"{user} you already have a wager set.")
      return
  
    try:
      wager = int(wager)
    except:
      pass
    if isinstance(wager, int):
      if wager < 1:
        await ctx.send(f"{user} your wager must be a positive integer.")
        return
      elif wager > bankroll:
        await ctx.send(f"{user} you do not have enough Grahams to make that wager. You currently have {bankroll} Grahams.")
        return
      else:
        await ctx.send(f"{user} bet {wager} Grahams on their next hand.")
        game.wagers[str(ctx.author.id)] = wager
    else:
      await ctx.send(f"{user} your wager must be a positive integer.")
      return

  @commands.command()
  async def abort(self, ctx):
    for game in games.game_list:
      if (isinstance(game, games.bjgame) and
          str(ctx.author.id) in game.players and
          not len(game.players) == len(game.wagers)
         ):
        games.game_list.remove(game)
        await ctx.send(f"The blackjack game involving {get_name(ctx.author)} was aborted.")
