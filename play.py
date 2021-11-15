
from agent import RandomAgent
from gamestate import GameState, DECK
from tableGUI import TableGUI




class HumanGame:

	def __init__(self, agent):
		self.agent = agent
		
		self.state = GameState()
		self.state.init_random_game()

		self.GUI = TableGUI()
		self.GUI.set_state(self.state.hands[0])


	def run(self):

		while 1:

			# Human turn
			card_choice, is_discard = self.GUI.get_play()
			self.state.do_play(card_choice, is_discard)
			self.GUI.set_scores(*self.state.get_scores())
			draw_choice = self.GUI.get_draw()
			drawn_card = self.state.do_draw(draw_choice)
			self.GUI.set_scores(*self.state.get_scores())
			if draw_choice == DECK:
				self.GUI.draw_from_deck(drawn_card)

			print('Human:', card_choice, is_discard, draw_choice)

			if self.state.is_finished():
				break

			self.state.swap_player()

			# Agent turn
			state_features = self.state.get_play_features()
			card_choice, is_discard = self.agent.pick_play(*state_features)
			self.state.do_play(card_choice, is_discard)
			self.GUI.opponent_play(card_choice, is_discard)


			state_features = self.state.get_draw_features()
			draw_choice = self.agent.pick_draw(*state_features)
			print('Agent:', card_choice, is_discard, draw_choice)
			drawn_card = self.state.do_draw(draw_choice)
			self.GUI.opponent_draw(draw_choice, drawn_card)

			opponent_scores, player_scores = self.state.get_scores()
			self.GUI.set_scores(player_scores, opponent_scores)
			if self.state.is_finished():
				break

			self.state.swap_player()




if __name__ == "__main__":

	agent = RandomAgent()
	game = HumanGame(agent)
	game.run()

    
