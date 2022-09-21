import os
import board
import numpy.random as rng

import network
import game_properties
from game_properties import GameStates
from kivy.clock import Clock
# from cards.card import *
from copy import copy
from cards.card_properties import *
from cards.card import *

# Config.set('graphics', 'fullscreen', 'auto')

class Game:

    def __init__(self, turn_duration=30, stack_duration=30, server=None, server_ip=None, server_port=None):
        """"
        cards_on_board is a cards list
        """
        self.board = board.Board(self)
        self.turn_duration = turn_duration
        self.stack_duration = stack_duration
        self.server = server
        self.curr_game_state = GameStates.VSKRYTIE
        self.turn_count = 0
        self.turn = 1
        self.current_active_player = 1
        self.curr_priority = 1
        self.in_stack = False
        self.stack = []
        self.passed_1 = False
        self.passed_2 = False
        self.cards_on_board1 = []
        self.cards_on_board2 = []
        self.defenders = []
        self.mode = 'offline'
        self.server_ip = server_ip
        self.server_port = server_port
        self.curr_id_on_bord = 0
        self.timer_state = {'restart': False, 'duration': self.turn_duration, 'state_name': 'Начало игры'}
        self.butt_state = [(0, 1), (0, 0)]  # 1 player(ph_button, eot_button)  2 player(ph_button, eot_button)
        self.selected_marks_list = []
        self.selected_card = [None, None]
        self.target_dict = {}
        self.flicker_dict = {}
        self.arrows = []
        self.dices = [[], []]
        self.popup_state = {}
        self.popup_temp = []
        self.send_count = 0
        self.card_exit = False
        self.red_fishki_bool = False
        self.stack_pause = False

    def set_cards(self, cards_on_board1, cards_on_board2, game):
        new_cards = []
        for block in [cards_on_board1, cards_on_board2]:
            for card in block:
                nc = card.__class__(card.player, card.loc, game)
                nc.id_on_board = self.curr_id_on_bord
                self.curr_id_on_bord += 1
                for i, a in enumerate(nc.abilities):
                    a.index = i
                new_cards.append(nc)
        self.populate_cards(new_cards)

    def populate_cards(self, new_cards):
        self.board.populate_board(new_cards)

    def check_game_end(self, *args):
        cards = self.board.get_all_cards()
        if not cards:
            text_ = 'Ничья'
        elif len([c for c in cards if c.player == 1]) == 0:
            text_ = 'Победа игрока 2!'
        elif len([c for c in cards if c.player == 2]) == 0:
            text_ = 'Победа игрока 1!'
        else:
            return
        if self.mode == 'online':
            print('check_game_end:', text_)
            self.server.end_game(text_)
        else:
            self.gui.on_game_end(text_)

    def player_passed(self, *args):
        # if self.in_stack:
        if self.curr_priority == 1:
            self.passed_1 = True
        else:
            self.passed_2 = True
        self.switch_priority()

    def get_roll_result(self,  count):
        res = []
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
        self.marks_bind = None
        self.target_dict = {}
        self.curr_priority = self.current_active_player
        self.passed_1 = False
        self.passed_2 = False
        if self.curr_game_state == GameStates.START_PHASE:
            if self.turn_count > 0:
                self.switch_curr_active_player()
                self.on_start_opening_phase()
        if self.curr_game_state == GameStates.OPENING_PHASE:
            self.turn_count += 1
        if self.curr_game_state == GameStates.MAIN_PHASE:
            cb = self.board.get_all_cards_with_callback(Condition.START_MAIN_PHASE)
            for c, a in cb:
                if a.check():
                    a.callback()
        if self.is_state_active(self.curr_game_state):
            self.handle_passes()
        else:
            self.next_game_state()


    def next_game_state(self, *args):
        self.passed_1 = False
        self.passed_2 = False
        next_state = self.curr_game_state.next_after_start()
        if self.is_state_active(next_state) or next_state == GameStates.MAIN_PHASE:
            self.curr_game_state = next_state
            self.on_step_start()
        else:
            self.curr_game_state = next_state
            self.on_step_start()

    def switch_priority(self, *args):
        if self.curr_priority == 1:
            self.curr_priority = 2
        else:
            self.curr_priority = 1
        # self.gui.buttons_on_priority_switch()

    def switch_curr_active_player(self):
        if self.current_active_player == 1:
            self.current_active_player = 2
            self.curr_priority = 2
        else:
            self.current_active_player = 1
            self.curr_priority = 1
        self.on_start_new_turn()

    def on_start_new_turn(self):
        for card in self.board.get_all_cards():
            if card.player != self.current_active_player and CardEffect.NETTED in card.active_status:
                card.active_status.remove(CardEffect.NETTED)
            # if self.turn_count > 1 and card.hidden:
            #     self.gui.unhide(card)

    def on_start_opening_phase(self):
        for c in self.board.get_all_cards():
            if c.player == self.current_active_player:
                if c.tapped:
                    c.tapped = False
                if CardEffect.NETTED in c.active_status:
                    c.actions_left = 0
                    c.curr_move = 0
                else:
                    c.actions_left = c.actions
                    c.curr_move = c.move

    def is_state_active(self, state):
        ret = False
        for card in self.board.get_all_cards():
            for ability in card.abilities:
                if not card.tapped and not isinstance(ability, TriggerBasedCardAction) and state in ability.state_of_action:
                    ret = True
        return ret

    def remove_fishka(self, card, amount):
        if callable(amount):
            cost = amount()
        else:
            cost = amount
        if card.curr_fishka >= cost:
            card.curr_fishka -= cost

    def update_arrows(self, card, target):
        out = []
        out.append(card.id_on_board)
        if isinstance(target, Card):
            out.append(target.id_on_board)
            out.append('card')
        elif isinstance(target, int):
            out.append(target)
            out.append('cell')
        elif isinstance(target, list):
            for el in target:
                if isinstance(el, int):
                    self.arrows.append([card.id_on_board, el, 'cell'])
                if isinstance(el, Card):
                    self.arrows.append([card.id_on_board, el.id_on_board, 'card'])
            return
        elif not target:
            out.append(card.id_on_board)
            out.append('card')
        self.arrows.append(out)

    def update_tap_to_hit_flyers(self, card):
        ground_1 = [x for x in [x for x in self.board.game_board if not isinstance(x, int)] if x.player == 1]
        ground_2 = [x for x in [x for x in self.board.game_board if not isinstance(x, int)] if x.player == 2]
        add_tap_for_flyer_flag = True
        to_add = TapToHitFlyerAction()
        to_add.index = len(card.abilities)
        for el in card.abilities:
            if isinstance(el, TapToHitFlyerAction):
                to_remove = el
                add_tap_for_flyer_flag = False
        if self.current_active_player == 1 and card.player == 1 and len(ground_2) == 0 \
                and card.type_ == CreatureType.CREATURE and add_tap_for_flyer_flag:
            card.abilities.append(to_add)
        elif self.current_active_player == 2 and card.player == 2 and len(ground_1) == 0 \
                and card.type_ == CreatureType.CREATURE and add_tap_for_flyer_flag:
            card.abilities.append(to_add)
        elif self.current_active_player == 1 and card.player == 1 and len(ground_2) != 0 \
                and card.type_ == CreatureType.CREATURE and not add_tap_for_flyer_flag:
            card.abilities.remove(to_remove)
        elif self.current_active_player == 2 and card.player == 2 and len(ground_1) != 0 \
                and card.type_ == CreatureType.CREATURE and not add_tap_for_flyer_flag:
            card.abilities.remove(to_remove)

    def check_for_card_ab_in_stack(self, card):
        for block in self.stack:
            for a, c, v, s in block:
                if card == c:
                    return True
        return False

    def check_card_abs_for_legality(self, card, pow):
        out = []
        for x in card.abilities:
            if ((not hasattr(x, 'display')) or x.display) and not card.tapped:
                if hasattr(x, 'disabled') and x.disabled:
                    out.append((x.txt, x.index, 1))
                elif not card.alive:
                    out.append((x.txt, x.index, 1))
                elif self.card_exit:
                    out.append((x.txt, x.index, 1))
                elif card.actions_left <= 0:
                    out.append((x.txt, x.index, 1))
                elif self.curr_game_state not in x.state_of_action:
                    out.append((x.txt, x.index, 1))
                elif self.check_for_card_ab_in_stack(card):
                    out.append((x.txt, x.index, 1))
                elif not x.isinstant and self.in_stack:
                    out.append((x.txt, x.index, 1))
                elif self.in_stack and card.player != self.curr_priority:
                    out.append((x.txt, x.index, 1))
                elif not self.in_stack and pow != self.current_active_player:
                    out.append((x.txt, x.index, 1))
                elif isinstance(x, IncreaseFishkaAction):
                    if card.curr_fishka >= card.max_fishka:
                        out.append((x.txt, x.index, 1))
                    else:
                        out.append((x.txt, x.index, 0))
                elif isinstance(x, FishkaCardAction):
                    if (isinstance(x.cost_fishka, int) and x.cost_fishka <= card.curr_fishka) or \
                            (callable(x.cost_fishka) and x.cost_fishka() <= card.curr_fishka):
                        out.append((x.txt, x.index, 0))
                    else:
                        out.append((x.txt, x.index, 1))
                else:
                    out.append((x.txt, x.index, 0))
            elif (not hasattr(x, 'display')) or x.display:
                out.append((x.txt, x.index, 1))
        return out


    def get_displayable_actions_for_gui(self, card, pow):
        self.update_tap_to_hit_flyers(card)
        if self.mode == 'online':
            if card.player == pow:
               out = self.check_card_abs_for_legality(card, pow)
            else:
                return [(x.txt, x.index, 1) for x in card.abilities if (not hasattr(x, 'display')) or x.display]
        else:
            out = self.check_card_abs_for_legality(card, pow)
        return out

    def card_to_state(self, card, player):
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
        res['tapped'] = card.tapped
        res['abilities'] = self.get_displayable_actions_for_gui(card, player)
        return res

    def form_state_obj(self, player):
        """what is displayed now over state:
        position, picture, life(curr/max), tap/untapped, flickers, popups,
        movement(curr/max), fishka/red fishka, buttons,
        red arrows, timer restart, def signs (zom)!"""
        state = {}
        all_cards = self.board.get_all_cards() + self.board.get_grave() + self.board.get_decks()
        cards = {}
        for card in all_cards:
            c_dict = self.card_to_state(card, player)
            cards[card.id_on_board] = c_dict
        state['cards'] = cards
        if self.curr_priority != player:
            state['markers'] = []
        else:
            state['markers'] = self.target_dict
        if player in self.flicker_dict.keys():
            state['flickers'] = self.flicker_dict[player]
        else:
            state['flickers'] = []
        if self.in_stack:
            self.timer_state['state_name'] = game_properties.state_to_str[self.curr_game_state] + ' Прио ' + str(self.curr_priority)
        else:
            self.timer_state['state_name'] = game_properties.state_to_str[self.curr_game_state] + ' игрока ' + str(self.current_active_player)
        state['timer'] = self.timer_state
        state['butt_state'] = self.butt_state[player-1]
        state['arrows'] = self.arrows
        state['dices'] = self.dices
        state['popups'] = self.popup_state
        state['red_fishki'] = self.red_fishki_bool
        return state

    def get_available_targets(self, ability, card):
        ret = []
        if isinstance(ability, MultipleCardAction):
            for t_val in ability.target_list:
                ret.append(self.get_available_targets_helper(ability, t_val, card))
            return ret
        elif hasattr(ability, 'multitarget') and ability.multitarget:
            for i, t_val in enumerate(ability.target_list):
                ret.append(self.get_available_targets_helper(ability, t_val, card, i))
            return ret
        else:
            return [self.get_available_targets_helper(ability, ability.targets, card)]

    def get_available_targets_helper(self, ability, t_val, card, ix=None):
        self.default_ability_target = []
        if t_val == 'all':
            targets = self.board.get_all_cards()
        elif t_val == 'ally':
            all_cards = self.board.get_all_cards()
            targets = [x for x in all_cards if x.player == card.player]
        elif t_val == 'enemy':
            all_cards = self.board.get_all_cards()
            targets = [x for x in all_cards if x.player != card.player]
        elif t_val == 'self':
            targets = [card]
        elif ability.a_type == ActionTypes.UDAR_CHEREZ_RYAD:
            targets = self.board.get_available_targets_uchr(card)
        elif callable(t_val):
            targets = t_val()
        elif isinstance(t_val, list):
            targets = t_val
        elif card.type_ == CreatureType.CREATURE and not card.can_hit_flyer:
            targets = self.board.get_ground_targets_min_max(card_pos_no=self.board.game_board.index(card),
                                                       range_max=ability.range_max, range_min=ability.range_min,
                                                       ability=ability)
            if hasattr(ability, 'target_restriction') and 'not_flyer' in ability.target_restriction:
                targets = [x for x in targets if x.type_ != CreatureType.FLYER]
            if hasattr(ability, 'target_restriction') and 'enemy' in ability.target_restriction:
                targets = [x for x in targets if x.player != card.player]
        elif card.can_hit_flyer:  # NO TARGETS ON GROUND ONLY FLYING CREATURES
            targets = self.board.get_flying_targets()
        elif card.type_ == CreatureType.FLYER:
            magnets = self.board.get_flyer_magnets(card.player, enemy=True)
            if magnets:
                targets = magnets
            else:
                targets = self.board.get_available_targets_flyer(card)
        if hasattr(ability, 'take_board_cells') and ability.take_board_cells:
            if targets:
                self.default_ability_target = targets[0]
            return {'cells': targets}
        elif hasattr(ability, 'multitarget') and ability.multitarget:
            if ability.cellsorfieldlist[ix] == 'card':
                return {'card_ids': [x.id_on_board for x in targets]}
            elif ability.cellsorfieldlist[ix] == 'cell':
                return {'cells': targets}
        else:
            if targets:
                self.default_ability_target = targets[0].id_on_board
            return {'card_ids': [x.id_on_board for x in targets]}


    def card_clicked(self, card, pow):
        """ send back ability list with active/passive status, move tile numbers"""
        print(self.curr_priority, self.current_active_player, self.curr_game_state)
        if self.card_exit:
            self.timer_state['restart'] = False
            self.send_state(player=pow)
            self.timer_state['restart'] = True
            return
        card = self.board.get_card_by_id(card)
        if card.player == pow and not self.in_stack and self.current_active_player == card.player:
            moves = self.board.get_available_moves(card)
        else:
            moves = []
        self.timer_state['restart'] = False
        self.selected_card[pow-1] = card
        self.marks_bind = DefaultMovementAction()
        self.target_dict = [{'cells': moves}]
        self.send_state(player=pow)
        self.timer_state['restart'] = True

    def ability_clicked(self, ability_id, pow):
        ab = self.selected_card[pow-1].get_ability_by_id(ability_id)
        self.marks_bind = ab
        if hasattr(ab, 'display_fast') and ab.display_fast:
            # self.stack.pop()
            ab.callback()
            return
        elif self.marks_bind.marks_needed == 0:
            self.selected_marks_list = []
            self.target_dict = {}
            self.add_to_stack(self.marks_bind, self.selected_card[pow-1], [], 0)
        else:
            self.timer_state['restart'] = False
            self.selected_marks_list = []
            self.target_dict = self.get_available_targets(self.marks_bind, self.selected_card[pow-1])
            self.send_state(player=pow)
            self.timer_state['restart'] = True

    def ability_clicked_forced(self, ab, card, pow, red_fishki=False):  # like selectcardaction
        self.card_exit = True
        self.stack_pause = True
        self.default_card = card
        self.default_ability = ab
        self.marks_bind = ab
        self.selected_card[pow-1] = card
        prev_prio = self.curr_priority
        if red_fishki:
            self.red_fishki_bool = True
        if self.marks_bind.marks_needed == 0:
            self.selected_marks_list = []
            self.target_dict = {}
            self.add_to_stack(self.marks_bind, self.selected_card[pow - 1], [], 0)
        else:
            self.timer_state['restart'] = False
            self.selected_marks_list = []
            self.target_dict = self.get_available_targets(self.marks_bind, self.selected_card[pow - 1])
            self.curr_priority = pow
            self.send_state(player=pow)
            self.curr_priority = prev_prio
            self.timer_state['restart'] = True


    def mark_clicked(self, marks, pow, *args):
        self.selected_marks_list = marks
        if self.marks_bind.marks_needed == len(self.selected_marks_list):
            self.target_dict = {}
            self.add_to_stack(self.marks_bind, self.selected_card[pow-1], self.selected_marks_list, 0)
            self.selected_marks_list = []
        else:
            pass

    def eot_clicked(self):
        if self.card_exit and self.default_ability_target:
            self.target_dict = {}
            self.add_to_stack(self.default_ability, self.default_card, self.default_ability_target, 0)
            self.default_ability = None
            self.default_card = None
        elif self.card_exit:
            self.card_exit = False
        self.next_game_state()
        if self.mode == 'online':
           self.send_state(1)
           self.send_state(2)
        else:
           self.send_state(1)

    def ph_clicked(self):
        if self.stack_pause:
            self.target_dict = {}
            self.stack_pause = False
        if self.card_exit and self.default_ability_target:
            self.target_dict = {}
            self.add_to_stack(self.default_ability, self.default_card, self.default_ability_target, 0)
            self.default_ability = None
            self.default_card = None
        elif self.card_exit:
            self.card_exit = False
        self.timer_state['restart'] = True
        self.player_passed()
        if self.mode == 'online':
            self.send_state(1)
            self.send_state(2)
        else:
            self.send_state(1)
        self.handle_passes()

    def timer_completed(self):
        if self.stack_pause:
            self.stack_pause = False
            self.target_dict = {}
        if self.card_exit and self.default_ability_target:
            self.target_dict = {}
            self.add_to_stack(self.default_ability, self.default_card, self.default_ability_target, 0)
            self.default_ability = None
            self.default_card = None
        elif self.card_exit:
            self.card_exit = False
        self.timer_state['restart'] = True
        if self.in_stack:
            self.player_passed()
            self.handle_passes()
        else:
            self.next_game_state()

    def send_state(self, player, msg=None):
        state = self.form_state_obj(player)
        if msg:
            print('send_state', msg, 'player:', player, 'state:', state)
        if self.mode == 'online':
            self.server.send_state(player, state)
        else:
            # print('send_state:', player, self.curr_priority)
            self.gui.on_state_received(state)

    def on_reveal(self, cards):
        for card in cards:
            if card.type_ == CreatureType.FLYER or card.type_ == CreatureType.LAND:
                self.board.game_board[card.loc] = 0
                card.loc = -1
                if card.player == 1:
                    self.board.extra1.append(card)
                else:
                    self.board.extra2.append(card)
        # Строй
        for card in cards:
            stroy_neighbors = self.board.get_adjacent_with_stroy(card.loc)
            if len(stroy_neighbors) != 0 and not card.in_stroy and card.stroy_in:
                card.stroy_in()

    def start(self, *args):
        if self.mode == 'online':
            pass
        else:
            self.gui.run()


    def on_load(self):
        self.on_reveal(self.board.get_all_cards())
        if self.mode == 'online':
            self.timer_state = {'restart': True, 'duration': self.turn_duration}
            self.send_state(1)
            self.send_state(2)
        else:
            self.timer_state = {'restart': True, 'duration': self.turn_duration}
            self.send_state(1)
        if not self.is_state_active(GameStates.VSKRYTIE):  # TODO add text for timer
            self.next_game_state()

    def check_for_defenders(self, ability, card, target, state):
        defenders = []
        if (ability.a_type == ActionTypes.ATAKA or ability.a_type == ActionTypes.UDAR_LETAUSHEGO) and state == 0 and \
                not CardEffect.NAPRAVLENNY_UDAR in card.active_status and (
                hasattr(ability, 'can_be_redirected') and ability.can_be_redirected):
            defenders = self.board.get_defenders(card, target)
        return defenders

    def stack_return_pending_attack(self):
        attk = ()
        for el in self.stack:  # assume attack is SimpleCardAction
            if len(el) == 1:
                ability, card, victim, stage = el[0]
                if (ability.a_type == ActionTypes.ATAKA or ability.a_type == ActionTypes.UDAR_LETAUSHEGO) and stage == 0 and \
                        not CardEffect.NAPRAVLENNY_UDAR in card.active_status and (
                        hasattr(ability, 'can_be_redirected') and ability.can_be_redirected):
                    attk = el[0]
        return attk

    def correct_stack_after_defence(self, a_ability, a_card, a_target, a_stage, new_attack, new_target):
        ix = -1
        for i, el in enumerate(self.stack):
            if len(el) == 1:
                ability, card, victim, stage = el[0]
                if ability == a_ability and card == a_card and victim == a_target and stage == a_stage:
                    ix = i
        if ix != -1:
            self.stack[ix][0] = [new_attack, a_card, new_target, a_stage]

    def handle_popups(self, question, texts, type, show_to, extra):
        if type == 'attack':
            self.popup_temp = extra
            self.popup_state = {'show_to': show_to, 'texts': texts, 'q': question, 'type': type}
        elif type == 'append':
            self.popup_temp = extra
            self.popup_state = {'show_to': show_to, 'texts': texts, 'q': question, 'type': type}

    def pop_up_clicked(self, choice, type_, *args):
        # if self.mode == 'online':  # TODO костыльно
        #     self.send_count += 1
        #     if self.send_count == 2:
        #         self.send_count = 0
        #     if self.send_count == 0:
        #         if self.popup_state:
        #             self.popup_state = {}
        # else:
        #     if self.popup_state:
        self.popup_state = {}
        if self.mode == 'online':
            self.send_state(1)
            self.send_state(2)
        else:
            self.send_state(1)
        if type_ == 'attack':
            ability, c, v, s = self.curr_top[0]
            a, b = self.popup_temp[int(choice)]
            if a:
                ability.damage_make = ability.damage[a - 1]
            else:
                ability.failed = True
                ability.damage_make = 0
            if b:
                ability.damage_receive = v.attack[b - 1]  # TODO possible bug
            else:
                ability.damage_receive = 0
            self.add_to_stack(ability, c, v, s)
        elif type_ == 'append':
            self.add_to_stack(*self.popup_temp[choice])

        self.popup_temp = []
        # print('cur top', self.curr_top)
        # print(choice, type_)


    def add_to_stack_helper(self, ability, card, target, stage=0):
        if hasattr(ability, 'take_board_cells') and ability.take_board_cells:
            if ability.marks_needed == 1:
                target = target[0]
            else:
                target = target
        elif hasattr(ability, 'multitarget') and ability.multitarget:
            out = []
            for i in range(len(ability.target_list)):
                if ability.cellsorfieldlist[i] == 'cell':
                    out.append(target[i])
                elif ability.cellsorfieldlist[i] == 'card':
                    out.append(self.board.get_card_by_id(target[i]))
            target = out
        else:
            if target is not None:
                if isinstance(target, list) and len(target) == 0:
                    target = target
                elif ability.marks_needed == 1 and isinstance(target, list):
                    target = target[0]
                if not isinstance(target, Card):
                    target = self.board.get_card_by_id(target)
        ability.passed = False  # to check if players allready passed once a each step
        instants = self.board.get_instants()
        if instants:
            self.in_stack = True
        if self.check_for_defenders(ability, card, target, stage):
            self.in_stack = False
        return ability, card, target, stage

    def add_to_stack(self, ability, card, target, stage=0):
        self.card_exit = False
        self.stack_pause = False
        if self.defenders:
            for c in self.defenders:
                c.defence_action.disabled = True
            self.defenders = []
        if isinstance(ability, MultipleCardAction):
            add = []
            for i, ab in enumerate(ability.action_list):
                ability, card, target, stage = self.add_to_stack_helper(ab, card, self.selected_marks_list[i], stage)
                add.append([ability, card, target, stage])
            self.stack.append(add)
        else:
            ability, card, target, stage = self.add_to_stack_helper(ability, card, target, stage)
            self.stack.append([[ability, card, target, stage]])
        if self.in_stack:
            self.passed_1 = False
            self.passed_2 = False
        else:
            self.passed_1 = True
            self.passed_2 = True


        if self.in_stack:
            self.timer_state = {'restart': True, 'duration': self.stack_duration}
            self.switch_priority()
            self.handle_passes()
        else:
            self.timer_state = {'restart': True, 'duration': self.turn_duration}
            self.switch_priority()
            self.handle_passes()

    def handle_passes(self):
        # print('handle_paasses:', self.flicker_dict)
        instants = self.board.get_instants()
        i1 = [(c, a) for (c, a) in instants if (c.player == 1 and c.actions_left > 0)]
        i2 = [(c, a) for (c, a) in instants if (c.player == 2 and c.actions_left > 0)]
        # print('i1', i1, 'i2', i2)
        # print('in gandle:', self.in_stack, self.curr_priority, self.passed_1, self.passed_2)
        if i1 or i2:
            self.in_stack = True
            if not i1 and self.curr_priority == 1:
                self.passed_1 = True
                self.switch_priority()
            if not i2 and self.curr_priority == 2:
                self.passed_2 = True
                self.switch_priority()
        else:
            self.curr_priority = self.current_active_player
            self.in_stack = False
            self.passed_1 = True
            self.passed_2 = True
        if self.passed_1 and self.passed_2:
            if len(self.stack) == 0 and self.curr_game_state != GameStates.MAIN_PHASE:
                self.next_game_state()
            if len(self.stack) == 0 and self.curr_game_state == GameStates.MAIN_PHASE:
                self.curr_priority = self.current_active_player
                self.in_stack = False
        # print(self.in_stack, self.passed_once, self.passed_1, self.passed_2)
        if self.in_stack and not(len(self.stack) == 0 and self.curr_game_state == GameStates.MAIN_PHASE):
            if self.curr_priority == 1:
                self.butt_state = [(1, 0), (0, 0)]
            else:
                self.butt_state = [(0, 0), (1, 0)]
        else:
            # print('mf', self.in_stack, self.current_active_player, self.curr_priority)
            if self.curr_priority == 1:
                self.butt_state = [(0, 1), (0, 0)]
            else:
                self.butt_state = [(0, 0), (0, 1)]
        if self.mode == 'online':
            self.send_state(1, msg='passes')
            self.send_state(2, msg='passes')
        else:
            self.send_state(1)
        if not self.passed_1 or not self.passed_2:
            return
        if self.passed_1 and self.passed_2 and self.stack:
            self.process_stack()

    def process_stack(self):
        # print('self.stack_pause', self.stack, self.stack_pause, self.passed_1, self.passed_2)
        if self.stack_pause:
            return
        self.red_fishki_bool = False
        self.dices = [[], []]
        while self.stack:
            if self.stack_pause:
                return
                # print('in stack!', self.passed_1, self.passed_2)
            if self.passed_1 and self.passed_2:
                self.curr_top = self.stack[-1]
                self.perform_action(self.curr_top)
                if self.mode == 'online':
                    self.send_state(1) #, msg='from stack')
                    self.send_state(2) #, msg='from stack')
                else:
                    # print('stack send')
                    self.send_state(1)
            else:
                return  # return here to get back to Kivy mainloop waiting for players to pass
            self.arrows = []
            self.handle_passes()


    def perform_action(self, action):
        stage = action[0][3]  # take stage of first action
        if stage == 0:
            self.perform_card_action_0(action)
        elif stage == 1:
            self.perform_card_action_1(action)
        elif stage == 2:
            self.perform_card_action_2(action)

    def perform_card_action_0(self, action):
        # STAGE 0  - PODGOTOVKA
        # self.draw_red_arrow(self.cards_dict[card], self.cards_dict[victim], card, victim) TODO RED ARROW
        for ability, card, target, stage in action:
            self.update_arrows(card, target)
            all_cards = self.board.get_all_cards()
            if not card in all_cards:
                self.stack.pop()
                return
            self.defenders = self.check_for_defenders(ability, card, target, stage)
            if self.defenders and not ability.passed:
                for c in self.defenders:
                    c.defence_action.disabled = False
                ability.passed = True
                self.in_stack = True
                self.passed_1 = False
                self.passed_2 = False
                self.curr_priority = card.player
                self.player_passed()
                self.flicker_dict = {target.player: [x.id_on_board for x in self.defenders]}
                                     # 3-int(target.player): [x.id_on_board for x in self.defenders]}  # for test
                self.handle_passes()
                return
            if ability.a_type == ActionTypes.ZASCHITA:
                pending_attack = self.stack_return_pending_attack()
                if pending_attack:
                    a_ability, a_card, a_target, a_stage = pending_attack
                    defenders = self.check_for_defenders(a_ability, a_card, a_target, a_stage)
                    if card in defenders:
                        card.actions_left -= 1
                        self.tap_card(card, cause='zashita')
                        new_ability = copy(a_ability)
                        new_ability.can_be_redirected = False
                        new_ability.redirected = True
                        self.correct_stack_after_defence(a_ability, a_card, a_target, a_stage, new_ability, card)
                        self.modify_stack_stage(new_ability, a_card, card, 1)
                        card.defender = True
                        self.stack.pop()
                        return
            if isinstance(ability, DefaultMovementAction):
                if not card.tapped:
                    stroy_neighbors_old = self.board.get_adjacent_with_stroy(card.loc)
                    prev = card.loc
                    card.loc = target
                    card.curr_move -= 1
                    self.board.update_board(prev, target, card)
                    # Строй
                    stroy_neighbors_new = self.board.get_adjacent_with_stroy(card.loc)
                    if len(stroy_neighbors_new) != 0 and not card.in_stroy and card.stroy_in:
                        card.stroy_in()
                        for neigh in stroy_neighbors_new:
                            if not neigh.in_stroy:
                                neigh.stroy_in()
                    elif len(stroy_neighbors_new) == 0 and card.in_stroy:
                        card.stroy_out()
                    if len(stroy_neighbors_old) != 0:  # убираем строй у соседей, оставшихся без строя
                        for neigh in stroy_neighbors_old:
                            if len(self.board.get_adjacent_with_stroy(neigh.loc)) == 0 and neigh.stroy_out:
                                neigh.stroy_out()
                    # Call Back Time
                    cb = self.board.get_all_cards_with_callback(Condition.ON_SELF_MOVING)
                    for c, a in cb:
                        if a.check():
                            a.callback()
                else:
                    pass
                self.stack.pop()
                return
            if isinstance(ability, IncreaseFishkaAction):
                self.add_fishka(card)
                self.stack.pop()
                return
            if isinstance(ability, TapToHitFlyerAction):
                card.can_hit_flyer = True
                card.actions_left -= 1
                self.tap_card(card)
                self.stack.pop()
                return
            if isinstance(ability, TriggerBasedCardAction):
                self.stack.pop()
                if ability.recieve_inc:
                    ability.callback(target)
                elif ability.recieve_all:
                    ability.callback(ability, card, target)
                else:
                    ability.callback()
                return
            if ability.a_type == ActionTypes.VOZROJDENIE:
                new_card, place = target
                new_card.alive = True
                new_card.loc = place
                new_card.player = card.player
                new_card.curr_life = new_card.life
                new_card.curr_move = new_card.move
                new_card.curr_fishka = new_card.start_fishka
                self.board.populate_board([new_card])
                self.on_reveal([new_card])
                new_card.zone = self.board.assign_initial_zone(new_card)
                if ability.is_tapped:
                    new_card.tapped = True
                else:
                    new_card.tapped = False
                if isinstance(ability, FishkaCardAction):
                    self.remove_fishka(card, ability.cost_fishka)
                self.tap_card(card)
                self.stack.pop()
                uq = self.board.check_for_uniqueness(new_card.player)
                if uq:
                    a = SimpleCardAction(a_type=ActionTypes.DESTRUCTION, damage=1, range_min=1, range_max=6,
                                         txt='Выберите какое уникальное существо оставить',
                                         ranged=False, state_of_action=[GameStates.MAIN_PHASE], target=uq, reverse=True)
                    # self.display_available_targets(self.backend.board, new_card, a, None, None)
                    self.ability_clicked_forced(a, new_card, new_card.player)
                return
            if ability.a_type == ActionTypes.DESTRUCTION:
                self.stack.pop()
                try:
                    iterator = iter(target)
                except TypeError:
                    self.destroy_card(target, is_ubiranie_v_colodu=True)
                else:
                    for t in target:
                        self.destroy_card(t, is_ubiranie_v_colodu=False)
                return
            if card in all_cards and target in all_cards:
                if ability.a_type == ActionTypes.TAP:
                    self.tap_card(target)
                    self.stack.pop()
                    return
                if (ability.a_type in ATTACK_LIST) and \
                        CardEffect.NETTED in target.active_status:
                    target.active_status.remove(CardEffect.NETTED)
                    target.actions_left = target.actions
                    target.curr_move = target.move
                    card.actions_left -= 1
                    if card.actions_left <= 0:
                        self.tap_card(card)
                    self.stack.pop()
                    return

            self.modify_stack_stage(ability, card, target, 1)
            ability.passed = False
        self.perform_card_action_1(action)

    def perform_card_action_1(self, action):
        self.flicker_dict = {}
        if self.defenders:
            for c in self.defenders:
                c.defence_action.disabled = True
            self.defenders = []
        print('perform_card_action_1', action, self.passed_1, self.passed_2)
        # STAGE 1 - KUBIKI
        # Шаг броска кубика (накладываем модификаторы к броску кубика, срабатывают особенности карт "при броске кубика")
        to_add_extra = []
        for ability, card, target, stage in action:
            ability.failed = False
            self.update_arrows(card, target)
            bonus1 = 0
            bonus2 = 0
            all_cards = self.board.get_all_cards()
            if not card in all_cards:
                self.stack.pop()
                return
            if ability.a_type in [ActionTypes.VYSTREL, ActionTypes.METANIE, ActionTypes.RAZRYAD]:  # bez UCHR
                cb = self.board.get_all_cards_with_callback(Condition.ON_RECIEVING_RANGED_ATTACK)
                for c, a in cb:
                    if c == target and a.check(ability, card, target):
                        a.callback(ability, card, target)
                        return
            print('rolls: ', ability.rolls, bonus1, bonus2)
            cb = self.board.get_all_cards_with_callback(Condition.ON_DEFENCE_BEFORE_DICE)
            for c, a in cb:
                a.cleanup()
                if a.check(ability, card, target):
                    a.callback_prep(ability, card, target)
                    return

            ability.rolls = []
            num_die_rolls_attack = 1
            num_die_rolls_def = 0
            if ability.a_type == ActionTypes.ATAKA or ability.a_type == ActionTypes.UDAR_LETAUSHEGO:
                if (not target.tapped or hasattr(target, 'defender') and target.defender) and not card.player == target.player:
                    num_die_rolls_def = 1
                    if target.rolls_twice:
                        num_die_rolls_def += 1
                if card.rolls_twice:
                    num_die_rolls_attack += 1
            ability.rolls = self.get_roll_result(num_die_rolls_attack + num_die_rolls_def)
            if ability.a_type == ActionTypes.ATAKA or ability.a_type == ActionTypes.UDAR_LETAUSHEGO:
                bonus1 = card.exp_in_off
                if ability.callback and ability.condition == Condition.ATTACKING:
                    ability.callback(target)
                if (not target.tapped or hasattr(target, 'defender') and target.defender) and not card.player == target.player:
                    if hasattr(target, 'defender'):
                        target.defender = False
                    bonus2 = target.exp_in_def
                    roll_attack = max(ability.rolls[:num_die_rolls_attack]) + bonus1
                    roll_def = max(ability.rolls[num_die_rolls_attack:]) + bonus2
                    outcome_list = self.get_fight_result(roll_attack, roll_def)
                    print('rolls: ', ability.rolls, bonus1, bonus2)
                    if len(outcome_list) == 1:
                        a, b = outcome_list[0]
                        if a:
                            ability.damage_make = ability.damage[a - 1]
                        else:
                            ability.damage_make = 0
                            ability.failed = True
                        if b:
                            ability.damage_receive = target.attack[b - 1]
                        else:
                            ability.damage_receive = 0
                    else:
                        if outcome_list[0][0] > outcome_list[0][1]:
                            show_to_ = card.player
                        else:
                            show_to_ = 3 - int(card.player)
                        dmg_dict = {0: 'Промах', 1: 'Слабый', 2: 'Средний', 3: 'Cильный'}
                        popup_texts = dmg_dict[outcome_list[0][0]] + '-' + dmg_dict[outcome_list[0][1]],\
                                      dmg_dict[outcome_list[1][0]] + '-' + dmg_dict[outcome_list[1][1]]
                        self.handle_popups(question='Выберите результат сражения', texts=popup_texts,
                                           type='attack', show_to=show_to_, extra=outcome_list)
                        self.modify_stack_stage(ability, card, target, 2)
                        if self.in_stack:
                            self.passed_1 = False
                            self.passed_2 = False
                        self.curr_priority = card.player
                        ability.passed = False
                        self.stack.pop()
                        self.process_rolls(ability.rolls, bonus1, bonus2, num_die_rolls_attack, num_die_rolls_def, card,
                                           target)
                        self.handle_passes()
                        return
                else:
                    roll1 = max(ability.rolls[:num_die_rolls_attack]) + bonus1
                    if roll1 <= 3:
                        d = ability.damage[0]
                    elif 4 <= roll1 <= 5:
                        d = ability.damage[1]
                    elif roll1 > 5:
                        d = ability.damage[2]
                    ability.damage_make = d
                    # if card.player == 1:
                    #     self.draw_die(bonus1, bonus2, ability.rolls, [])
                    # else:
                    #     self.draw_die(bonus2, bonus1, [], ability.rolls)
                    print('rolls: ', ability.rolls, bonus1, bonus2)
            else:
                roll1 = ability.rolls[0]
                if isinstance(ability.damage, int):
                    d = ability.damage
                elif callable(ability.damage):
                    d = ability.damage()
                elif len(ability.damage) == 3:
                    if roll1 <= 3:
                        d = ability.damage[0]
                    elif 4 <= roll1 <= 5:
                        d = ability.damage[1]
                    elif roll1 > 5:
                        d = ability.damage[2]
                ability.damage_make = d
            self.process_rolls(ability.rolls, bonus1, bonus2, num_die_rolls_attack, num_die_rolls_def, card, target)
            self.modify_stack_stage(ability, card, target, 2)
            if self.in_stack:
                self.passed_1 = False
                self.passed_2 = False
            self.curr_priority = card.player
            ability.passed = False
        self.handle_passes()

    def perform_card_action_2(self, action):
        #  STAGE 2 - NALOJENIE I OPLATA
        # Оба игрока должны пасануть в случае нахождения в стеке
        print('in perform_card_action_2', self.in_stack, self.stack)
        if not action[0][0].passed and self.in_stack:  # TODO questionable
            self.passed_1 = False
            self.passed_2 = False
            self.curr_priority = action[0][1].player
            action[0][0].passed = True
            self.handle_passes()
            return
        for ability, card, target, stage in action:
            self.update_arrows(card, target)
            all_cards = self.board.get_all_cards()
            cb = self.board.get_all_cards_with_callback(Condition.ON_MAKING_DAMAGE_STAGE)
            for c, a in cb:
                if a.check(ability, card, target):
                    a.prep(ability, card, target)
                    return
                a.cleanup()
            if self.stack:
                self.stack.pop()
            if isinstance(ability, BlockAction):
                to_block = ability.to_block
                for el in reversed(self.stack):
                        if el == to_block:
                            a,c,t,s = el[0]  # TODO only for single action abilities
                            self.stack.remove(el)
                            if not c.tapped:
                                c.tapped = True
                            if isinstance(a, FishkaCardAction):
                                self.remove_fishka(c, a.cost_fishka)
                return
            elif isinstance(target, list):
                for t in target:
                    self.deal_damage_stage_2(ability, card, t, stage)
            elif ability.a_type not in target.defences and card in all_cards and target in all_cards:
                self.deal_damage_stage_2(ability, card, target, stage)
            else:
                card.actions_left -= 1
                if card.actions_left <= 0:
                    self.tap_card(card)

            if hasattr(ability, 'on_complete') and ability.on_complete:
                ability.on_complete()
            ability.rolls = []  # cleanup
            ability.damage_make = 0
            ability.damage_receive = 0


    def deal_damage_stage_2(self, ability, card, target, stage):
        all_cards = self.board.get_all_cards()
        if ability.a_type not in target.defences and card in all_cards and target in all_cards:
            cb_abs = self.board.cards_callback(target, Condition.ON_TAKING_DAMAGE)
            for cb_ab in cb_abs:
                cb_ab.callback(ability, card, target)
            if ability.a_type == ActionTypes.ATAKA or ability.a_type == ActionTypes.UDAR_LETAUSHEGO:
                if card.can_hit_flyer and target.type_ == CreatureType.FLYER:
                    card.can_hit_flyer = False
                if ability.damage_make:
                    target.curr_life -= ability.damage_make
                if ability.damage_receive:
                    card.curr_life -= ability.damage_receive
            else:
                if ability.a_type == ActionTypes.LECHENIE:
                    target.curr_life = min(target.curr_life + ability.damage_make, target.life)
                elif ability.a_type == ActionTypes.EXTRA_LIFE:
                    target.life += ability.damage_make
                    target.curr_life += ability.damage_make
                elif ability.a_type in [ActionTypes.VYSTREL, ActionTypes.METANIE, ActionTypes.RAZRYAD]:  # bez UCHR
                    target.curr_life -= ability.damage_make
                elif ability.a_type == ActionTypes.NET:
                    target.actions_left = 0
                    target.active_status.append(CardEffect.NETTED)
                elif ability.a_type == ActionTypes.DOBIVANIE and target.curr_life <= ability.damage and \
                        CardEffect.BESTELESNOE not in target.active_status:
                    target.curr_life = 0
                else:
                    target.curr_life -= ability.damage_make

            if card and target:
                if card.curr_life <= 0 and card in all_cards:
                    self.destroy_card(card)
                if target.curr_life <= 0 and target in all_cards:
                    if CardEffect.TRUPOEDSTVO in card.active_status and not CardEffect.BESTELESNOE in target.active_status:
                        if card.type_ == CreatureType.FLYER or target.loc in self.board.get_adjacent_cells(card.loc):
                            card.curr_life = card.life
                            if CardEffect.OTRAVLEN in card.active_status:
                                card.otravlenie = 0
                                card.active_status.remove(CardEffect.OTRAVLEN)
                    self.destroy_card(target)
                card.actions_left -= 1
                if card.actions_left <= 0:
                    self.tap_card(card)

            if isinstance(ability, FishkaCardAction):
                self.remove_fishka(card, ability.cost_fishka)
            if hasattr(ability, 'failed') and not ability.failed:
                self.handle_PRI_ATAKE(ability, card, target)
                ability.failed = False
        else:
            card.actions_left -= 1
            if card.actions_left <= 0:
                self.tap_card(card)


    def handle_PRI_ATAKE(self, ability, card, victim, *args):
        all_cards = self.board.get_all_cards()
        if ability.a_type == ActionTypes.ATAKA or ability.a_type == ActionTypes.UDAR_LETAUSHEGO and card in all_cards and victim in all_cards:
            for ab in card.abilities:
                if isinstance(ab, TriggerBasedCardAction) and ab.condition == Condition.PRI_ATAKE:
                    if ab.recieve_inc:
                        ab.callback(victim)
                    else:
                        ab.callback()

    def tap_card(self, card, cause=None):
        if not card.tapped:
            card.tapped = True
            cb = self.board.get_all_cards_with_callback(Condition.ON_CREATURE_TAP)
            for c, a in cb:
                if a.check():
                    a.callback(cause)

    def process_rolls(self, rolls, bonus1, bonus2, x1, x2, card, target):
        # self.dices = [[], []]
        bonuses = [bonus1, bonus2]
        if isinstance(card, list) or isinstance(target, list):  # TODO
            return
        if not target or card.player == target.player:
            self.dices[card.player-1].append((rolls, bonuses[card.player-1]))
        elif card.player != target.player:
            if card.player == 1:
                self.dices[0].append((rolls[:x1], bonus1))
                self.dices[1].append((rolls[x1:], bonus2))
            if card.player == 2:
                self.dices[1].append((rolls[:x1], bonus2))
                self.dices[0].append((rolls[x1:], bonus1))



    def modify_stack_stage(self, ability, card, target, new_state):
        ix = -1
        ix1 = -1
        # print('stack', self.stack)
        for i, action in enumerate(self.stack):
            for j, (a, c, t, s) in enumerate(action):
                if a == ability and c == card and t == target:
                    ix = i
                    ix1 = j
                    break
        if ix != -1:
            self.stack[ix][ix1][3] = new_state
        # print('stack after', self.stack)

    def destroy_card(self, card, is_ubiranie_v_colodu=False):
        cb = self.board.get_all_cards_with_callback(Condition.ANYCREATUREDEATH)
        if cb and not is_ubiranie_v_colodu:
            for c, a in cb:
                self.add_to_stack(a, c, c, 0)
        self.board.remove_card(card)
        card.alive = False
        if card.player == 1 and not is_ubiranie_v_colodu:
            self.board.grave1.append(card)
            card.zone = 'gr'
        elif card.player == 2 and not is_ubiranie_v_colodu:
            self.board.grave2.append(card)
            card.zone = 'gr'
        elif card.player == 1 and is_ubiranie_v_colodu:
            card.zone = 'deck'
            self.board.deck1.append(card)
        elif card.player == 2 and is_ubiranie_v_colodu:
            card.zone = 'deck'
            self.board.deck2.append(card)
        self.check_game_end()

    def add_fishka(self, card, flag=False):
        close = True
        if flag:
            close = False
        if card.curr_fishka < card.max_fishka:
            card.curr_fishka += 1
            if close:
                card.actions_left -= 1
                self.tap_card(card)



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
    import berserk_gui
    gui = berserk_gui.BerserkApp(WINDOW_SIZE, pow=1, backend=game, mode='offline')
    game.gui = gui
    cards1 = [Elfiyskiy_voin_1(player=1, location=27, gui=game),
               Lovets_dush_1(player=1, location=13, gui=game),
               Gnom_basaarg_1(player=1, location=12, gui=game),
               Ledyanoy_ohotnik_1(player=1, location=21, gui=game),
               # Elfiyskiy_voin_1(player=1, location=12, gui=game),
               Necromant_1(player=1, location=14, gui=game),
               # Otshelnik_1(player=1, location=4, gui=game),
               Ar_gull_1(player=1, location=15, gui=game),
               Cobold_1(player=1, location=6, gui=game)
        ]
    cards2 = [
        Draks_1(player=2, location=20),
                Voin_hrama_1(player=2, location=22, gui=game),
                Ovrajnii_gnom_1(player=2, location=19, gui=game),
                # Otshelnik_1(player=2, location=18, gui=game),
                Gnom_basaarg_1(player=2, location=16, gui=game),
                Cobold_1(player=2, location=22, gui=gui), #Draks_1(player=2, location=25, gui=gui)
            ]
    game.set_cards(cards1, cards2, game)
    game.start()

