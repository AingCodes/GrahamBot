from random import shuffle
from custom_types import Hand, BJStatus, BJResult
from games import bjgame
import players
from misc import cvt_member


async def parse_blackjack_command(ctx, args):
  players = [await cvt_member(ctx, str(ctx.author.id))]
  kwargs = {"deck_count": 4}
  for arg in args:
    if arg.startswith("<@"):
      try:
        players.append(cvt_member(ctx, arg))
      except Exception:
        pass
    elif arg.startswith("decks="):
      try:
        deck_count = int(arg[6:])
        kwargs["deck_count"] = deck_count
      except Exception:
        pass
  return players, kwargs

def create_deck(deck_count):
  ranks = ("A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K")
  suits = ("♠️", "♥️", "♣️", "♦️")
  deck = [rank + suit for rank in ranks for suit in suits for _ in range(deck_count)]
  shuffle(deck)
  return deck

def hit(hand, amount, deck):
  hand.cards.extend([deck.pop(0) for _ in range(amount)])
  hand.hand_value()

def split(hand_to_split, player, game):
  # Creates a new hand
  player.hands.append(Hand())
  # The new hand contains the 2nd card of the original hand
  player.hands[-1].cards = [hand_to_split.cards[1]]
  # The 2nd card is removed from the original hand
  hand_to_split.cards = [hand_to_split.cards[0]]
  # Hand values are recalculated
  hand_to_split.hand_value()
  player.hands[-1].hand_value()

def check_win(phand, dhand):
  result = BJResult.LOST
  if phand.value < 22:
    if dhand.value < phand.value or dhand.value > 21:
      result = BJResult.WON
    elif phand.value == dhand.value:
      result = BJResult.PUSHED
  return result

def resolve_hand(hand, player, game):
  wager = player.wager
  if hand.status is BJStatus.BLACKJACK:
    reward = wager * 3/2
    result = BJResult.BLACKJACK
  elif hand.status is BJStatus.BUST:
    reward = -wager
    result = BJResult.BUST
  elif hand.status is BJStatus.SURRENDER:
    result = BJResult.SURRENDER
    reward = -wager*0.5
  else:
    multiplier = 1 if hand.status is BJStatus.STAND else 2 # only other possible status is double down
    result = check_win(hand, game.dealer_hand)
    reward = wager*multiplier if result in (BJResult.WON, BJResult.PUSHED) else -wager*multiplier
  player.bankroll += reward if result is not BJResult.PUSHED else 0
  player.update_db()
  return result.value, reward

def create_display_message(game, end_of_game):
  nth = ('first', 'second', 'third', 'fourth')
  status_display = ('active', 'natural blackjack (auto stood)', 'bust', 'stood', 'doubled down', 'forfeit')

  if end_of_game:
    dealer_hand = f"Dealer's hand:\n{'  '.join(game.dealer_hand.cards)}"
  else:
    dealer_hand = f"Dealer's hand:\n{game.dealer_hand.cards[0]}"
    
  player_hands = '\n\n'.join([f"{player.name}'s {nth[index]} hand: (status: {status_display[hand.status.value]}){', insured' if player.insured else ''}\n{'  '.join(hand.cards)}" for player in game.players.values() for index, hand in enumerate(player.hands)])
  
  return f"{dealer_hand}\n\n{player_hands}"

def game_is_active(game):
  for player in game.players.values():
    for hand in player.hands:
      if hand.status is BJStatus.ACTIVE:
        return True
  return False

def check_insurance(player, game):
  if game.dealer_hand.value == 21 and len(game.dealer_hand.cards) == 2:
    result = 'won'
    reward = player.wager
  else:
    result = 'lost'
    reward = -player.wager*0.5
  player.bankroll += reward
  player.update_db()
  return result, reward

def find_active_hand(player):
  for hand in player.hands:
    if hand.status is BJStatus.ACTIVE:
      return hand

def bjgame_containing_id(id, game_list):
  # Checks each game to see if the player is in a blackjack game
  for game in game_list:
    if isinstance(game, bjgame) and id in game.players:
      return game
