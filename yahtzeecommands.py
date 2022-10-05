import discord
from discord.ext import commands
import games
import yahtzee
import players
from misc import get_name, create_buttons

async def setup(bot):
  await bot.add_cog(yahtzeeCog(bot))

class yahtzeeCog(commands.Cog):
  def __init__(self, bot):
    self.bot = bot

  @commands.command()
  async def yahtzee(self, ctx):
    # Adds a yahtzee game to the games list and grabs it as the variable game
    games.game_list.append(games.yahtzeegame())
    game = games.game_list[-1]

    # Adds the author of the command to the players
    game.players[str(ctx.author.id)] = players.yahtzeeplayer(str(ctx.author.id), get_name(ctx.author))
    
    # Creates a message you can interact with to join, start or cancel the game
    labels = ('Join/Unjoin', 'Start Game', 'Cancel Game')
    ids = ('join', 'start', 'cancel')
    view = create_buttons(labels=labels, ids=ids)
    initial_message = await ctx.send(f"Yahtzee game started. Current players: {yahtzee.initial_game_message(game)}", view=view)

    # Waits until the cancel button is hit or 
    while game.players:
      interaction = await self.bot.wait_for('interaction')
    
      user = str(interaction.user.id)
      nick = interaction.user.nick
      name = interaction.user.name
  
      if interaction.data['custom_id'] == 'join':
        # Adds the user to players if they press the join button, or removes them if they were already playing
        if user in game.players:
          del game.players[user]
          await initial_message.edit(content=f"Yahtzee game started. Current players: {yahtzee.initial_game_message(game)}")
          await interaction.response.defer()
        else:
          game.players[user] = players.yahtzeeplayer(user, nick if nick else name)
          await initial_message.edit(content=f"Yahtzee game started. Current players: {yahtzee.initial_game_message(game)}")
          await interaction.response.defer()
          
      elif interaction.data['custom_id'] == 'start':
        # Runs the game if the start button is hit
        await yahtzee.run_game(game, ctx, self.bot)
        await initial_message.delete()
        await interaction.response.defer()
        
      elif interaction.data['custom_id'] == 'cancel':
        # Cancels the game if the cancel button is hit
        await interaction.response.defer()
        await initial_message.delete()
        break

    await ctx.send('Game cancelled.')
    games.game_list.remove(game)
