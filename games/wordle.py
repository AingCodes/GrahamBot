import random
import datetime
import asyncio

class wordlegame:
  def __init__(self):
    self.words = tuple(line.strip() for line in open('words.txt'))
    self.word = self.words[datetime.datetime.now().day**2 * datetime.datetime.now().month + datetime.datetime.now().year]
    asyncio.create_task(self.reset_word())
    
  
  async def reset_word(self):
    await asyncio.sleep(time_until_end_of_day())
    self.word = self.words[datetime.datetime.now().day**2 * datetime.datetime.now().month + datetime.datetime.now().year]
    asyncio.create_task(self.reset_word())


def time_until_end_of_day(dt=None):
  if dt is None:
      dt = datetime.datetime.now()
  return ((24 - dt.hour - 1) * 60 * 60) + ((60 - dt.minute - 1) * 60) + (60 - dt.second)

