from logging import handlers
from random import shuffle
import games
import discord
import players
from misc import create_buttons

from enum import Enum

class Status(Enum):
  ACTIVE = 0
  BLACKJACK = 1
  BUST = 2
  STAND = 3
  DOUBLE_DOWN = 4
  SURRENDER = 5

class Result(Enum):
  WON = 'won'
  PUSHED = 'pushed'
  LOST = 'lost'
  BLACKJACK = 'got a blackjack'
  BUST = 'bust'
  SURRENDER = 'surrendered'

class Hand:
  __slots__ = ('cards', 'value', 'status')

  def __init__(self):
    self.cards = []
    self.status = Status.ACTIVE

  def card_value(self, card_number):
    rank = self.cards[card_number][:-2]
    if rank == 'A':
      value = 11
    elif rank in ('J', 'Q', 'K'):
      value = 10
    else:
      value = int(rank)
    return value

  def hand_value(self):
    value = 0
    ace_count = 0
    for card_number, card in enumerate(self.cards):
      rank = card[:-2]
      value += self.card_value(card_number)
      if rank == 'A':
        ace_count += 1
    for ace in range(ace_count):
      if value > 21:
        value -= 10
    self.value = value

def create_deck(deck_count):
  ranks = ("A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K")
  suits = ("♠️", "♥️", "♣️", "♦️")
  deck = [rank + suit for rank in ranks for suit in suits for i in range(deck_count)]
  shuffle(deck)
  return deck

def hit(hand, amount, deck):
  hand.cards.extend([deck.pop(0) for i in range(amount)])
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
  result = Result.LOST
  if phand.value < 22:
    if dhand.value < phand.value or dhand.value > 21:
      result = Result.WON
    elif phand.value == dhand.value:
      result = Result.PUSHED
  return result

def resolve_hand(hand, player, game):
  wager = player.wager
  if hand.status is Status.BLACKJACK:
    reward = wager * 3/2
    result = Result.BLACKJACK
  elif hand.status is Status.BUST:
    reward = -wager
    result = Result.BUST
  elif hand.status is Status.SURRENDER:
    result = Result.SURRENDER
    reward = -wager*0.5
  else:
    multiplier = 1 if hand.status is Status.STAND else 2
    result = check_win(hand, game.dealer_hand)
    reward = wager*multiplier if result in (Result.WON, Result.PUSHED) else -wager*multiplier
  player.bankroll += reward if not result is Result.PUSHED else 0
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
      if hand.status is Status.ACTIVE:
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

async def reset_game(ctx, game):
  game.wagers = {}
  game.dealer_hand = Hand()
  game.players = {id: players.bjplayer(name, id) for name in game.name_list for id in game.id_list}
  if len(game.deck) < 20*len(game.players):
    game.reshuffle_deck()
    await ctx.send('Deck was reshuffled!')

async def is_playing(ctx):
  # Checks each game to see if the player is in a blackjack game
  playing_blackjack = None
  for game in games.game_list:
    if isinstance(game, games.bjgame) and str(ctx.author.id) in game.id_list:
      playing_blackjack = True
      current_game = game
      break

  # Exits if they are not
  if not playing_blackjack:
    await ctx.send(f"<@{ctx.author.id}> you are not playing blackjack.")
    return False, None

  # If they are, returns True along with the game they are playing in
  return True, current_game

async def refresh_display(game, end_of_game=False):
  if not end_of_game:
    await game.display_message.edit(content = create_display_message(game, end_of_game))
  else:
    await game.display_message.edit(content = create_display_message(game, end_of_game), view=None)
  
async def run(ctx, bot, game):
  names = ', '.join([player.name for player in game.players.values()])

  # Waits for each player to submit a wager
  wager_msg_content = [f"Blackjack game started for {names}! Please enter a wager.", "Bankrolls:"]
  for player in game.players.values():
    wager_msg_content.append(f"{player.name}: {player.bankroll}")
  wager_msg = await ctx.send("\n".join(wager_msg_content))
  await bot.wait_for('command_completion', check = lambda x: len(game.wagers) == len(game.players) or game not in games.game_list)
  await wager_msg.delete()
  
  # Ends the function if the game was aborted
  if game not in games.game_list:
    return

  # Sets the wager for each player
  for id, wager in game.wagers.items():
    game.players[id].wager = wager
    game.players[id].sum()

  # Deals 2 cards to the dealer and all players
  hit(game.dealer_hand, 2, game.deck)
  for player in game.players.values():
    hit(player.hands[0], 2, game.deck)

  # Checks for any natural blackjacks
  for player in game.players.values():
    if player.hands[0].value == 21:
      player.hands[0].status = Status.BLACKJACK

  # Creates an interactable message that displays all hands 
  labels = ('Hit', 'Stand', 'Double Down', 'Split', 'Insurance', 'Surrender')
  ids = ('h', 's', 'd', 'x', 'i', 'ff')
  view = create_buttons(ids=ids, labels=labels)
  game.display_message = await ctx.send(f"{create_display_message(game, False)}", view=view)
  
  # Waits for all players to finish their hand before moving on
  while game_is_active(game):
    interaction = await bot.wait_for('interaction')
    button_id = interaction.data['custom_id']
    player = game.players[str(interaction.user.id)]

    # Ends the interaction if the interactor is not playing
    if player not in game.players.values():
      await interaction.response.defer()
      continue

    # Grabs the player's first active hand as current_hand
    current_hand = None
    for hand in player.hands:
      if hand.status is Status.ACTIVE:
        current_hand = hand
        break

    # Ends the interaction if there were no active hands
    if not current_hand:
      await interaction.response.defer()
      continue

    #  Executes the player's request
    if button_id == 'h':
      hit(current_hand, 1, game.deck)
      if current_hand.value > 21:
        current_hand.status = Status.BUST
      elif current_hand.value == 21:
        current_hand.status = Status.STAND
      await refresh_display(game)
      await interaction.response.defer()

    elif button_id == 's':
      current_hand.status = Status.STAND
      await refresh_display(game)
      await interaction.response.defer()

    elif button_id == 'd':
      if player.total_bet + player.wager > player.bankroll:
        await interaction.response.send_message(content='You do not have enough Grahams available to double down.', ephemeral=True)
      elif not len(current_hand.cards) == 2:
        await interaction.response.send_message(content='You may only double down on 2 cards', ephemeral=True)
      else:
        hit(current_hand, 1, game.deck)
        current_hand.status = Status.DOUBLE_DOWN
        await refresh_display(game)
        await interaction.response.defer()

    elif button_id == 'x':
      if player.total_bet + player.wager > player.bankroll:
        await interaction.response.send_message(content='You do not have enough Grahams to split', ephemeral=True)
      elif (not len(current_hand.cards) == 2 or
            not current_hand.card_value(0) == current_hand.card_value(1) and
            not current_hand.value == 16
           ):
             await interaction.response.send_message(content='To split, you must have exactly two cards of equal value, or exactly two cards that total to 16.', ephemeral=True)
      elif len(player.hands) > 3:
        await interaction.response.send_message(content='You may only have up to 4 hands', ephemeral=True)
      else:
        split(current_hand, player, game)
        await refresh_display(game)
        await interaction.response.defer()

    elif button_id == 'i':
      if player.insured == True:
        await interaction.response.send_message(content='You already took insurance', ephemeral=True)
      elif player.total_bet + player.wager*2 > player.bankroll:
        await interaction.response.send_message(content='You do not have enough Grahams to take insurance', ephemeral=True)
      elif not game.dealer_hand.cards[0][:-2] == 'A':
        await interaction.response.send_message(content='You may only take insurance when the dealer is showing an Ace', ephemeral=True)
      else:
        player.insured = True
        player.sum()
        await interaction.response.defer()

    elif button_id == 'ff':
      current_hand.status = Status.SURRENDER
      await refresh_display(game)
      await interaction.response.defer()


  # The dealer takes their turn
  while game.dealer_hand.value < 17:
    hit(game.dealer_hand, 1, game.deck)
  await refresh_display(game, True)

  # Creates a message that shows the results of all hands
  nth = ('first', 'second', 'third', 'fourth')

  results = []
  for player in game.players.values():
    for index, _hand in enumerate(player.hands):
      result, reward = resolve_hand(_hand, player, game)
      results.append(f"{player.name}'s {nth[index]} hand {result}! {'Won' if result in ('won', 'blackjack') else 'Refunded' if result == 'pushed' else 'Lost'} {-reward if result in ('lost', 'bust', 'surrendered') else reward} Grahams.")
    if player.insured:
      result, reward = check_insurance(player, game)
      results.append(f"{player.name}'s insurance bet {result}! {'Won' if result == 'won' else 'lost'} {reward} Grahams!")

  await ctx.send('\n'.join(results))

  # Asks if the player would like to play again

  labels = ('Yes', 'No')
  ids = ('y', 'n')
  view = create_buttons(labels=labels, ids=ids)
  reset_message = await ctx.send('Would you like to play again?', view=view)

  interaction = await bot.wait_for('interaction')
  button_id = interaction.data['custom_id']

  if button_id == 'y':
    await reset_game(ctx, game)
    await reset_message.delete()
    await interaction.response.send_message('A new game has started.')
    await run(ctx, bot, game)

  elif button_id == 'n':
    await reset_message.delete()
    await interaction.response.defer()
    await ctx.send('The game has ended.')
    games.game_list.remove(game)