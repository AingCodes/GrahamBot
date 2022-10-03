import players
import bj
import hand

game_list = []
all_players = []

class yahtzeegame:
  def __init__(self):
    self.players = {}


class bjgame:
  def __init__(self, name_list, id_list, deck_count):
    self.id_list = id_list
    self.name_list = name_list
    self.players = {id_list[i]: players.bjplayer(name_list[i], id_list[i]) for i, x in enumerate(name_list)}
    self.deck = bj.create_deck(deck_count)
    self.dealer_hand = hand.hand()
    self.wagers = {}
    self.display_message = ''

  def reshuffle_deck(self):
    self.deck = bj.create_deck()