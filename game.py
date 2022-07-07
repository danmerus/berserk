import os
import board
import berserk_gui
from cards import c1
from kivy.clock import Clock

class Game:

    def __init__(self, cards_on_board1, cards_on_board2):
        """"
        cards_on_board is a cards list
        """
        self.board = board.Board()
        self.input_cards1 = cards_on_board1
        self.input_cards2 = cards_on_board2
        self.populate_cards()

    def populate_cards(self):
        self.board.populate_board(self.input_cards1)
        self.board.populate_board(self.input_cards2)


    def start(self):
        pass


if __name__ == '__main__':
    # hack to import all cards
    filedir = 'cards'
    modules = [f[:-3] for f in os.listdir(filedir) if
               os.path.isfile(os.path.join(filedir, f)) and f.endswith('.py') and f != '__init__.py']
    imports = [f"from cards import {module}\nfrom cards.{module} import *" for module in sorted(modules)]
    for imp in imports:
        exec(imp)

    cards1 = [C1(player=1, location=12)]
    cards2 = [C1(player=2, location=14)]
    game = Game(cards1, cards2)
    game.start()
    ######## GUI #######
    game.gui = berserk_gui.BerserkApp(game)
    game.gui.run()

    #game.on_start('qwe')
    #game.update_board_gui()
