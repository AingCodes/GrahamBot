from custom_types import BJStatus, BJDecision, BJPlayer, Hand
from yahtzee import refresh_dice, refresh_scoresheet
from misc import create_buttons, get_from_db, update_db
import asyncio
import inflect
import bj
import wordle

game_list = []
all_players = []

class yahtzeegame:
  def __init__(self):
    self.players = []
    self.turn = 0
    self.basic = (None, 'Aces', 'Twos', 'Threes', 'Fours', 'Fives', 'Sixes')
    self.wager = None

  def increment(self):
    self.turn += 1
    self.turn = self.turn % len(self.players)

  def get_results(self):
    scores = [self.players[0]]
    for player in self.players[1:]:
      for index, p in enumerate(scores):
        if player.scoresheet['**Total Score**'] > p.scoresheet['**Total Score**']:
          scores.insert(index, player)
      if player not in scores:
        scores.append(player)

    p = inflect.engine()
    message = [f"In {p.ordinal(i+1)} place: {player.name} with a score of {player.scoresheet['**Total Score**']} points" for i, player in enumerate(scores)]
    if self.wager:
      winnings = 0
      for player in scores[1:]:
        winnings += self.wager
        loserbal = get_from_db("bank_of_graham.json", player.id)
        loserbal = loserbal - self.wager
        update_db("bank_of_graham.json", player.id, loserbal)
      bal = get_from_db("bank_of_graham.json", scores[0].id)
      bal = bal + winnings
      update_db("bank_of_graham.json", scores[0].id, bal)
      message.append(f"{scores[0].name} won {winnings} Grahams! This amount has been added to their balance.")
    return "\n".join(message)

  async def resolve_interaction(self, id, player, type):
    score = 0
    if id in self.basic:
      value = self.basic.index(id) # the points awarded is equal to the index in the tuple
      for die in player.dice:
        if die == value:
          score += value        

    elif id == 'Chance':
      for die in player.dice:
          score += die

    elif id == 'Three of a Kind':
      for die in player.dice:
        if player.dice.count(die) >= 3:
          score = sum(player.dice)
          break
            
    elif id == 'Four of a Kind':
      for die in player.dice:
        if player.dice.count(die) >= 4:
          score = sum(player.dice)
          break

    elif id == 'Full House':
      if player.dice.count(player.dice[0]) in (2, 3) and len(set(player.dice)) == 2:
        score = 25

    elif id == 'Small Straggot':
      dice_as_set = set(player.dice)
      if (
        {1,2,3,4}.issubset(dice_as_set) or 
        {2,3,4,5}.issubset(dice_as_set) or 
        {3,4,5,6}.issubset(dice_as_set)
      ):
        score = 30

    elif id == 'Large Straggot':
      if sorted(player.dice) == list(range(min(player.dice), max(player.dice)+1)):
        score = 40

    elif id == 'Grahamzee':
      if player.dice.count(player.dice[0]) == 5:
        score = 50

    elif id in ('1', '2', '3', '4', '5'):
      player.held[int(id)-1] = True if not player.held[int(id)-1] else False
      await refresh_dice(self.dice_message, player)

    elif id == 'roll':
      await player.roll_dice(self.dice_message)

    if type == 3:
      player.scoresheet[id] = score

    player.check_scores()
    await refresh_scoresheet(self.sheet_message, player)
      
    if type == 3:
      await refresh_scoresheet(self.sheet_message, player, True)
      self.increment()
      player.reset_dice()

      if len(self.players) > 1:
        await asyncio.sleep(3)
      
      await refresh_scoresheet(self.sheet_message, self.players[self.turn])
      await refresh_dice(self.dice_message, self.players[self.turn])


class bjgame:
  __slots__ = ('deck_count', 'players', 'deck', 'dealer_hand', 'wagers', 'display_message')
  
  def __init__(self, names, ids, deck_count):
    self.deck_count = deck_count
    self.players = {id: BJPlayer(name, id) for name, id in zip(names, ids)}
    self.deck = bj.create_deck(deck_count)
    self.dealer_hand = Hand()
    self.wagers = {}

  def reshuffle_deck(self):
    self.deck = bj.create_deck(self.deck_count)

  async def refresh_display(self, end_of_game = False):
    if not end_of_game:
      await self.display_message.edit(content = bj.create_display_message(self, end_of_game))
    else:
      await self.display_message.edit(content = bj.create_display_message(self, end_of_game), view=None)

  async def reset(self, ctx):
    self.players = {id: BJPlayer(player.name, id) for id, player in self.players.items()}
    self.dealer_hand = Hand()
    self.wagers = {}

    if len(self.deck) < 20*len(self.players):
      self.reshuffle_deck
      await ctx.send("Deck was reshuffled!")

  async def run(self, ctx, bot):
    global game_list
    names = ', '.join([player.name for player in self.players.values()])

    # Waits for each player to submit a wager
    wager_msg_content = [f"Blackjack game started for {names}! Please enter a wager.", "Bankrolls:"]
    wager_msg_content.extend((f"{player.name}: {player.bankroll}" for player in self.players.values()))
    wager_msg = await ctx.send("\n".join(wager_msg_content))
    await bot.wait_for('command_completion', check = lambda x: len(self.wagers) == len(self.players) or self not in game_list)
    await wager_msg.delete()
    
    # Ends the function if the game was aborted
    if self not in game_list:
      return

    # Sets the wager for each player
    for id, wager in self.wagers.items():
      self.players[id].wager = wager
      self.players[id].sum()

    # Deals 2 cards to the dealer and all players
    bj.hit(self.dealer_hand, 2, self.deck)
    for player in self.players.values():
      bj.hit(player.hands[0], 2, self.deck)

    # Checks for any natural blackjacks
    for player in self.players.values():
      if player.hands[0].value == 21:
        player.hands[0].status = BJStatus.BLACKJACK

    # Creates an interactable message that displays all hands 
    labels = tuple(enum.value for enum in BJDecision)
    view = create_buttons(ids=labels, labels=labels)
    self.display_message = await ctx.send(f"{bj.create_display_message(self, False)}", view=view)
    
    # Waits for all players to finish their hand before moving on
    while bj.game_is_active(self):
      interaction = await bot.wait_for('interaction')
      button_id = interaction.data['custom_id']
      player = self.players[str(interaction.user.id)]

      # Ends the interaction if the interactor is not playing
      if player not in self.players.values():
        await interaction.response.defer()
        continue

      # Grabs the player's first active hand as hand
      hand = bj.find_active_hand(player)

      # Ends the interaction if there were no active hands
      if not hand:
        await interaction.response.defer()
        continue

      # Executes the player's request
      """match button_id:
        case BJDecision.HIT.value:
          bj.hit(hand, 1, self.deck)
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
            bj.hit(hand, 1, self.deck)
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
            bj.split(hand, player, self)


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
          hand.status = BJStatus.SURRENDER"""


      await self.refresh_display()
      await interaction.response.defer()


    # The dealer takes their turn
    while self.dealer_hand.value < 17:
      bj.hit(self.dealer_hand, 1, self.deck)
    await self.refresh_display(True)

    # Creates a message that shows the results of all hands
    nth = ('first', 'second', 'third', 'fourth')

    results = []
    for player in self.players.values():
      for index, hand in enumerate(player.hands):
        result, reward = bj.resolve_hand(hand, player, self)
        results.append(f"{player.name}'s {nth[index]} hand {result}! {'Won' if result in ('won', 'blackjack') else 'Refunded' if result == 'pushed' else 'Lost'} {-reward if result in ('lost', 'bust', 'surrendered') else reward} Grahams.")
      if player.insured:
        result, reward = bj.check_insurance(player, self)
        results.append(f"{player.name}'s insurance bet {result}! {'Won' if result == 'won' else 'lost'} {reward} Grahams!")

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
      game_list.remove(self)

class wordlegame:
  