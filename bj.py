from random import shuffle
import games
import discord
import hand
import players
from misc import create_buttons

def create_deck(deck_count):
  ranks = ("A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K")
  suits = ("♠️", "♥️", "♣️", "♦️")
  deck = [rank + suit for rank in ranks for suit in suits for i in range(deck_count)]
  shuffle(deck)
  return deck

def hit(hand, amount, deck):
  hand.cards.extend([deck.pop(0) for i in range(amount)])
  hand.hand_value()
  return

def split(hand_to_split, player, game):
  # Creates a new hand
  player.hands.append(hand.hand())
  # The new hand contains the 2nd card of the original hand
  player.hands[-1].cards = [hand_to_split.cards[1]]
  # The 2nd card is removed from the original hand
  hand_to_split.cards = [hand_to_split.cards[0]]
  # Hand values are recalculated
  hand_to_split.hand_value()
  player.hands[-1].hand_value()

def check_win(phand, dhand):
  result = 'lost'
  if phand.value < 22:
    if dhand.value < phand.value or dhand.value > 21:
      result = 'won'
    elif phand.value == dhand.value:
      result = 'pushed'
  return result

def resolve_hand(hand, player, game):
  wager = player.wager
  if hand.status == 'blackjack':
    reward = wager * 3/2
    result = 'blackjack'
  elif hand.status == 'bust':
    reward = -wager
    result = 'bust'
  elif hand.status == 'stand':
    result = check_win(hand, game.dealer_hand)
    reward = wager if result in ['won', 'pushed'] else -wager
  elif hand.status == 'double down':
    result = check_win(hand, game.dealer_hand)
    reward = wager*2 if result in ['won', 'pushed'] else -wager*2
  elif hand.status == 'surrender':
    result = 'surrendered'
    reward = -wager*0.5
  player.bankroll += reward if not result == 'pushed' else 0
  player.update_db()
  return result, reward
  
  
def check_for_naturals(game):
  for player in game.players.values():
    if player.hands[0].value == 21:
      player.hands[0].status = 'blackjack'

def create_display_message(game, end_of_game):
  nth = ['first', 'second', 'third', 'fourth']

  if end_of_game:
    dealer_hand = f"Dealer's hand:\n{'  '.join(game.dealer_hand.cards)}"
  else:
    dealer_hand = f"Dealer's hand:\n{game.dealer_hand.cards[0]}"
    
  player_hands = '\n\n'.join([f"{player.name}'s {nth[index]} hand: (status: {hand.status}){', insured' if player.insured else ''}\n{'  '.join(hand.cards)}" for player in game.players.values() for index, hand in enumerate(player.hands)])
  
  return f"{dealer_hand}\n\n{player_hands}"

def game_is_active(game):
  for player in game.players.values():
    for _hand in player.hands:
      if _hand.status == 'active':
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
  game.dealer_hand = hand.hand()
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
    return False, False

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
  check_for_naturals(game)

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
    for _hand in player.hands:
      if _hand.status == 'active':
        current_hand = _hand
        break

    # Ends the interaction if there were no active hands
    if not current_hand:
      await interaction.response.defer()
      continue

    #  Executes the player's request
    if button_id == 'h':
      hit(current_hand, 1, game.deck)
      if current_hand.value > 21:
        current_hand.status = 'bust'
      elif current_hand.value == 21:
        current_hand.status = 'stand'
      await refresh_display(game)
      await interaction.response.defer()
      

    elif button_id == 's':
      current_hand.status = 'stand'
      await refresh_display(game)
      await interaction.response.defer()

    elif button_id == 'd':
      if player.total_bet + player.wager > player.bankroll:
        await interaction.response.send_message(content='You do not have enough Grahams available to double down.', ephemeral=True)
      elif not len(current_hand.cards) == 2:
        await interaction.response.send_message(content='You may only double down on 2 cards', ephemeral=True)
      else:
        hit(current_hand, 1, game.deck)
        current_hand.status = 'double down'
        await refresh_display(game)
        await interaction.response.defer()

    elif button_id == 'x':
      if player.total_bet + player.wager > player.bankroll:
        await interaction.response.send_message(content='You do not have enough Grahams to split', ephemeral=True)
      elif (not len(current_hand.cards) == 2 
            or not current_hand.card_value(0) == current_hand.card_value(1)
            and not current_hand.value == 16
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
      current_hand.status = 'surrender'
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
      results.append(f"{player.name}'s {nth[index]} hand {'got a blackjack!' if result == 'blackjack' else result}! {'Won' if result in ('won', 'blackjack') else 'Refunded' if result == 'pushed' else 'Lost'} {-reward if result in ('lost', 'bust', 'surrendered') else reward} Grahams.")
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