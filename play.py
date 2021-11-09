
from agent import RandomAgent
from gamestate import GameState, DECK
from tableGUI import TableGUI




class HumanGame:

	def __init__(self, virtual_game=True):
		self.virtual_game = virtual_game  # For later features
		
		self.state = GameState()
		self.state.init_random_game()

		self.GUI = TableGUI()
		self.GUI.set_state(self.state.hands[0])


	def run(self):

		agent = RandomAgent()

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
			card_choice, is_discard = agent.pick_play(self.state)
			self.state.do_play(card_choice, is_discard)
			self.GUI.opponent_play(card_choice, is_discard)

			draw_choice = agent.pick_draw(self.state)
			print('Agent:', card_choice, is_discard, draw_choice)
			drawn_card = self.state.do_draw(draw_choice)
			self.GUI.opponent_draw(draw_choice, drawn_card)

			opponent_scores, player_scores = self.state.get_scores()
			self.GUI.set_scores(player_scores, opponent_scores)
			if self.state.is_finished():
				break

			self.state.swap_player()




if __name__ == "__main__":

	game = HumanGame()
	game.run()

    
