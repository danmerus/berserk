import os
import board
import berserk_gui
import numpy.random as rng
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

    def get_fight_result(self, mod_1=0, mod_2=0):
        """
        returns fight simulation, accounts for blessings/curses etc.
        """
        x1 = rng.randint(1, 7) + mod_1 # attacker
        x2 = rng.randint(1, 7) + mod_2 # defender
        res_dict = {
            1: (1, 0),
            2: (2, 1),
            3: (2, 0),
            4: (3, 1),
            5: (3, 0),
            -1: (1, 0),
            -2: (0, 0),
            -3: (0, 1),
            -4: (1, 2),
            -5: (0, 2),
        }
        score = x1 - x2
        if score < -5:
            res = (0, 2)
        elif score > 5:
            res = (3, 0)
        elif score == 0 and x1 <= 4:
            res = (1, 0)
        elif score == 0 and x1 > 4:
            res = (0, 1)
        else:
            res = res_dict[score]
        return res, x1, x2  # (attack, defence) roll1  roll2



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
