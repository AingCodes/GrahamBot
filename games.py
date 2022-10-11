import players
import bj
import hand
from yahtzee import refresh_dice, refresh_scoresheet
import asyncio

game_list = []
all_players = []

class yahtzeegame:
  def __init__(self):
    self.players = []
    self.turn = 0

  def increment(self):
    self.turn += 1
    self.turn = self.turn % len(self.players)

  async def resolve_interaction(self, id, player, type):
    if id == 'Aces':
      for a in player.dice:
        if a == 1:
          player.scoresheet['Aces'] += 1          
      if not player.scoresheet['Aces']:
        player.scoresheet['Aces'] = '0'

    elif id == 'Twos':
      for a in player.dice:
        if a == 2:
          player.scoresheet['Twos'] += 2
      if not player.scoresheet['Twos']:
        player.scoresheet['Twos'] = '0'

    elif id == 'Threes':
      for a in player.dice:
        if a == 3:
          player.scoresheet['Threes'] += 3
      if not player.scoresheet['Threes']:
        player.scoresheet['Threes'] = '0'

    elif id == 'Fours':
      for a in player.dice:
        if a == 4:
          player.scoresheet['Fours'] += 4
      if not player.scoresheet['Fours']:
        player.scoresheet['Fours'] = '0'

    elif id == 'Fives':
      for a in player.dice:
        if a == 5:
          player.scoresheet['Fives'] += 5
      if not player.scoresheet['Fives']:
        player.scoresheet['Fives'] = '0'

    elif id == 'Sixes':
      for a in player.dice:
        if a == 6:
          player.scoresheet['Sixes'] += 6
      if not player.scoresheet['Sixes']:
        player.scoresheet['Sixes'] = '0'

    elif id == 'Chance':
      for a in player.dice:
          player.scoresheet['Chance'] += a

    elif id == 'Three of a Kind':
      for a in player.dice:
        if player.dice.count(a) >= 3:
          for b in player.dice:
            player.scoresheet['Three of a Kind'] += b
      if not player.scoresheet['Three of a Kind']:
        player.scoresheet['Three of a Kind'] = '0'

    elif id == 'Four of a Kind':
      for a in player.dice:
        if player.dice.count(a) >= 4:
          for b in player.dice:
            player.scoresheet['Four of a Kind'] += b
      if not player.scoresheet['Four of a Kind']:
        player.scoresheet['Four of a Kind'] = '0'

    elif id == 'Full House':
      for a in player.dice:
        if player.dice.count(a) == 3:
          for b in player.dice:
            if player.dice.count(b) == 2:
              player.scoresheet['Full House'] = 25
      if not player.scoresheet['Full House']:
        player.scoresheet['Full House'] = '0'

    elif id == 'Small Straggot':
      dice_as_set = set(player.dice)
      if (
        {1,2,3,4}.issubset(dice_as_set) or 
        {2,3,4,5}.issubset(dice_as_set) or 
        {3,4,5,6}.issubset(dice_as_set)
      ):
        player.scoresheet['Small Straggot'] = 30
      if not player.scoresheet['Small Straggot']:
        player.scoresheet['Small Straggot'] = '0'

    elif id == 'Large Straggot':
      if sorted(player.dice) == list(range(min(player.dice), max(player.dice)+1)):
        player.scoresheet['Large Straggot'] = 40
      if not player.scoresheet['Large Straggot']:
        player.scoresheet['Large Straggot'] = '0'

    elif id == 'Grahamzee':
      if player.dice.count(player.dice[0]) == 5:
        player.scoresheet['Grahamzee'] = 50
      if not player.scoresheet['Grahamzee']:
        player.scoresheet['Grahamzee'] = '0'

    elif id in ('1', '2', '3', '4', '5'):
      player.held[int(id)-1] = True if not player.held[int(id)-1] else False
      await refresh_dice(self.dice_message, player)

    elif id == 'roll':
      await player.roll_dice(self.dice_message)

    player.check_scores()
    await refresh_scoresheet(self.sheet_message, player)

    if type == 3:
      self.increment()
      player.reset_dice()
      await refresh_dice(self.dice_message, self.players[self.turn])

      if len(self.players) > 1:
        await asyncio.sleep(3)
      
      await refresh_scoresheet(self.sheet_message, self.players[self.turn])


class bjgame:
  __slots__ = ('id_list', 'deck_count', 'name_list', 'players', 'deck', 'dealer_hand', 'wagers', 'display_message')
  
  def __init__(self, name_list, id_list, deck_count):
    self.id_list = id_list
    self.deck_count = deck_count
    self.name_list = name_list
    self.players = {id_list[i]: players.bjplayer(name_list[i], id_list[i]) for i, x in enumerate(name_list)}
    self.deck = bj.create_deck(deck_count)
    self.dealer_hand = hand.hand()
    self.wagers = {}

  def reshuffle_deck(self):
    self.deck = bj.create_deck(self.deck_count)
