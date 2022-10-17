import random
from bj import Hand, Status
import jsonfuncs
from yahtzee import refresh_dice

class yahtzeeplayer:
  __slots__ = ('id', 'name', 'dice', 'held', 'roll_amount', 'active', 'scoresheet')

  def __init__(self, id, name):
    self.id = id
    self.name = name
    self.dice = [random.randint(1,6) for i in range(5)]
    self.held = [False, False, False, False, False]
    self.roll_amount = 0
    self.active = True
    self.scoresheet = {
      'Aces': 0,
      'Twos': 0, 
      'Threes': 0,
      'Fours': 0,
      'Fives': 0,
      'Sixes': 0,
      'Total Top Score': 0,
      'Bonus': '0',
      'Chance': 0,
      'Three of a Kind': 0,
      'Four of a Kind': 0,
      'Full House': 0,
      'Small Straggot': 0,
      'Large Straggot': 0,
      'Grahamzee': 0,
      'Total Score': 0,
    }

  async def roll_dice(self, dice_message):
    for i, x in enumerate(self.dice):
      if not self.held[i]:
        self.dice[i] = random.randint(1,6)
    await refresh_dice(dice_message, self)
    self.roll_amount += 1

  def reset_dice(self):
    self.held = [False, False, False, False, False]
    self.dice = [random.randint(1,6) for i in range(5)]
    self.roll_amount = 0

  def check_scores(self):
    self.scoresheet['Total Top Score'] = 0
    self.scoresheet['Total Score'] = 0
    for key, value in self.scoresheet.items():
      if key == 'Total Top Score':
        break
      else:
        self.scoresheet['Total Top Score'] += 0 if value == '0' else value

    if self.scoresheet['Total Top Score'] > 63:
      self.scoresheet['Bonus'] = 35

    for key, value in self.scoresheet.items():
      if not key in ('Total Top Score', 'Total Score'):
        self.scoresheet['Total Score'] += 0 if value == '0' else value

    if not self.scoresheet['Total Top Score']:
      self.scoresheet['Total Top Score'] = '0'
        
      

class bjplayer:
  __slots__ = ('name', 'id', 'hands', 'insured', 'bankroll', 'wager', 'total_bet')
  def __init__(self, name, id):
    self.name = name
    self.id = id
    self.hands = [Hand()]
    self.insured = False
    self.bankroll = self.set_bankroll()

  def set_bankroll(self):
    try:
      return jsonfuncs.get_from_db('bank_of_graham.json', self.id)
    except:
      jsonfuncs.update_db('bank_of_graham.json', self.id, 1000)
      return 1000

  def update_db(self):
    jsonfuncs.update_db('bank_of_graham.json', self.id, self.bankroll)

  def sum(self):
    sum = 0
    for hand in self.hands:
      if hand.status is Status.DOUBLE_DOWN:
        sum += self.wager*2
      else:
        sum += self.wager
    if self.insured == True:
      sum += self.wager*0.5
    self.total_bet = sum