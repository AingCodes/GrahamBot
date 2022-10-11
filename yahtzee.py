import random
import discord
from misc import create_buttons, create_dropdown
import asyncio

dice_emojis = {

  '1': ("<:1_:1025021708895277156>"),
  '2': ("<:2_:1025021711218921482>"),
  '3': ("<:3_:1025021712842096660>"),
  '4': ("<:4_:1025021715123798086>"),
  '5': ("<:5_:1025021717128675368>"),
  '6': ("<:6_:1025021719204860014>"),
  '1h': ("<:1h:1025033781465317426>"),
  '2h': ("<:2h:1025033782987849849>"),
  '3h': ("<:3h:1025033784548143124>"),
  '4h': ("<:4h:1025033786628509866>"),
  '5h': ("<:5h:1025033788931194991>"),
  '6h': ("<:6h:1025033790906704002>"),
}

def initial_game_message(game):
  players = [player.name for player in game.players]
  return ', '.join(players)

def roll_dice(player):
  for die_number, die in enumerate(player.dice):
    if player.kept[die_number]:
      player.dice[die_number] = random.randint(1,6)

def display_dice(player):
  global dice_emojis
  view = discord.ui.View()

  emojis = [dice_emojis[f"{die}h"] if player.held[die_number] else dice_emojis[f"{die}"] for die_number, die in enumerate(player.dice)]
  ids = ['1', '2', '3', '4', '5']
  view = create_buttons(emojis=emojis, ids=ids)
  view.add_item(discord.ui.Button(label='Roll', custom_id='roll'))
  
  return f"{player.name}'s dice:", view

def display_scoresheet(player):
  options = []
  for key, value in player.scoresheet.items():
    if not value and key not in ("Total Top Score", "Bonus", "Total Score"):
      options.append(key)
    
  view = create_dropdown(options=options, placeholder="Submit a score", custom_id="scoresheet")
  
  scoresheet = [f"{key}: {value}" for key, value in player.scoresheet.items()]
  scoresheet = '\n'.join(scoresheet)
  return f"{player.name}'s scoresheet:\n{scoresheet}", view

def game_is_active(game):
  for player in game.players:
    for value in player.scoresheet.values():
      if not value:
        return True
  return False

async def refresh_scoresheet(sheet_message, player):
  content, view = display_scoresheet(player)
  await sheet_message.edit(content=content, view=view)

async def refresh_dice(dice_message, player):
  content, view = display_dice(player)
  await dice_message.edit(content=content, view=view)

async def run_game(game, ctx, bot):
  content, view = display_scoresheet(game.players[0])
  game.sheet_message = await ctx.send(content, view=view)
  content, view = display_dice(game.players[0])
  game.dice_message = await ctx.send(content, view=view)

  while game_is_active(game):
    interaction = await bot.wait_for('interaction')
    type = interaction.data['component_type']
    id = interaction.data['values'][0] if type == 3 else interaction.data['custom_id']

    for _player in game.players:
      if str(interaction.user.id) == _player.id:
        player = _player
    await interaction.response.defer()

    if not player == game.players[game.turn]:
      continue

    asyncio.create_task(game.resolve_interaction(id, player, type))




      