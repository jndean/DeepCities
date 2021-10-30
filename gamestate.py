from enum import Enum
from random import shuffle


class Colour(Enum):
	RED = 1
	GREEN = 2
	WHITE = 3
	BLUE = 4
	YELLOW = 5

class Card:
	__slots__ = ['colour', 'value']
	def __init__(self, colour, value):
		self.colour, self.value = colour, value

	def __repr__(self):
		return f'({self.colour}, {self.value})'


class GameState:

	def __init__(self):
		pass

	def init_random_game(self):
		self.deck = []
		for colour in Colour:
			for value in range(2, 11):
				self.deck.append(Card(colour, value))
			for _ in range(3):
				self.deck.append(Card(colour, 0))
		shuffle(self.deck)

		self.hands = [[self.deck.pop() for _ in range(8)] for _ in range(2)]
		self.current_player = 0

if __name__ == '__main__':
	game = GameState()
	game.new_game()