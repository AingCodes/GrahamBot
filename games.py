import players
from bj import create_deck, Hand
from yahtzee import refresh_dice, refresh_scoresheet
import asyncio
import inflect

game_list = []
all_players = []

class yahtzeegame:
  def __init__(self):
    self.players = []
    self.turn = 0
    self.basic = (None, 'Aces', 'Twos', 'Threes', 'Fours', 'Fives', 'Sixes')

  def increment(self):
    self.turn += 1
    self.turn = self.turn % len(self.players)

  def get_results(self):
    scores = [self.players[0]]
    for player in self.players[1:]:
      for index, p in enumerate(scores):
        if player.scoresheet['Total Score'] > p.scoresheet['Total Score']:
          scores.insert(index, player)
      if player not in scores:
        scores.append(player)

    p = inflect.engine()
    message = [f"In {p.ordinal(i+1)} place: {player.name} with a score of {player.scoresheet['Total Score']} points" for i, player in enumerate(scores)]

    return "\n".join(message)

    
      
      
      

  async def resolve_interaction(self, id, player, type):
    if id in self.basic:
      value = self.basic.index(id) # the points awarded is equal to the index in the tuple
      for die in player.dice:
        if die == value:
          player.scoresheet[id] += value        

    elif id == 'Chance':
      for a in player.dice:
          player.scoresheet['Chance'] += a

    elif id == 'Three of a Kind':
      for a in player.dice:
        if player.dice.count(a) >= 3:
          player.scoresheet['Three of a Kind'] += sum(player.dice)
          break
            
    elif id == 'Four of a Kind':
      for a in player.dice:
        if player.dice.count(a) >= 4:
          player.scoresheet['Four of a Kind'] += sum(player.dice)
          break

    elif id == 'Full House':
      for a in player.dice:
        if player.dice.count(a) == 3:
          for b in player.dice:
            if player.dice.count(b) == 2:
              player.scoresheet['Full House'] = 25

    elif id == 'Small Straggot':
      dice_as_set = set(player.dice)
      if (
        {1,2,3,4}.issubset(dice_as_set) or 
        {2,3,4,5}.issubset(dice_as_set) or 
        {3,4,5,6}.issubset(dice_as_set)
      ):
        player.scoresheet['Small Straggot'] = 30

    elif id == 'Large Straggot':
      if sorted(player.dice) == list(range(min(player.dice), max(player.dice)+1)):
        player.scoresheet['Large Straggot'] = 40

    elif id == 'Grahamzee':
      if player.dice.count(player.dice[0]) == 5:
        player.scoresheet['Grahamzee'] = 50

    elif id in ('1', '2', '3', '4', '5'):
      player.held[int(id)-1] = True if not player.held[int(id)-1] else False
      await refresh_dice(self.dice_message, player)

    elif id == 'roll':
      await player.roll_dice(self.dice_message)

    if type == 3 and not player.scoresheet[id]:
      player.scoresheet[id] = '0'

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
    self.deck = create_deck(deck_count)
    self.dealer_hand = Hand()
    self.wagers = {}

  def reshuffle_deck(self):
    self.deck = create_deck(self.deck_count)
