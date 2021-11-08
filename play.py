
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
			draw_choice = self.GUI.get_draw()

			print('Human:', card_choice, is_discard, draw_choice)

			self.state.do_play(card_choice, is_discard)
			drawn_card = self.state.do_draw(draw_choice)

			if draw_choice == DECK:
				self.GUI.draw_from_deck(drawn_card)

			# print('Pre', self.state.discard_piles, flush=True)

			self.state.swap_player()

			# Agent turn
			card_choice, is_discard = agent.pick_play(self.state)
			self.state.do_play(card_choice, is_discard)
			self.GUI.opponent_play(card_choice, is_discard)


			draw_choice = agent.pick_draw(self.state)
			print('Agent:', card_choice, is_discard, draw_choice)
			drawn_card = self.state.do_draw(draw_choice)
			self.GUI.opponent_draw(draw_choice, drawn_card)

			self.state.swap_player()


if __name__ == "__main__":

	game = HumanGame()
	game.run()

    
