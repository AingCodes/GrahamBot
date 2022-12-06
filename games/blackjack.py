from enum import Enum, auto
from misc import update_db, get_from_db, create_buttons
from typing import Tuple, List, Dict
from random import shuffle

class BJStatus(Enum):
  ACTIVE = auto()
  BLACKJACK = auto()
  BUST = auto()
  STAND = auto()
  DOUBLE_DOWN = auto()
  SURRENDER = auto()

class BJResult(Enum):
  WON = auto()
  PUSHED = auto()
  LOST = auto()
  BLACKJACK = auto()
  BUST = auto()
  SURRENDER = auto()

class BJDecision(Enum):
  HIT = auto()
  STAND = auto()
  DOUBLE_DOWN = auto()
  SPLIT = auto()
  INSURE = auto()
  SURRENDER = auto()

NTH = ("first", "second", "third", "fourth")
STATUS_DISPLAY = {
    BJStatus.ACTIVE: "Active",
    BJStatus.BLACKJACK: "Natural Blackjack",
    BJStatus.BUST: "Bust",
    BJStatus.STAND: "Stood",
    BJStatus.DOUBLE_DOWN: "Doubled down",
    BJStatus.SURRENDER: "Forfeit"
}
RESULT_DISPLAY = {
  BJResult.WON: ("won", "Won"),
  BJResult.BLACKJACK: ("got a blackjack", "Won"),
  BJResult.BUST: ("bust", "Lost"),
  BJResult.LOST: ("lost", "Lost"),
  BJResult.PUSHED: ("pushed", "Refunded"),
  BJResult.SURRENDER: ("was forfeit", "Lost")
}
BUTTON_LABELS = {
  BJDecision.HIT: "Hit",
  BJDecision.STAND: "Stand",
  BJDecision.DOUBLE_DOWN: "Double Down",
  BJDecision.SPLIT: "Split",
  BJDecision.INSURE: "Insurance",
  BJDecision.SURRENDER: "Surrender"
}

class BJPlayer:
  __slots__ = ('name', 'id', 'hands', 'insured', 'bankroll', 'wager', 'total_bet')
  def __init__(self, name, id):
    self.name = name
    self.id = id
    self.hands = [Hand()]
    self.insured = False
    self.bankroll = self.set_bankroll()
    self.wager = 0

  def set_bankroll(self):
    try:
      return get_from_db('bank_of_graham.json', self.id)
    except:
      update_db('bank_of_graham.json', self.id, 1000)
      return 1000

  def update_db(self):
    update_db('bank_of_graham.json', self.id, self.bankroll)

  def sum(self):
    sum = 0
    for hand in self.hands:
      if hand.status is BJStatus.DOUBLE_DOWN:
        sum += self.wager*2
      else:
        sum += self.wager
    if self.insured == True:
      sum += self.wager*0.5
    self.total_bet = sum

  def __str__(self):
    return "\n\n".join([f"{self.name}'s {NTH[i]} hand: (Status: {STATUS_DISPLAY[hand.status]})\n{hand}" for i, hand in enumerate(self.hands)])

class Hand:
  __slots__ = ('cards', 'value', 'status')

  def __init__(self):
    self.cards = []
    self.status = BJStatus.ACTIVE

  def __str__(self):
    return "  ".join(self.cards)

  def card_value(self, card_number: int) -> int:
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

  def hit(self, amount, deck):
      self.cards.extend([deck.pop(0) for _ in range(amount)])
      self.hand_value()

class BJGame:
  __slots__ = ('deck_count', 'players', 'deck', 'dealer_hand', 'wagers', 'display_message')
  
  def __init__(self, names: Tuple[str, ...], ids: Tuple[str, ...], deck_count: int):
    self.deck_count = deck_count
    self.players = {id: BJPlayer(name, id) for name, id in zip(names, ids)}
    self.deck = create_deck(deck_count)
    self.dealer_hand = Hand()
    self.wagers: Dict[str, int] = {}

  def reshuffle_deck(self):
    self.deck = create_deck(self.deck_count)

  async def refresh_display(self, end_of_game = False):
    if not end_of_game:
      await self.display_message.edit(content = create_display_message(self, end_of_game))
    else:
      await self.display_message.edit(content = create_display_message(self, end_of_game), view=None)

  async def reset(self, ctx):
    self.players = {id: BJPlayer(player.name, id) for id, player in self.players.items()}
    self.dealer_hand = Hand()
    self.wagers = {}

    if len(self.deck) < 20*len(self.players):
      self.reshuffle_deck
      await ctx.send("Deck was reshuffled!")

  async def run(self, ctx, bot):
    from games.commands import GLOBAL_GAME_LIST
    names = ', '.join([player.name for player in self.players.values()])

    # Waits for each player to submit a wager
    wager_msg_content = [f"Blackjack game started for {names}! Please enter a wager.", "Bankrolls:"]
    wager_msg_content.extend((f"{player.name}: {player.bankroll}" for player in self.players.values()))
    wager_msg = await ctx.send("\n".join(wager_msg_content))
    await bot.wait_for('command_completion', check = lambda x: len(self.wagers) == len(self.players) or self not in GLOBAL_GAME_LIST)
    await wager_msg.delete()
    
    # Ends the function if the game was aborted
    if self not in GLOBAL_GAME_LIST:
      return

    # Sets the wager for each player
    for id, wager in self.wagers.items():
      self.players[id].wager = wager
      self.players[id].sum()

    # Deals 2 cards to the dealer and all players
    self.dealer_hand.hit(2, self.deck)
    for player in self.players.values():
      player.hands[0].hit(2, self.deck)

    # Checks for any natural blackjacks
    for player in self.players.values():
      if player.hands[0].value == 21:
        player.hands[0].status = BJStatus.BLACKJACK

    # Creates an interactable message that displays all hands 
    labels = tuple(BUTTON_LABELS[enum] for enum in BJDecision)
    ids = tuple(str(enum.value) for enum in BJDecision)
    view = create_buttons(ids=ids, labels=labels)
    self.display_message = await ctx.send(f"{create_display_message(self, False)}", view=view)
    
    # Waits for all players to finish their hand before moving on
    while game_is_active(self):
      interaction = await bot.wait_for('interaction')
      button_id = interaction.data['custom_id']
      player = self.players[str(interaction.user.id)]

      # Ends the interaction if the interactor is not playing
      if player not in self.players.values():
        await interaction.response.defer()
        continue

      hand = None
      # Grabs the player's first active hand as hand
      for cand_hand in player.hands:
        if cand_hand.status is BJStatus.ACTIVE:
          hand = cand_hand
        
      # Ends the interaction if there were no active hands
      if not hand:
        await interaction.response.defer()
        continue

      # Executes the player's request
      match int(button_id):
        case BJDecision.HIT.value:
          hand.hit(1, self.deck)
          if hand.value > 21:
            hand.status = BJStatus.BUST
          elif hand.value == 21:
            hand.status = BJStatus.STAND

        case BJDecision.STAND.value:
          hand.status = BJStatus.STAND

        case BJDecision.DOUBLE_DOWN.value:
          if player.total_bet + player.wager > player.bankroll:
            await interaction.response.send_message(content='You do not have enough Grahams available to double down.', ephemeral=True)
            continue
          elif not len(hand.cards) == 2:
            await interaction.response.send_message(content='You may only double down on 2 cards', ephemeral=True)
            continue
          else:
            hand.hit(1, self.deck)
            hand.status = BJStatus.DOUBLE_DOWN

        case BJDecision.SPLIT.value:
          if player.total_bet + player.wager > player.bankroll:
            await interaction.response.send_message(content='You do not have enough Grahams to split', ephemeral=True)
          elif (not len(hand.cards) == 2 or
                not hand.card_value(0) == hand.card_value(1) and
                not hand.value == 16
              ):
                await interaction.response.send_message(content='To split, you must have exactly two cards of equal value, or exactly two cards that total to 16.', ephemeral=True)
          elif len(player.hands) > 3:
            await interaction.response.send_message(content='You may only have up to 4 hands', ephemeral=True)
          else:
            player.hands.append(Hand())
            player.hands[-1].cards = [hand.cards[1]]
            hand.cards = [hand.cards[0]]
            hand.hand_value()
            player.hands[-1].hand_value()

        case BJDecision.INSURE.value:
          if player.insured:
            await interaction.response.send_message(content='You already took insurance', ephemeral=True)
          elif player.total_bet + player.wager*2 > player.bankroll:
            await interaction.response.send_message(content='You do not have enough Grahams to take insurance', ephemeral=True)
          elif not self.dealer_hand.cards[0][:-2] == 'A':
            await interaction.response.send_message(content='You may only take insurance when the dealer is showing an Ace', ephemeral=True)
          else:
            player.insured = True
            player.sum()

        case BJDecision.SURRENDER.value:
          hand.status = BJStatus.SURRENDER

      await self.refresh_display()
      await interaction.response.defer()

    # The dealer takes their turn
    while self.dealer_hand.value < 17:
      self.dealer_hand.hit(1, self.deck)
    await self.refresh_display(True)

    # Creates a message that shows the results of all hands
    results = []
    for player in self.players.values():
      for index, hand in enumerate(player.hands):
        result, reward = resolve_hand(hand, player, self.dealer_hand)
        results.append(f"{player.name}'s {NTH[index]} hand {RESULT_DISPLAY[result][0]}! {RESULT_DISPLAY[result][1]} {-reward if result in (BJResult.LOST, BJResult.BUST, BJResult.SURRENDER) else reward} Grahams.")
      if player.insured:
        result, reward = check_insurance(player, self)
        results.append(f"{player.name}'s insurance bet {result.lower()}! {result} {reward} Grahams!")

    await ctx.send('\n'.join(results))

    # Asks if the player would like to play again

    labels = ('Yes', 'No')
    view = create_buttons(labels=labels, ids=labels)
    reset_message = await ctx.send('Would you like to play again?', view=view)

    interaction = await bot.wait_for('interaction')
    button_id = interaction.data['custom_id']

    if button_id == 'Yes':
      await self.reset(ctx)
      await reset_message.delete()
      await interaction.response.send_message('A new game has started.')
      await self.run(ctx, bot)

    else:
      await reset_message.delete()
      await interaction.response.defer()
      await ctx.send('The game has ended.')
      GLOBAL_GAME_LIST.remove(self)

def create_deck(deck_count) -> List[str]:
  ranks = ("A", "2", "3", "4", "5", "6", "7", "8", "9", "10", "J", "Q", "K")
  suits = ("♠️", "♥️", "♣️", "♦️")
  deck = [rank + suit for rank in ranks for suit in suits for _ in range(deck_count)]
  shuffle(deck)
  return deck

def create_display_message(game, end_of_game) -> str:
  if end_of_game:
    dealer_hand = f"Dealer's hand:\n{game.dealer_hand}"
  else:
    dealer_hand = f"Dealer's hand:\n{game.dealer_hand.cards[0]}"

  player_hands = "\n\n".join([f"{player}" for player in game.players.values()])

  return f"{dealer_hand}\n\n{player_hands}"

def game_is_active(game) -> bool:
  for player in game.players.values():
    for hand in player.hands:
      if hand.status is BJStatus.ACTIVE:
        return True
  return False

def check_win(phand, dhand) -> BJResult:
  result = BJResult.LOST
  if phand.value < 22:
    if dhand.value < phand.value or dhand.value > 21:
      result = BJResult.WON
    elif phand.value == dhand.value:
      result = BJResult.PUSHED
  return result

def resolve_hand(hand: Hand, player: BJPlayer, dealer_hand: Hand) -> Tuple[BJResult, int]:
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
    multiplier = 1 if hand.status is BJStatus.STAND else 2 # stand or double down
    result = check_win(hand, dealer_hand)
    reward = wager*multiplier if result in (BJResult.WON, BJResult.PUSHED) else -wager*multiplier
  player.bankroll += 0 if result is BJResult.PUSHED else reward
  player.update_db()
  return result, reward

def check_insurance(player: BJPlayer, dealer_hand: Hand) -> Tuple[str, int]:
  if dealer_hand.value == 21 and len(dealer_hand.cards) == 2:
    result = 'Won'
    reward = player.wager
  else:
    result = 'Lost'
    reward = -player.wager*0.5
  player.bankroll += reward
  player.update_db()
  return result, reward