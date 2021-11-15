import numpy as np

from agent import RandomAgent, DenseAgent
from gamestate import GameState, DECK


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
	play_choice_feats = np.zeros((num_turns, 60 * 2), dtype=np.float32)
	play_choice_feats[turn_idxs[::2], play_choices[:num_turns:2]] = p0_score
	play_choice_feats[turn_idxs[1::2], play_choices[1:num_turns:2]] = -p0_score
	draw_choice_feats = np.zeros((num_turns, 6), dtype=np.float32)
	draw_choice_feats[turn_idxs[::2], draw_choices[:num_turns:2]] = p0_score
	draw_choice_feats[turn_idxs[1::2], draw_choices[1:num_turns:2]] = -p0_score
	play_feats, draw_feats = play_feats[:num_turns], draw_feats[:num_turns]

	return play_feats, draw_feats, play_choice_feats, draw_choice_feats




if __name__ == "__main__":

	agent = RandomAgent()
	play_feats, draw_feats, play_choice_feats, draw_choice_feats = self_play(agent)
    
