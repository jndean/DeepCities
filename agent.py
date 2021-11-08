import numpy as np


class Agent:

	def pick_play(self, state):
		raise NotImplementedError()

	def pick_draw(self, state):
		raise NotImplementedError()

	def _probs_into_move(self, probs):
		pass



class RandomAgent(Agent):
	PLAY_VS_DISCARD_WEIGHTING = 2

	def pick_play(self, state):
		mask = state.get_legal_play_mask()
		
		# Random choice, with playing twice as likely as discarding
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