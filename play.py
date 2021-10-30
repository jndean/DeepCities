
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
			mv = self.GUI.get_play()
			print(mv)
			mv = self.GUI.get_draw()
			print(mv)

if __name__ == "__main__":

	game = HumanGame()
	game.run()

    
