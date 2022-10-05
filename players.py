import random
import hand
import jsonfuncs

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
      'Aces': '',
      'Twos': '', 
      'Threes': '',
      'Fours': '',
      'Fives': '',
      'Sixes': '',
      'Total top score': 0,
      'Bonus': '',
      'Chance': '',
      'Three of a Kind': '',
      'Four of a Kind': '',
      'Full House': '',
      'Small Straggot': '',
      'Large Straggot': '',
      'Grahamzee': '',
      'Total Score': 0,
    }

class bjplayer:
  __slots__ = ('name', 'id', 'hands', 'insured', 'bankroll', 'wager', 'total_bet')
  def __init__(self, name, id):
    self.name = name
    self.id = id
    self.hands = [hand.hand()]
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
      if hand.status == 'doubled down':
        sum += self.wager*2
      else:
        sum += self.wager
    if self.insured == True:
      sum += self.wager*0.5
    self.total_bet = sum