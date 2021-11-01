from collections import defaultdict
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

		self.hands = tuple([self.deck.pop() for _ in range(8)] for _ in range(2))
		self.current_player = 0

		self.discard_piles = defaultdict(list)
		self.stacks = (defaultdict(list), defaultdict(list))


	def swap_player(self):
		self.stacks = (self.stacks[1], self.stacks[0])
		self.hands = (self.hands[1], self.hands[0])
		self.current_player = int(not self.current_player)


	def do_turn(self, hand_choice, is_discard, draw_choice):
		card = self.hands[0][hand_choice]
		card_dst = self.discard_piles[card.colour] if is_discard else self.stacks[0][card.colour]
		card_dst.append(card)

		if draw_choice is None:
			new_card = self.deck.pop()
		else:
			new_card = self.discard_piles[draw_choice].pop()
		
		self.hands[0][hand_choice] = new_card

		return new_card



if __name__ == '__main__':
	game = GameState()
	game.new_game()