class hand:
  __slots__ = ('cards', 'value', 'status')

  def __init__(self):
    self.cards = []
    self.status = 'active'

  def card_value(self, card_number):
    rank = self.cards[card_number][:-2]
    if rank == 'A':
      value = 11
    elif rank in ['J', 'Q', 'K']:
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