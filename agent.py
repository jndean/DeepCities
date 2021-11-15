from random import random

import numpy as np
from tensorflow import keras


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

	def __init__(self, exploration_prob=0):
		self.exploration_prob = exploration_prob
		self.play_model = build_dense_play_network()
		self.draw_model =  build_dense_draw_network()
		self.random_agent = RandomAgent()

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


if __name__ == "__main__":
	agent = DenseAgent()

	import numpy as np
	x = np.random.random((64, 301))
	output = agent.model(x)
	print(output.shape)