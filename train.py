import numpy as np
import tensorflow.keras.backend as K
from tqdm import tqdm

from agent import RandomAgent, DenseAgent, MinAgent
from gamestate import GameState, DECK

SENTINEL = 9999


def play_match(A, B, max_turns=150):
	state = GameState()
	state.init_random_game()

	for turn in range(0, max_turns, 2):
		input_feats, output_mask = state.get_play_features()
		card_choice, is_discard = A.pick_play(input_feats, output_mask)
		state.do_play(card_choice, is_discard)
		input_feats, output_mask = state.get_draw_features()
		draw_choice = A.pick_draw(input_feats, output_mask)
		drawn_card = state.do_draw(draw_choice)

		if state.is_finished():
			break
		state.swap_player()

		input_feats, output_mask = state.get_play_features()
		card_choice, is_discard = B.pick_play(input_feats, output_mask)
		state.do_play(card_choice, is_discard)
		input_feats, output_mask = state.get_draw_features()
		draw_choice = B.pick_draw(input_feats, output_mask)
		drawn_card = state.do_draw(draw_choice)

		state.swap_player()
		if state.is_finished():
			break

	return state.get_score_delta()



def self_play_match(agent, exploration_factor=0, max_turns=150):

	play_feats = np.empty((max_turns, 60 * 5 + 1), dtype=np.float32)
	draw_feats = np.empty((max_turns, 60 * 5 + 1), dtype=np.float32)
	play_choices = np.empty(max_turns, dtype=int)
	draw_choices = np.empty(max_turns, dtype=int)

	state = GameState()
	state.init_random_game()

	for turn in range(max_turns):
		if state.is_finished():  # Check first, so that 'turn' has correct value after loop
			break

		input_feats, output_mask = state.get_play_features()
		card_choice, is_discard = agent.pick_play(input_feats, output_mask)
		state.do_play(card_choice, is_discard)
		play_feats[turn] = input_feats
		play_choices[turn] = 2 * card_choice + is_discard

		input_feats, output_mask = state.get_draw_features()
		draw_choice = agent.pick_draw(input_feats, output_mask)
		drawn_card = state.do_draw(draw_choice)
		draw_feats[turn] = input_feats
		draw_choices[turn] = draw_choice

		state.swap_player()

	num_turns = turn


	p0_score = state.get_score_delta()
	if state.current_player:
		p0_score *= -1

	turn_idxs = np.arange(num_turns)
	play_choice_feats = np.full((num_turns, 60 * 2), SENTINEL, dtype=np.float32)
	play_choice_feats[turn_idxs[::2], play_choices[:num_turns:2]] = p0_score
	play_choice_feats[turn_idxs[1::2], play_choices[1:num_turns:2]] = -p0_score
	draw_choice_feats = np.full((num_turns, 6), SENTINEL, dtype=np.float32)
	draw_choice_feats[turn_idxs[::2], draw_choices[:num_turns:2]] = p0_score
	draw_choice_feats[turn_idxs[1::2], draw_choices[1:num_turns:2]] = -p0_score
	play_feats, draw_feats = play_feats[:num_turns], draw_feats[:num_turns]

	return play_feats, draw_feats, play_choice_feats, draw_choice_feats


def dual_shuffle(a, b):
	assert(a.shape[0] == b.shape[0])
	p = np.random.permutation(a.shape[0])
	return a[p], b[p]

def squared_error_masked(y_true, y_pred):
    """ Squared error of elements where y_true is not 0 """
    err = y_pred - y_true  # K.cast(y_true, y_pred.dtype)
    return K.sum(K.square(err) * K.cast(K.not_equal(y_true, SENTINEL), y_pred.dtype), axis=-1)


def train():

	random_agent = RandomAgent()
	training_agent = DenseAgent(exploration_prob=0.15)
	training_agent.compile_models_for_training(loss=squared_error_masked)
	eval_agent = DenseAgent(exploration_prob=0, existing_agent=training_agent)

	for i in range(20):
		
		all_play_X, all_draw_X, all_play_Y, all_draw_Y = [], [], [], []	
		for match in tqdm(range(100)):
			play_X, draw_X, play_Y, draw_Y = self_play_match(random_agent)
			all_play_X.append(play_X)
			all_play_Y.append(play_Y)
			all_draw_X.append(draw_X)
			all_draw_Y.append(draw_Y)

		play_X = np.concatenate(all_play_X, axis=0)
		play_Y = np.concatenate(all_play_Y, axis=0)
		draw_X = np.concatenate(all_draw_X, axis=0)
		draw_Y = np.concatenate(all_draw_Y, axis=0)

		play_X, play_Y = dual_shuffle(play_X, play_Y)
		draw_X, draw_Y = dual_shuffle(draw_X, draw_Y)
		
		training_agent.play_model.fit(
			x=play_X,
			y=play_Y,
			epochs=3,
		)
		training_agent.draw_model.fit(
			x=draw_X,
			y=draw_Y,
			epochs=3,
		)

		scores = [play_match(eval_agent, random_agent) for _ in tqdm(range(10))]
		print(f'Eval: avg={sum(scores)/len(scores)}, {scores=}')
    


if __name__ == "__main__":
	#train()

	"""
	agent = RandomAgent()
	all_play_X, all_draw_X, all_play_Y, all_draw_Y = [], [], [], []	
	for match in tqdm(range(100)):
		play_X, draw_X, play_Y, draw_Y = self_play_match(agent)
		all_play_X.append(play_X)
		all_play_Y.append(play_Y)
		all_draw_X.append(draw_X)
		all_draw_Y.append(draw_Y)

	play_X = np.concatenate(all_play_X, axis=0)
	play_Y = np.concatenate(all_play_Y, axis=0)
	draw_X = np.concatenate(all_draw_X, axis=0)
	draw_Y = np.concatenate(all_draw_Y, axis=0)

	play_X, play_Y = dual_shuffle(play_X, play_Y)
	draw_X, draw_Y = dual_shuffle(draw_X, draw_Y)


	A = play_Y[0]
	i = np.argmin(A)
	B = np.zeros_like(A)
	B[i] = A[i]
	B[i + 1] = 999
	print(B)
	loss = squared_error_masked(A, B)
	print(loss)
	"""

	randy = RandomAgent()
	minny = MinAgent(play_handshakes=False)


	scores = [play_match(minny, randy) for _ in tqdm(range(1000))]
	print(f'Eval: avg={sum(scores)/len(scores)}')