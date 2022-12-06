from enum import Enum, auto
import discord
from misc import create_buttons, create_dropdown, get_name
import asyncio
from random import randint
from itertools import islice
from typing import List, Tuple, Dict, Union, Optional

class Decision(Enum):
  ONE = auto()
  TWO = auto()
  THREE = auto()
  FOUR = auto()
  FIVE = auto()
  SIX = auto()
  CHANCE = auto()
  TOK = auto()
  FOK = auto()
  FH = auto()
  SS = auto()
  LS = auto()
  GZ = auto()
  ROLL = auto()
  K1 = auto()
  K2 = auto()
  K3 = auto()
  K4 = auto()
  K5 = auto()

SCORESHEET_NAMES = [
  "",
  "Aces",
  "Twos",
  "Threes",
  "Fours",
  "Fives", 
  "Sixes", 
  "Chance", 
  "Three of a Kind", 
  "Four of a Kind",
  "Full House",
  "Small Straggot",
  "Large Straggot",
  "Grahamzee"
]

DICE_EMOJIS = {
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

class YahtzeePlayer:
  __slots__ = ("id", "name", "dice", "held", "rolls_spent", "scoresheet")

  def __init__(self, id: str, name: str):
    self.id = id
    self.name = name
    self.dice = [randint(1,6) for _ in range(5)]
    self.held = [False for _ in range(5)]
    self.rolls_spent = 0
    self.scoresheet: Dict[Decision, Union[str, int]] = {key: "" for key in islice(Decision, 13)}

  def __str__(self):
    scores = [f"{self.name}'s scoresheet:"]
    calc_bonus = False if "" in islice(self.scoresheet, 6) else True
    scores.extend(f"{SCORESHEET_NAMES[decision.value]}: {self.scoresheet[decision]}" for decision in islice(Decision, 6))
    total_top = sum_scores(islice(self.scoresheet.values(), 6))
    scores.append(f"**Total Top Score**: {total_top}")
    bonus = "" if not calc_bonus else 35 if total_top > 62 else 0
    scores.append(f"**Bonus**: {bonus}")
    scores.extend(f"{SCORESHEET_NAMES[decision.value]}: {self.scoresheet[decision]}" for decision in islice(Decision, 6, 13))
    scores.append(f"**Total Score**: {sum_scores(islice(self.scoresheet.values(), 13)) + bonus if calc_bonus else 0}")
    return "\n".join(scores)

  def roll(self, keeps: List[bool]):
    self.dice = [die if keep else randint(1,6) for die, keep in zip(self.dice, keeps)]
    self.rolls_spent += 1

  def hold(self, i: int):
    self.held[i] = False if self.held[i] else True

  def add_score(self, key: Decision, value: int):
    self.scoresheet[key] = value
    self.held = [False for _ in range(5)]
    self.roll(self.held)
    self.rolls_spent = 0

class YahtzeeGame:
  __slots__ = ("players", "turn", "wager", "sheet_message", "dice_message")

  def __init__(self, name: str, id: str, wager: int | None):
    self.wager = wager
    self.players = {id: YahtzeePlayer(id, name)}
    self.turn = 0

  def increment(self):
    self.turn = (self.turn + 1) % len(self.players)

  async def update_messages(self):
    content, view = await get_scoresheet(list(self.players.values())[self.turn])
    await self.sheet_message.edit(content=content, view=view)
    content, view = await get_dice(list(self.players.values())[self.turn])
    await self.dice_message.edit(content=content, view=view)

  async def run(self, ctx, bot):
    from games.commands import GLOBAL_GAME_LIST
    labels = ('Join/Unjoin', 'Start Game', 'Cancel Game')
    ids = ('join', 'start', 'cancel')
    view = create_buttons(labels=labels, ids=ids)
    setup_message = await ctx.send(f"Yahtzee game started with {f'a wager of {self.wager}' if self.wager else 'no wager'}\nCurrent players: {', '.join([player.name for player in self.players.values()])}", view=view)

    while self.players:
      interaction = await bot.wait_for("interaction")
      button = interaction.data["custom_id"]
      player = self.players.get(str(interaction.user.id))

      if player and button == "cancel":
        GLOBAL_GAME_LIST.remove(self)
        await interaction.response.defer()
        await setup_message.delete()
        return
      elif button == "join":
        name, id = get_name(interaction.user), str(interaction.user.id)
        if player:
          self.players.pop(id)
        else:
          self.players[str(id)] = YahtzeePlayer(id, name)
        await interaction.response.defer()
      elif button == "start" and player:
        await interaction.response.defer()
        await setup_message.delete()
        break

    content, view = await get_scoresheet(list(self.players.values())[self.turn])
    self.sheet_message = await ctx.send(content, view=view)
    content, view = await get_dice(list(self.players.values())[self.turn])
    self.dice_message = await ctx.send(content, view=view)
    
    while "" in list(self.players.values())[-1].scoresheet.values():
      interaction = await bot.wait_for("interaction")
      id = str(interaction.user.id)
      player = self.players.get(id)
      if list(self.players.values())[self.turn] is not player:
        await interaction.response.defer()
        continue

      await self.sheet_message.edit(view=None)
      await self.dice_message.edit(view=None)

      score = 0
      type = interaction.data['component_type']
      id = int(SCORESHEET_NAMES.index(interaction.data['values'][0])) if type == 3 else int(interaction.data['custom_id'])
      id = Decision(id)

      if id in islice(Decision, 6):
        score = sum(id.value if die == id.value else 0 for die in player.dice)
      elif id is Decision.CHANCE:
        score = sum(player.dice)
      elif id in islice(Decision, 7, 9):
        for die in player.dice:
          if player.dice.count(die) >= id.value - 5:
            score = sum(self.dice)
            break
      elif id is Decision.FH:
        if player.dice.count(player.dice[0]) in (2, 3) and len(set(player.dice)) == 2:
          score = 25
      elif id is Decision.SS:
        dice = set(player.dice)
        if (
          {1,2,3,4}.issubset(dice) or
          {2,3,4,5}.issubset(dice) or
          {3,4,5,6}.issubset(dice)
        ):
          score = 30
      elif id is Decision.LS:
        if sorted(player.dice) == list(range(min(player.dice), max(player.dice)+1)):
          score = 40
      elif id is Decision.GZ:
        if player.dice.count(player.dice[0]) == 5:
          score = 50
      elif id is Decision.ROLL:
        player.roll(player.held)
      elif id in islice(Decision, 15, 19):
        player.hold(id.value - 15)
      
      await interaction.response.defer()
      if id in islice(Decision, 13):
        player.add_score(id, score)
        self.increment()
      await self.update_messages()
      
    await self.sheet_message.delete()
    await self.dice_message.delete()
    scores = [calculate_score(player.scoresheet) for player in self.players.values()]
    for i, player in enumerate(self.players.values()):
      await ctx.send(f"{player.name} finished with a score of {scores[i]}")
    await ctx.send(f"{list(self.players.values())[scores.index(sorted(scores)[-1])]} won!")

    
  
def sum_scores(values):
  print([0 if value == "" else value for value in values])
  return sum(0 if value == "" else value for value in values)

async def get_scoresheet(player: YahtzeePlayer) -> Tuple[str, Optional[discord.ui.View]]:
  options = [SCORESHEET_NAMES[decision.value] for decision, value in player.scoresheet.items() if not value]
  view = create_dropdown(options=options, placeholder="Submit a score", custom_id="a") if options else None
  return str(player), view

async def get_dice(player: YahtzeePlayer) -> Tuple[str, discord.ui.View]:
  emojis = [DICE_EMOJIS[f"{die}h"] if player.held[die_number] else DICE_EMOJIS[f"{die}"] for die_number, die in enumerate(player.dice)]
  ids = [str(decision.value) for decision in islice(Decision, 14, 19)]
  view = create_buttons(emojis=emojis, ids=ids)
  if player.rolls_spent < 2:
    view.add_item(discord.ui.Button(label="Roll", custom_id=str(Decision.ROLL.value)))
  return f"**{player.name}'s dice:**", view

def calculate_score(scores: Dict[str, int]) -> int:
  tts = sum(score for score in islice(scores.values(), 6))
  bonus = 35 if tts > 62 else 0
  return sum(scores.values()) + bonus