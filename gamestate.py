from collections import defaultdict
from random import shuffle

import numpy as np


"""
Play/discard agent:

Input format:
    60x5 + 1. 60 cards each with a row of 5 for 
    	in hand                   (1, -1)
    	in my stacks              (1, -1)
    	in opponent stacks        (1, -1)
    	on top of discard pile    (1, -1)
    	elsewhere in discard pile (0, or +ve index)
    plus 1 unit for remaining cards in deck

Output format:
	60x2. 60 cards, one unit for play, one for discard
	estiamtes score delta in each output

Draw agent:

Input format:
	60x5 + 1 (plus last layer features from play/discard agent...?)

Output format:
	6 units, first five for discard piles, last for deck, estimate score delta for each
"""

RED = 0
GREEN = 1
WHITE = 2
BLUE = 3
YELLOW = 4
NUM_COLOURS = 5
DECK = 5


class Card:
	__slots__ = ['index', 'colour', 'value', 'label']
	def __init__(self, index):
		self.index = index
		self.colour, self.value = Card.idx_to_colour_and_value(index)
		self.label = 'X' if self.value == 0 else str(self.value)

	def __repr__(self):
		return f'({self.colour}, {self.label})'

	def idx_to_colour_and_value(idx):
		colour, r = divmod(idx, 12)
		val = 0 if r < 3 else r - 1
		return colour, val


class GameState:

	def __init__(self):
		pass

	def init_random_game(self):
		self.current_player = 0
		self.illegal_draw_pile = None  # If you just played to a pile
	
		self.deck = [Card(i) for i in range(60)]
		shuffle(self.deck)

		self.discard_piles = defaultdict(list)
		self.discard_top_features = np.ones(60, dtype=np.float32) * -1
		self.discard_covered_features = np.zeros(60, dtype=np.float32)
		self.stacks = (defaultdict(list), defaultdict(list))
		self.stack_features = [np.ones(60, dtype=np.float32) * -1 for _ in range(2)]

		self.hands = ([], [])
		self.hand_features = [np.ones(60, dtype=np.float32) * -1 for _ in range(2)]
		for hand, features in zip(self.hands, self.hand_features):
			for _ in range(8):
				card = self.deck.pop()
				hand.append(card)
				features[card.index] = 1


	def swap_player(self):
		self.stacks = (self.stacks[1], self.stacks[0])
		self.stack_features = (self.stack_features[1], self.stack_features[0])
		self.hands = (self.hands[1], self.hands[0])
		self.hand_features = (self.hand_features[1], self.hand_features[0])
		self.current_player = 1 - self.current_player;


	def do_play(self, card_index, is_discard):
		card = None
		for i, c in enumerate(self.hands[0]):
			if c.index == card_index:
				card = c
				self.hands[0][i] = None
				self.hand_features[0][card.index] = -1
				break
		else:
			raise ValueError("Tried to use card not in hand")

		if is_discard:
			pile = self.discard_piles[card.colour]
			self.illegal_draw_pile = card.colour
			for prev_discard in pile:
				self.discard_covered_features[prev_discard.index] += 1
			if pile:
				self.discard_top_features[pile[-1].index] = -1
			pile.append(card)
			self.discard_top_features[card.index] = 1

		else:
			self.stacks[0][card.colour].append(card)
			self.stack_features[0][card.index] = 1


	def do_draw(self, choice):
		assert(choice != self.illegal_draw_pile)
		self.illegal_draw_pile = None

		if choice == DECK:
			new_card = self.deck.pop()
		else:
			pile = self.discard_piles[choice]
			new_card = pile.pop()
			self.discard_top_features[new_card.index] = -1

			for prev_discard in pile:
				self.discard_covered_features[prev_discard.index] -= 1
			if pile:
				self.discard_top_features[pile[-1].index] = 1

		for i, c in enumerate(self.hands[0]):
			if c is None:
				self.hands[0][i] = new_card
				self.hand_features[0][new_card.index] = 1
				return new_card

		raise ValueError("No free slot in hand for new card")


	def _get_features(self):
		features = np.empty(60 * 5 + 1, dtype = np.float32)
		np.concatenate(
			(
				self.hand_features[0][:, None],
				self.stack_features[0][:, None],
				self.stack_features[1][:, None],
				self.discard_top_features[:, None],
				self.discard_covered_features[:, None],
			),
			axis=-1,
			out=features[:60*5].reshape((60, 5)),
		).flatten()
		features [-1] = len(self.deck)
		return features


	def _get_legal_play_mask(self):
		mask = np.zeros(shape=(60, 2), dtype=bool)

		for card in self.hands[0]:
			if card is None:
				continue
			stack = self.stacks[0][card.colour]
			mask[card.index, 0] = not stack or stack[-1].value <= card.value
			mask[card.index, 1] = 1  # can always discard from hand

		return mask


	def _get_legal_draw_mask(self):
		mask = np.ones(6, dtype=bool)

		if self.illegal_draw_pile is not None:
			mask[self.illegal_draw_pile] = False
		for colour in range(NUM_COLOURS):
			if len(self.discard_piles[colour]) == 0:
				mask[colour] = False
		return mask

	def get_play_features(self):
		return self._get_features(), self._get_legal_play_mask()

	def get_draw_features(self):
		return self._get_features(), self._get_legal_draw_mask()


	def is_finished(self):
		return len(self.deck) == 0


	def get_scores(self):
		scores = np.empty(shape=(2, 5), dtype=np.int32)
		for player in range(2):
			for colour in range(NUM_COLOURS):
				scores[player, colour] = score_stack(self.stacks[player][colour])
		return scores

	def get_score_delta(self):
		score = 0
		for colour in range(NUM_COLOURS):
			 score += score_stack(self.stacks[0][colour])
			 score -= score_stack(self.stacks[1][colour])
		return score


def score_stack(stack):
	if not stack:
		return 0
	score = sum(card.value for card in stack)
	score -= 20
	score *= 1 + sum(card.value == 0 for card in stack[:3])
	score += 20 * (len(stack) >= 8)
	return score


if __name__ == '__main__':
	game = GameState()
	game.new_game()