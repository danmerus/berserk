import os
import board
import berserk_gui
import numpy.random as rng
from game_properties import GameStates
from kivy.clock import Clock
from cards.card import *
import placement


# Config.set('graphics', 'fullscreen', 'auto')

class Game:

    def __init__(self, ):
        """"
        cards_on_board is a cards list
        """
        self.board = board.Board()
        self.curr_game_state = GameStates.VSKRYTIE
        self.turn = 1
        self.current_active_player = 1
        self.curr_priority = 1
        self.in_stack = False
        self.stack = []
        self.passed_1 = False
        self.passed_2 = False
        self.passed_once = False
        self.cards_on_board1 = []
        self.cards_on_board2 = []

    def set_cards(self, cards_on_board1, cards_on_board2, gui):
        for card in cards_on_board1:
            card.gui = gui
        for card in cards_on_board2:
            card.gui = gui
        self.input_cards1 = cards_on_board1
        self.input_cards2 = cards_on_board2
        self.populate_cards()

    def populate_cards(self):
        self.board.populate_board(self.input_cards1)
        self.board.populate_board(self.input_cards2)

    def player_passed(self, *args):
        if self.in_stack:
            if self.curr_priority == 1:
                self.passed_1 = True
            else:
                self.passed_2 = True
            self.switch_priority()

    def get_roll_result(self, mod_1=0):
        x1 = rng.randint(1, 7) + mod_1
        return x1

    def get_fight_result(self, roll1, roll2):
        """
        returns fight simulation, accounts for blessings/curses etc.
        roll1 - attacker,
        roll2 - defender
        """
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
        score = roll1 - roll2
        if score < -5:
            res = [(0, 2)]
        elif score > 5:
            res = [(3, 0)]
        elif score == 0 and roll1 <= 4:
            res = [(1, 0)]
        elif score == 0 and roll1 > 4:
            res = [(0, 1)]
        else:
            res = res_dict[score]
        return res  # (attack, defence) list

    def on_step_start(self):
        if self.curr_game_state == GameStates.END_PHASE:
            self.switch_curr_active_player()
        if self.curr_game_state == GameStates.OPENING_PHASE:
            self.on_start_opening_phase()

    def next_game_state(self, *args):
        self.passed_1 = False
        self.passed_2 = False
        self.passed_once = False
        next_state = self.curr_game_state.next_after_start()
        if next_state != GameStates.MAIN_PHASE:
            gui.disable_all_non_instant_actions()
        if next_state == GameStates.MAIN_PHASE:
            cb = self.board.get_all_cards_with_callback(Condition.START_MAIN_PHASE)
            for c, a in cb:
                if c.player == self.current_active_player and a.check():
                    self.stack.append((a, c, c, 0))
                    Clock.schedule_once(gui.process_stack)
        if self.is_state_active(next_state) or next_state == GameStates.MAIN_PHASE:
            self.curr_game_state = next_state
            self.on_step_start()
            game.gui.check_all_passed(None)
        else:
            self.curr_game_state = next_state
            self.on_step_start()
            self.next_game_state()

    def switch_priority(self, *args):
        if self.curr_priority == 1:
            self.curr_priority = 2
        else:
            self.curr_priority = 1
        gui.buttons_on_priority_switch()

    def switch_curr_active_player(self):
        if self.current_active_player == 1:
            self.current_active_player = 2
            self.curr_priority = 2
        else:
            self.current_active_player = 1
            self.curr_priority = 1
        self.on_start_new_turn()

    def on_start_new_turn(self):
        self.turn += 1
        for card in self.board.get_all_cards():
            if card.player != self.current_active_player and CardEffect.NETTED in card.active_status:
                card.active_status.remove(CardEffect.NETTED)
                gui.add_defence_signs(card)
        #game.gui.on_new_turn()

    def on_start_opening_phase(self):
        game.gui.on_new_turn()


    def is_state_active(self, state):
        ret = False
        for card in self.board.get_all_cards():
            for ability in card.abilities:
                if not isinstance(ability, TriggerBasedCardAction) and state in ability.state_of_action:
                    ret = True
        return ret

    def start(self, *args):
        if not self.is_state_active(GameStates.VSKRYTIE):
            self.next_game_state()



if __name__ == '__main__':
    # hack to import all cards
    filedir = 'cards/set_1'
    modules = [f[:-3] for f in os.listdir(filedir) if
               os.path.isfile(os.path.join(filedir, f)) and f.endswith('.py') and f != '__init__.py']
    imports = [f"from cards.set_1 import {module}\nfrom cards.set_1.{module} import *" for module in sorted(modules)]
    for imp in imports:
        exec(imp)

    WINDOW_SIZE = (960, 540) # (1920, 1080) #
    STACK_DURATION = 10
    TURN_DURATION = 10
    game = Game()
    # cards1 = [Lovets_dush_1(), Cobold_1(), Draks_1(), Lovets_dush_1(), Voin_hrama_1(), Draks_1(),]
    #           # Lovets_dush_1(), PovelitelMolniy_1(), Draks_1(),Lovets_dush_1(), PovelitelMolniy_1(), Draks_1(),
    #           # Lovets_dush_1(), PovelitelMolniy_1(), Draks_1()]
    # cards2 = [Lovets_dush_1(), PovelitelMolniy_1(), Draks_1(), Lovets_dush_1(), PovelitelMolniy_1(), Draks_1(),]
    #          # Lovets_dush_1(), PovelitelMolniy_1(), Draks_1(), Lovets_dush_1(), PovelitelMolniy_1(), Draks_1(),
    #         #  Lovets_dush_1(), PovelitelMolniy_1(), Draks_1()]
    # selection = placement.SelectionApp(game, WINDOW_SIZE, cards1, 1)
    # selection.run()
    # selection = placement.SelectionApp(game, WINDOW_SIZE, cards2, 2)
    # selection.run()

    gui = berserk_gui.BerserkApp(game, WINDOW_SIZE, STACK_DURATION, TURN_DURATION)
    game.gui = gui
    # game.set_cards(game.cards_on_board1, game.cards_on_board2, gui)
    cards1 = [Lovets_dush_1(player=1, location=18, gui=gui),
              Otshelnik_1(player=1, location=13, gui=gui),
              Lovets_dush_1(player=1, location=0, gui=gui),
              Bjorn_1(player=1, location=21, gui=gui),
              Elfiyskiy_voin_1(player=1, location=27, gui=gui),
              Gnom_basaarg_1(player=1, location=2, gui=gui),
              Pauk_peresmeshnik_1(player=1, location=4, gui=gui),
              Necromant_1(player=1, location=3, gui=gui), Draks_1(player=1, location=5, gui=gui)]
    cards2 = [
        PovelitelMolniy_1(player=2, location=14),
             Bjorn_1(player=2, location=20, gui=gui),Bjorn_1(player=2, location=19, gui=gui),
              # Lovets_dush_1(player=2, location=12, gui=gui),
              Ar_gull_1(player=2, location=15, gui=gui),
              Voin_hrama_1(player=2, location=22, gui=gui), Draks_1(player=2, location=25, gui=gui)]
    game.set_cards(cards1, cards2, gui)

    game.gui.run()

