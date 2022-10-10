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
  
  return view

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
  view = display_dice(player)
  await dice_message.edit(view=view)
  

async def run_game(game, ctx, bot):
  sheet_message = display_scoresheet(game.players[0])
  sheet_message = await ctx.send(sheet_message[0], view=sheet_message[1])
  dice_message = await ctx.send(f"{game.players[0].name}'s dice: ", view=display_dice(game.players[0]))

  while game_is_active(game):
    interaction = await bot.wait_for('interaction')
    id = interaction.data['values'][0] if interaction.data['component_type'] == 3 else interaction.data['custom_id']
    for _player in game.players:
      if str(interaction.user.id) == _player.id:
        player = _player
    await interaction.response.defer()

    if not player == game.players[game.turn]:
      continue

    if id == 'Aces':
      for a in player.dice:
        if a == 1:
          player.scoresheet['Aces'] += 1          
      game.increment()
      if not player.scoresheet['Aces']:
        player.scoresheet['Aces'] = '0'
      

    elif id == 'Twos':
      for a in player.dice:
        if a == 2:
          player.scoresheet['Twos'] += 2
      game.increment()
      if not player.scoresheet['Twos']:
        player.scoresheet['Twos'] = '0'


    elif id == 'Threes':
      for a in player.dice:
        if a == 3:
          player.scoresheet['Threes'] += 3
      game.increment()
      if not player.scoresheet['Threes']:
        player.scoresheet['Threes'] = '0'

    elif id == 'Fours':
      for a in player.dice:
        if a == 4:
          player.scoresheet['Fours'] += 4
      game.increment()
      if not player.scoresheet['Fours']:
        player.scoresheet['Fours'] = '0'

    elif id == 'Fives':
      for a in player.dice:
        if a == 5:
          player.scoresheet['Fives'] += 5
      game.increment()
      if not player.scoresheet['Fives']:
        player.scoresheet['Fives'] = '0'

    elif id == 'Sixes':
      for a in player.dice:
        if a == 6:
          player.scoresheet['Sixes'] += 6
      game.increment()
      if not player.scoresheet['Sixes']:
        player.scoresheet['Sixes'] = '0'

    elif id == 'Chance':
      for a in player.dice:
          player.scoresheet['Chance'] += a
      game.increment()

    elif id == 'Three of a Kind':
      for a in player.dice:
        if player.dice.count(a) >= 3:
          for b in player.dice:
            player.scoresheet['Three of a Kind'] += b
      game.increment()
      if not player.scoresheet['Three of a Kind']:
        player.scoresheet['Three of a Kind'] = '0'

    elif id == 'Four of a Kind':
      for a in player.dice:
        if player.dice.count(a) >= 4:
          for b in player.dice:
            player.scoresheet['Four of a Kind'] += b
      game.increment()
      if not player.scoresheet['Four of a Kind']:
        player.scoresheet['Four of a Kind'] = '0'

    elif id == 'Full House':
      for a in player.dice:
        if player.dice.count(a) == 3:
          for b in player.dice:
            if player.dice.count(b) == 2:
              player.scoresheet['Full House'] = 25
      game.increment()
      if not player.scoresheet['Full House']:
        player.scoresheet['Full House'] = '0'

    elif id == 'Small Straggot':
      dice_as_set = set(player.dice)
      if (
        dice_as_set == {1,2,3,4} or 
        dice_as_set == {2,3,4,5} or 
        dice_as_set == {3,4,5,6}
      ):
        player.scoresheet['Small Straggot'] = 30
      game.increment()
      if not player.scoresheet['Small Straggot']:
        player.scoresheet['Small Straggot'] = '0'

    elif id == 'Large Straggot':
      if sorted(player.dice) == range(min(player.dice), max(player.dice)+1):
        player.scoresheet['Large Straggot'] = 40
      game.increment()
      if not player.scoresheet['Large Straggot']:
        player.scoresheet['Large Straggot'] = '0'

    elif id == 'Grahamzee':
      if player.dice.count(player.dice[0]) == 5:
        player.scoresheet['Grahamzee'] = 50
      game.increment()
      if not player.scoresheet['Grahamzee']:
        player.scoresheet['Grahamzee'] = '0'

    elif id in ('1', '2', '3', '4', '5'):
      player.held[int(id)-1] = True if not player.held[int(id)-1] else False
      await refresh_dice(dice_message, player)

    elif id == 'roll':
      await player.roll_dice(dice_message)


    player.check_scores()
    await refresh_scoresheet(sheet_message, player)

    if interaction.data['component_type'] == 3:
      player.reset_dice()
      await refresh_dice(dice_message, game.players[game.turn])

      if len(game.players) > 1:
        await asyncio.sleep(3)
      
      await refresh_scoresheet(sheet_message, game.players[game.turn])





      