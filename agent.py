
import numpy as np
from tensorflow import keras


class Agent:

	def pick_play(self, state):
		raise NotImplementedError()

	def pick_draw(self, state):
		raise NotImplementedError()



class RandomAgent(Agent):
	PLAY_VS_DISCARD_WEIGHTING = 1

	def pick_play(self, state):
		mask = state.get_legal_play_mask()
		
		# Random choice, with playing normalised against discarding
		noise = np.random.random(mask.shape)
		num_playable_cards = np.sum(mask[:, 0])
		print(mask.shape, num_playable_cards)
		if num_playable_cards:
			noise[:, 0] = 1 - ((num_playable_cards / 8) * noise[:, 0] / self.PLAY_VS_DISCARD_WEIGHTING)
		choice = np.argmax(noise * mask)

		card, is_discard = divmod(choice, 2)
		return card, is_discard

	def pick_draw(self, state):
		mask = state.get_legal_draw_mask()
		return np.argmax(np.random.random(mask.size) * mask)



class DenseAgent(Agent):

	def __init__(self):
		self.model = build_dense_network()

	def pick_play(self, state):
		raise NotImplementedError()

	def pick_draw(self, state):
		raise NotImplementedError()



def build_dense_network():
	hidden_units = 1024
	hidden_layers = 3
	
	model = keras.models.Sequential()
	model.add(keras.Input(shape=(60 * 5 + 1)))
	
	for _ in range(hidden_layers):
		model.add(keras.layers.Dense(hidden_units, activation='relu'))  # , kernel_regularizer='l2')

	model.add(keras.layers.Dense(60 * 2, activation=None))

	return model


if __name__ == "__main__":
	agent = DenseAgent()

	import numpy as np
	x = np.random.random((64, 301))
	output = agent.model(x)
	print(output.shape)