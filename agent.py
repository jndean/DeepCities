from collections import defaultdict
from random import random

import numpy as np
from tensorflow import keras

import gamestate


class Agent:

	def pick_play(self, state, mask):
		raise NotImplementedError()

	def pick_draw(self, state, mask):
		raise NotImplementedError()



class RandomAgent(Agent):
	PLAY_VS_DISCARD_WEIGHTING = 1

	def pick_play(self, state, mask):
		
		# Random choice, with playing normalised against discarding
		noise = np.random.random(mask.shape)
		num_playable_cards = np.sum(mask[:, 0])
		if num_playable_cards:
			noise[:, 0] = 1 - ((num_playable_cards / 8) * noise[:, 0] / self.PLAY_VS_DISCARD_WEIGHTING)
		choice = np.argmax(noise * mask)

		card, is_discard = divmod(choice, 2)
		return card, is_discard

	def pick_draw(self, state, mask):
		return np.argmax(np.random.random(mask.size) * mask)



class DenseAgent(Agent):

	def __init__(self, exploration_prob=0, existing_agent=None):
		self.exploration_prob = exploration_prob
		if exploration_prob != 0:
			self.random_agent = RandomAgent()

		if existing_agent is None:
			self.play_model = build_dense_play_network()
			self.draw_model =  build_dense_draw_network()
		else:
			self.play_model = existing_agent.play_model
			self.draw_model = existing_agent.draw_model

	def pick_play(self, state, mask):
		if random() < self.exploration_prob:
			return self.random_agent.pick_play(state, mask)

		results = self.play_model(state[None, :])
		choice = np.argmax(np.ma.array(results, mask=np.logical_not(mask)))
		card, is_discard = divmod(choice, 2)
		return card, is_discard

	def pick_draw(self, state, mask):
		if random() < self.exploration_prob:
			return self.random_agent.pick_draw(state, mask)

		results = self.draw_model(state[None, :])
		choice = np.argmax(np.ma.array(results, mask=np.logical_not(mask)))
		return choice

	def compile_models_for_training(self, loss):
		self.play_model.compile(loss=loss, optimizer='adam')
		self.draw_model.compile(loss=loss, optimizer='adam')


def build_dense_play_network():
	hidden_units = 1024
	hidden_layers = 3
	
	model = keras.models.Sequential()
	model.add(keras.Input(shape=(60 * 5 + 1)))
	
	for _ in range(hidden_layers):
		model.add(keras.layers.Dense(hidden_units, activation='relu'))  # , kernel_regularizer='l2')

	model.add(keras.layers.Dense(60 * 2, activation=None))
	return model


def build_dense_draw_network():
	hidden_units = 1024
	hidden_layers = 3
	
	model = keras.models.Sequential()
	model.add(keras.Input(shape=(60 * 5 + 1)))
	
	for _ in range(hidden_layers):
		model.add(keras.layers.Dense(hidden_units, activation='relu'))  # , kernel_regularizer='l2')

	model.add(keras.layers.Dense(6, activation=None))
	return model

tmp = [0]

class MinAgent(Agent):
	def __init__(self, play_handshakes=False, play_drawn_cards_weighting=1.0):
		self.play_handshakes = play_handshakes
		self.play_drawn_cards_weighting = play_drawn_cards_weighting
		self.random_agent = RandomAgent()

	def pick_play(self, state, mask):
		deck_size = state[-1]
		card_features = state[:-1].reshape((60, 5)) > 0
		played_multipliers = np.sum(card_features[:, 1].reshape(5, 12)[:, :3], axis=1) + 1
		empty_stacks = np.sum(card_features[:, 1].reshape(5, 12), axis=1) == 0

		in_hand = card_features[:, 0]
		unseen = np.sum(card_features, axis=-1) == 0
		draw_unseen_chance = deck_size / (2 * (deck_size + 8))
		play_unseen_chance = draw_unseen_chance * self.play_drawn_cards_weighting
		probabilities = in_hand * 1 + unseen * play_unseen_chance

		# Take card base values
		expected_worth = np.arange(60, dtype=np.float32).reshape((5, 12)) % 12 - 1
		expected_worth[:, :3] = 0
		# Multiply by probability of holding in hand at some point
		expected_worth *= probabilities.reshape((5, 12))

		# zero out cards that can't be played
		stack_maxes = [0] * 5
		for card_idx in np.where(card_features[:, 1])[0]:
			colour, value = gamestate.Card.idx_to_colour_and_value(card_idx)
			stack_maxes[colour] = max(stack_maxes[colour], value)
		for stack, stack_max in enumerate(stack_maxes):
			expected_worth[stack, :stack_max+2] = 0

		# apply handshake multipliers
		expected_worth *= played_multipliers[:, None]

		# Cost of playing a card (opportunity cost and new venture penalty)
		play_costs = expected_worth.copy()
		play_costs[:, 0] += 20 * empty_stacks
		play_costs = np.cumsum(play_costs, axis=1)
		play_costs = np.roll(play_costs, 1, axis=1)
		play_costs[:, 0] = play_costs[:, 1]  # 0
		play_costs = play_costs.flatten()

		# If we play a card, it will be the one minimising the opportunity cost
		# whlst still allowing best cards to be played at the end
		values_in_hand = expected_worth.flatten() * in_hand
		num_cards_worth_playing = np.count_nonzero(values_in_hand)
		remaining_turns = 1 + (deck_size - 1) // 2
		if remaining_turns < num_cards_worth_playing:
			cards = list(np.where(values_in_hand)[0])
			cards.sort(lambda x: values_in_hand[x], reverse=True)
			card_to_play = cards[remaining_turns - 1]

		else:
			card_to_play = np.argmin(play_costs * in_hand)
		play_card_cost = play_costs[card_to_play]
		


		""" 
		Play / discard decided by
			-summing top (deck_size//2) expected values to predict points to be score,
			  subtracting points scored by playing one fewer cards to find opportinuity cost of 
			  discarding
			- increase opportunity cost of discarding by max potential value of discarded card to 
			  opponent
			- compare against opportinuty cost of playing lowest cost card in hand
		"""



		tmp[0] += 1
		if tmp[0] > 1:
			print(empty_stacks)
			for i, (f, c, E) in enumerate(zip(card_features, play_costs.flatten(), expected_worth.flatten())):
				if E:
					print(f'{i % 12 - 1: 3d} {f} {E: 2.2f} {c: 2.2f}')
				else:
					print(f'{i % 12 - 1: 3d} {f} -')
				if i % 12 == 11:
					print('------------------------------------------------')

			print(f'{card_to_play=} {play_card_cost=}')
			quit()

		# Potential_values
		
		return self.random_agent.pick_play(state, mask)



	def pick_draw(self, state, mask):
		return self.random_agent.pick_draw(state, mask)


if __name__ == "__main__":
	agent = DenseAgent()

	import numpy as np
	x = np.random.random((64, 301))
	output = agent.model(x)
	print(output.shape)