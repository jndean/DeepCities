
from gamestate import GameState, Colour
from tableGUI import TableGUI




class HumanGame:

	def __init__(self, virtual_game=True):
		self.virtual_game = virtual_game  # For later features
		
		self.state = GameState()
		self.state.init_random_game()

		self.GUI = TableGUI()
		self.GUI.set_state(self.state.hands[0])


	def run(self):
		while 1:
			hand_choice, is_discard, draw_choice = self.GUI.get_turn()

			print(hand_choice, is_discard, draw_choice)
			
			drawn_card = self.state.do_turn(hand_choice, is_discard, draw_choice)
			if draw_choice is None:
				self.GUI.draw_from_deck(drawn_card)
				

if __name__ == "__main__":

	game = HumanGame()
	game.run()

    
