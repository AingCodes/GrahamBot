import players
import bj
import hand

game_list = []
all_players = []

class yahtzeegame:
  def __init__(self):
    self.players = []
    self.turn = 0

  def increment(self):
    self.turn += 1
    self.turn = self.turn % len(self.players)


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
