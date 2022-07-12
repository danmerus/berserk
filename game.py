import os
import board
import berserk_gui
import numpy.random as rng
from game_properties import GameStates
from kivy.clock import Clock
from kivy import Config
from kivy.core.window import Window
# Config.set('graphics', 'fullscreen', 'auto')

class Game:

    def __init__(self, cards_on_board1, cards_on_board2):
        """"
        cards_on_board is a cards list
        """
        self.board = board.Board()
        self.input_cards1 = cards_on_board1
        self.input_cards2 = cards_on_board2
        self.populate_cards()
        self.curr_game_state = GameStates.VSKRYTIE
        self.current_active_player = 1
        self.instant_actions_present = False

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
            1: [(1, 0)],
            2: [(2, 1), (1, 0)],
            3: [(2, 0)],
            4: [(3, 1), (2, 0)],
            5: [(3, 0)],
            -1: [(1, 0)],
            -2: [(0, 0)],
            -3: [(0, 1)],
            -4: [(1, 2), (0, 1)],
            -5: [(0, 2)],
        }
        score = x1 - x2
        if score < -5:
            res = [(0, 2)]
        elif score > 5:
            res = [(3, 0)]
        elif score == 0 and x1 <= 4:
            res = [(1, 0)]
        elif score == 0 and x1 > 4:
            res = [(0, 1)]
        else:
            res = res_dict[score]
        return res, x1, x2  # (attack, defence) roll1  roll2

    def next_game_state(self, instance):
        if self.curr_game_state == GameStates.END_PHASE:
            self.switch_curr_player()
        self.curr_game_state = self.curr_game_state.next()

    def switch_curr_player(self):
        if self.current_active_player == 1:
            self.current_active_player = 2
        else:
            self.current_active_player = 1

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


    cards1 = [PovelitelMolniy_1(player=1, location=12), Draks_1(player=1, location=13), Draks_1(player=1, location=2),
              Draks_1(player=1, location=3), Draks_1(player=1, location=4), Draks_1(player=1, location=5)]
    cards2 = [PovelitelMolniy_1(player=2, location=14), Draks_1(player=2, location=22), Draks_1(player=2, location=25)]
    game = Game(cards1, cards2)
    game.start()
    ######## GUI #######
    game.gui = berserk_gui.BerserkApp(game)
    game.gui.run()

    #game.on_start('qwe')
    #game.update_board_gui()
