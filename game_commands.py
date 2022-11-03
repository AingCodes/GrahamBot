from discord.ext import commands
import players
import yahtzee
from bj import parse_blackjack_command, bjgame_containing_id
from misc import get_name, create_buttons, get_from_db, already_playing, intify
import games

async def setup(bot):
  await bot.add_cog(bjCog(bot))
  await bot.add_cog(yahtzeeCog(bot))
  
class bjCog(commands.Cog):
  def __init__(self, bot):
    self.bot = bot
    
  @commands.command()
  async def blackjack(self, ctx, *args):
    members, kwargs = await parse_blackjack_command(ctx, args)
    deck_count = kwargs.get("deck_count")
    print(deck_count)
    names, ids = map(get_name, members), map(lambda x: str(x.id), members)

    naughty_player = already_playing(games.game_list, ids)

    if naughty_player:
      await ctx.send(f"<@{naughty_player}> is already playing a game. Finish the game before starting a new one.")
      return
  
    games.game_list.append(games.bjgame(names, ids, deck_count))
    game = games.game_list[-1]
    await game.run(ctx, self.bot)

  @commands.command(name='wager', aliases=['w'])
  async def wager(self, ctx, wager):

    id = str(ctx.author.id)
    ping = f"<@{id}>"
    game = bjgame_containing_id(id, games.game_list)

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
    for game in games.game_list:
      if (isinstance(game, games.bjgame) and
          str(ctx.author.id) in game.players and
          not len(game.players) == len(game.wagers)
         ):
        games.game_list.remove(game)
        await ctx.send(f"The blackjack game involving {get_name(ctx.author)} was aborted.")

class yahtzeeCog(commands.Cog):
  def __init__(self, bot):
    self.bot = bot

  @commands.command()
  async def yahtzee(self, ctx):
    # Adds a yahtzee game to the games list and grabs it as the variable game
    games.game_list.append(games.yahtzeegame())
    game = games.game_list[-1]

    # Adds the author of the command to the players
    game.players.append(players.yahtzeeplayer(str(ctx.author.id), get_name(ctx.author)))
    
    # Creates a message you can interact with to join, start or cancel the game
    labels = ('Join/Unjoin', 'Start Game', 'Cancel Game')
    ids = ('join', 'start', 'cancel')
    view = create_buttons(labels=labels, ids=ids)
    initial_message = await ctx.send(f"Yahtzee game started. Current players: {', '.join([player.name for player in game.players])}", view=view)

    # Waits until the cancel button is hit or 
    while game.players:
      interaction = await self.bot.wait_for('interaction')
    
      user = str(interaction.user.id)
      nick = interaction.user.nick
      name = interaction.user.name
      interactor = None

      for player in game.players:
        if user == player.id:
          interactor = player
  
      if interaction.data['custom_id'] == 'join':
        # Adds the user to players if they press the join button, or removes them if they were already playing
        if interactor in game.players:
          game.players.remove(interactor)
          await initial_message.edit(content=f"Yahtzee game started. Current players: {yahtzee.initial_game_message(game)}")
          await interaction.response.defer()
        else:
          game.players.append(players.yahtzeeplayer(user, nick if nick else name))
          await initial_message.edit(content=f"Yahtzee game started. Current players: {yahtzee.initial_game_message(game)}")
          await interaction.response.defer()
          
      elif interaction.data['custom_id'] == 'start':
        # Runs the game if the start button is hit
        await initial_message.delete()
        await interaction.response.defer()
        await yahtzee.run_game(game, ctx, self.bot)
        return
        
      elif interaction.data['custom_id'] == 'cancel':
        # Cancels the game if the cancel button is hit
        await interaction.response.defer()
        await initial_message.delete()
        break

    await ctx.send('Game cancelled.')
    await initial_message.delete()
    games.game_list.remove(game)