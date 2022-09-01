import os
import board
import berserk_gui
import numpy.random as rng

import network
from kivy.clock import Clock
from cards.card import *


# Config.set('graphics', 'fullscreen', 'auto')

class Game:

    def __init__(self, turn_duration=10, stack_duration=10, server_ip=None, server_port=None):
        """"
        cards_on_board is a cards list
        """
        self.board = board.Board(self)
        self.turn_duration = turn_duration
        self.stack_duration = stack_duration
        self.curr_game_state = GameStates.VSKRYTIE
        self.turn_count = 1
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
        self.mode = 'offline'
        self.server_ip = server_ip
        self.server_port = server_port
        self.curr_id_on_bord = 0

    def set_cards(self, cards_on_board1, cards_on_board2, gui):
        new_cards = []
        for block in [cards_on_board1, cards_on_board2]:
            for card in block:
                nc = card.__class__(card.player, card.loc, gui)
                nc.id_on_board = self.curr_id_on_bord
                self.curr_id_on_bord += 1
                for i, a in enumerate(nc.abilities):
                    a.index = i
                new_cards.append(nc)
        self.populate_cards(new_cards)

    def populate_cards(self, new_cards):
        self.board.populate_board(new_cards)

    def player_passed(self, *args):
        if self.in_stack:
            if self.curr_priority == 1:
                self.passed_1 = True
            else:
                self.passed_2 = True
            self.switch_priority()

    def get_roll_result(self,  count):
        res = []
        if self.mode == 'online':
            res = network.get_rolls(self.server_ip, self.server_port, count)
        else:
            for _ in range(count):
                res.append(rng.randint(1, 7))
        return res

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

    # def next_game_state(self, *args):
    #     if self.stack:
    #         self.gui.process_stack()
    #     self.passed_1 = False
    #     self.passed_2 = False
    #     self.passed_once = False
    #     next_state = self.curr_game_state.next_after_start()
    #     if next_state != GameStates.MAIN_PHASE:
    #         self.gui.disable_all_non_instant_actions()
    #     if next_state == GameStates.MAIN_PHASE:
    #         cb = self.board.get_all_cards_with_callback(Condition.START_MAIN_PHASE)
    #         for c, a in cb:
    #             if c.player == self.current_active_player and a.check():
    #                 if self.mode != 'online' or (self.mode == 'online' and c.player == self.gui.pow):
    #                     self.gui.start_stack_action(a, c, c, 0, 0)
    #                     # self.gui.check_all_passed()
    #                     # if self.backend.mode == 'online' and self.pow != self.backend.current_active_player:
    #                     #     self.eot_button.disabled = True
    #                     # Clock.schedule_once(self.gui.process_stack)
    #     if self.is_state_active(next_state) or next_state == GameStates.MAIN_PHASE:
    #         self.curr_game_state = next_state
    #         self.on_step_start()
    #         self.gui.check_all_passed(None)
    #     else:
    #         self.curr_game_state = next_state
    #         self.on_step_start()
    #         self.next_game_state()


    # def switch_priority(self, *args):
    #     if self.curr_priority == 1:
    #         self.curr_priority = 2
    #     else:
    #         self.curr_priority = 1
    #     self.gui.buttons_on_priority_switch()
    #
    # def switch_curr_active_player(self):
    #     if self.current_active_player == 1:
    #         self.current_active_player = 2
    #         self.curr_priority = 2
    #     else:
    #         self.current_active_player = 1
    #         self.curr_priority = 1
    #     if self.gui.pow == self.current_active_player and self.mode == 'online':
    #         self.gui.eot_button.disabled = False
    #     elif self.gui.pow != self.current_active_player and self.mode == 'online':
    #         self.gui.eot_button.disabled = True
    #     self.on_start_new_turn()

    # def on_start_new_turn(self):
    #     self.turn_count += 1
    #     for card in self.board.get_all_cards():
    #         if card.player != self.current_active_player and CardEffect.NETTED in card.active_status:
    #             card.active_status.remove(CardEffect.NETTED)
    #             if not card.tapped:
    #                 card.actions_left = 1
    #             self.gui.add_defence_signs(card)
    #         if self.turn_count > 1 and card.hidden:
    #             self.gui.unhide(card)
    #     #game.gui.on_new_turn()
    #
    # def on_start_opening_phase(self):
    #     self.gui.on_new_turn()


    def is_state_active(self, state):
        ret = False
        for card in self.board.get_all_cards():
            for ability in card.abilities:
                if not card.tapped and not isinstance(ability, TriggerBasedCardAction) and state in ability.state_of_action:
                    ret = True
        return ret


    def get_displayable_actions_for_gui(self, card):
        return [(x.txt, x.index, 0) for x in card.abilities if (not hasattr(x, 'display')) or x.display]

    def card_to_state(self, card):
        res = {}
        res['id'] = card.id_on_board
        res['name'] = card.name
        if hasattr(card, 'life'):
            res['life'] = card.life
        if hasattr(card, 'curr_life'):
            res['curr_life'] = card.curr_life
        if hasattr(card, 'move'):
            res['move'] = card.move
        if hasattr(card, 'curr_move'):
            res['curr_move'] = card.curr_move
        if hasattr(card, 'curr_fishka'):
            res['curr_fishka'] = card.curr_fishka
        if hasattr(card, 'red_fishka'):  # TODO для перераспределения
            res['red_fishka'] = card.curr_fishka
        if hasattr(card, 'pic'):
            res['pic'] = card.pic
        if hasattr(card, 'loc'):
            res['loc'] = card.loc
        if hasattr(card, 'player'):
            res['player'] = card.player
        if hasattr(card, 'zone'):
            res['zone'] = card.zone
        if hasattr(card, 'defences') or hasattr(card, 'active_status'):
            res['defences'] = card.defences
            res['active_status'] = card.active_status
        return res

    def form_state_obj(self):
        """what is displayed now over state:
        position, picture, life(curr/max),
        movement(curr/max), fishka/red fishka, buttons,
        red arrows, timer restart, def signs (zom)!"""
        state = {}
        all_cards = self.board.get_all_cards() + self.board.get_grave()
        cards = {}
        for card in all_cards:
            c_dict = self.card_to_state(card)
            cards[card.id_on_board] = c_dict
        markers = {}  # клетка на поле или существо в доп зоне ? отправляем только одному игроку
        state['cards'] = cards
        state['markers'] = markers
        state['timer'] = {'restart': False, 'duration': 30}
        return state

    def card_clicked(self, card):
        """ send back ability list with active/passive status, move tile numbers"""
        if self.mode == 'online':
            pass
        else:
            card = self.board.get_card_by_id(card)
            ability_names = self.get_displayable_actions_for_gui(card)
            moves = self.board.get_available_moves(card)
        self.selected_card = card
        self.marks_bind = DefaultMovementAction()
        return ability_names, moves

    def ability_clicked(self, ability_id):
        ab = self.selected_card.get_ability_by_id(ability_id)
        print('ability_clicked', ab)

    def mark_clicked(self, mark, *args):
        print('clicked: ', mark, self.selected_card, self.marks_bind)

    def send_state(self):
        state = self.form_state_obj()
        if self.mode == 'online':
            pass
        else:
            self.gui.on_state_recieved(state)

    def on_reveal(self, cards):
        for card in cards:
            if card.type_ == CreatureType.FLYER or card.type_ == CreatureType.LAND:
                self.board.game_board[card.loc] = 0

    def start(self, *args):
        if self.mode == 'online':
            pass
        else:
            self.gui.run()

    def on_load(self, client):
        if self.mode == 'online':
            pass
        else:
            self.send_state()
            Clock.schedule_once(lambda x: self.gui.start_timer(self.turn_duration, True), 0.1) # TODO add text for timer
            # if not self.is_state_active(GameStates.VSKRYTIE):
            #     self.next_game_state()


if __name__ == '__main__':
    # hack to import all cards
    filedir = 'cards/set_1'
    modules = [f[:-3] for f in os.listdir(filedir) if
               os.path.isfile(os.path.join(filedir, f)) and f.endswith('.py') and f != '__init__.py']
    imports = [f"from cards.set_1 import {module}\nfrom cards.set_1.{module} import *" for module in sorted(modules)]
    for imp in imports:
        exec(imp)

    WINDOW_SIZE = (960, 540)  # (1920, 1080) #
    STACK_DURATION = 5
    TURN_DURATION = 5
    game = Game(TURN_DURATION, STACK_DURATION)
    # game.mode = 'online'
    gui = berserk_gui.BerserkApp(WINDOW_SIZE, pow=1, backend=game, mode='offline')
    game.gui = gui
    cards1 = [Elfiyskiy_voin_1(player=1, location=27, gui=gui),
               Lovets_dush_1(player=1, location=13, gui=gui),
              #  Lovets_dush_1(player=1, location=0, gui=gui),
              # Necromant_1(player=1, location=21, gui=gui),
               Ar_gull_1(player=1, location=12, gui=gui),
               Cobold_1(player=1, location=14),
               Otshelnik_1(player=1, location=4, gui=gui),
               Gnom_basaarg_1(player=1, location=15, gui=gui),
               Draks_1(player=1, location=5, gui=gui)
        ]
    cards2 = [
        Bjorn_1(player=2, location=13),
                Ovrajnii_gnom_1(player=2, location=22, gui=gui),
               Necromant_1(player=2, location=19, gui=gui),
             # Lovets_dush_1(player=2, location=12, gui=gui),
               Ar_gull_1(player=2, location=16, gui=gui),
             #  Voin_hrama_1(player=2, location=22, gui=gui), Draks_1(player=2, location=25, gui=gui)
            ]
    game.set_cards(cards1, cards2, gui)
    print(game.form_state_obj())
    game.start()

