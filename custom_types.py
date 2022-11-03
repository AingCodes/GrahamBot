from enum import Enum
from misc import get_from_db, update_db

class BJStatus(Enum):
  ACTIVE = 0
  BLACKJACK = 1
  BUST = 2
  STAND = 3
  DOUBLE_DOWN = 4
  SURRENDER = 5

class BJResult(Enum):
  WON = 'won'
  PUSHED = 'pushed'
  LOST = 'lost'
  BLACKJACK = 'got a blackjack'
  BUST = 'bust'
  SURRENDER = 'surrendered'

class BJDecision(Enum):
  HIT = 'Hit'
  STAND = 'Stand'
  DOUBLE_DOWN = 'Double Down'
  SPLIT = 'Split'
  INSURE = 'Insure'
  SURRENDER = 'Surrender'

class Hand:
  __slots__ = ('cards', 'value', 'status')

  def __init__(self):
    self.cards = []
    self.status = BJStatus.ACTIVE

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

class BJPlayer:
  __slots__ = ('name', 'id', 'hands', 'insured', 'bankroll', 'wager', 'total_bet')
  def __init__(self, name, id):
    self.name = name
    self.id = id
    self.hands = [Hand()]
    self.insured = False
    self.bankroll = self.set_bankroll()

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