import random
import discord
from misc import create_buttons

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
  print(game.players)
  players = [player.name for player in game.players.values()]
  print(players)
  return ', '.join(players)

def roll_dice(player):
  for die_number, die in enumerate(player.dice):
    if player.kept[die_number]:
      player.dice[die_number] = random.randint(1,6)

async def display_dice(player, ctx):
  global dice_emojis
  view = discord.ui.View()

  emojis = [dice_emojis[f"{die}h"] if player.held[die_number] else dice_emojis[f"{die}"] for die_number, die in enumerate(player.dice)]
  ids = ['1', '2', '3', '4', '5']
  view = create_buttons(emojis=emojis, ids=ids)
  view.add_item(discord.ui.Button(label='Roll', custom_id='roll'))
  
  return view

async def display_scoresheet(player, ctx):
  view = discord.ui.View()
  labels = []
  #for key, value in player.scoresheet.items():
    #if not value and key not in ['Top total score', ]
  items = [discord.ui.Button(label=labels[i], custom_id=labels[i]) for i in range(len(labels))]
  for item in items:
    view.add_item(item)
  scoresheet = [f"{key}: {value}" for key, value in player.scoresheet.items()]
  scoresheet = '\n'.join(scoresheet)
  return f"{player.name}'s scoresheet:'\n'{scoresheet}", view

def player_turn(player):
  while player.active:
    print("lol")


async def run_game(game, ctx, bot):
  sheet_message = await display_scoresheet(game.players['170393330306383874'], ctx)
  await ctx.send(sheet_message[0], view=sheet_message[1])
  await ctx.send("Moron McGee's dice: ", view=await display_dice(game.players['170393330306383874'], ctx))