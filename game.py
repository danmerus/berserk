import os
import board
import berserk_gui
import numpy.random as rng

import network
from kivy.clock import Clock
from cards.card import *
from copy import copy

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
        self.timer_state = {'restart': False, 'duration': self.turn_duration}
        self.butt_state = [(0, 1), (0, 0)]  # 1 player(ph_button, eot_button)  2 player(ph_button, eot_button)
        self.selected_marks_list = []
        self.target_dict = {}
        self.flicker_list = []

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

    def next_game_state(self, *args):
        self.passed_1 = False
        self.passed_2 = False
        self.passed_once = False
        next_state = self.curr_game_state.next_after_start()
        if next_state == GameStates.MAIN_PHASE:
            cb = self.board.get_all_cards_with_callback(Condition.START_MAIN_PHASE)
            for c, a in cb:
                if c.player == self.current_active_player and a.check():
                    self.add_to_stack(a, c, c, 0)
        if self.is_state_active(next_state) or next_state == GameStates.MAIN_PHASE:
            self.curr_game_state = next_state
            self.on_step_start()
        else:
            self.curr_game_state = next_state
            self.on_step_start()
            self.next_game_state()


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
        self.turn_count += 1
        for card in self.board.get_all_cards():
            if card.player != self.current_active_player and CardEffect.NETTED in card.active_status:
                card.active_status.remove(CardEffect.NETTED)
                if not card.tapped:
                    card.actions_left = 1
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

    def get_displayable_actions_for_gui(self, card, pow):
        self.update_tap_to_hit_flyers(card)
        if card.player == pow:
            out = []
            for x in card.abilities:
                if ((not hasattr(x, 'display')) or x.display) and not card.tapped:
                    out.append((x.txt, x.index, 0))
                elif (not hasattr(x, 'display')) or x.display:
                    out.append((x.txt, x.index, 1))
            return out
        else:
            return [(x.txt, x.index, 1) for x in card.abilities if (not hasattr(x, 'display')) or x.display]

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
        res['tapped'] = card.tapped
        res['abilities'] = self.get_displayable_actions_for_gui(card, player)
        return res

    def form_state_obj(self, player):
        """what is displayed now over state:
        position, picture, life(curr/max), tap/untapped, flickers, popups,
        movement(curr/max), fishka/red fishka, buttons,
        red arrows, timer restart, def signs (zom)!"""
        state = {}
        all_cards = self.board.get_all_cards() + self.board.get_grave()
        cards = {}
        for card in all_cards:
            c_dict = self.card_to_state(card, player)
            cards[card.id_on_board] = c_dict
        # клетка на поле или существо в доп зоне ? отправляем только одному игроку
        state['cards'] = cards
        state['markers'] = self.target_dict
        state['flickers'] = self.flicker_list
        state['timer'] = self.timer_state
        state['butt_state'] = self.butt_state[player-1]
        return state

    def get_available_targets(self, ability, card):
        if ability.targets == 'all':
            targets = self.board.get_all_cards()
        elif ability.targets == 'ally':
            all_cards = self.board.get_all_cards()
            targets = [x for x in all_cards if x.player == card.player]
        elif ability.targets == 'enemy':
            all_cards = self.board.get_all_cards()
            targets = [x for x in all_cards if x.player != card.player]
        elif ability.targets == 'self':
            targets = [card]
        elif ability.a_type == ActionTypes.UDAR_CHEREZ_RYAD:
            targets = self.board.get_available_targets_uchr(card)
        elif callable(ability.targets):
            targets = ability.targets()
        elif isinstance(ability.targets, list):
            targets = ability.targets
        elif card.type_ == CreatureType.CREATURE and not card.can_hit_flyer:
            targets = self.board.get_ground_targets_min_max(card_pos_no=self.board.game_board.index(card),
                                                       range_max=ability.range_max, range_min=ability.range_min,
                                                       ability=ability)
            if hasattr(ability, 'target_restriction') and 'not_flyer' in ability.target_restriction:
                targets = [x for x in targets if x.type_ != CreatureType.FLYER]
            if hasattr(ability, 'target_restriction') and 'enemy' in ability.target_restriction:
                targets = [x for x in targets if x.player != card.player]
        elif card.can_hit_flyer:  # NO TARGETS ON GROUND ONLY FLYING  CREATURES
            targets = self.board.get_flying_targets()
        elif card.type_ == CreatureType.FLYER:
            magnets = self.board.get_flyer_magnets(card.player, enemy=True)
            if magnets:
                targets = magnets
            else:
                targets = self.board.get_available_targets_flyer(card)
        if hasattr(ability, 'take_board_cells') and ability.take_board_cells:
            return {'cells': targets}
        else:
            return {'card_ids': [x.id_on_board for x in targets]}


    def card_clicked(self, card, pow):
        """ send back ability list with active/passive status, move tile numbers"""
        if self.mode == 'online':
            pass
        else:
            card = self.board.get_card_by_id(card)
            ability_names = self.get_displayable_actions_for_gui(card, pow)
            if card.player == pow:
                moves = self.board.get_available_moves(card)
            else:
                moves = []
        self.selected_card = card  # it should handle two selected cards for two players
        self.marks_bind = DefaultMovementAction()
        return ability_names, moves

    def ability_clicked(self, ability_id):
        ab = self.selected_card.get_ability_by_id(ability_id)
        self.marks_bind = ab
        if self.marks_bind.marks_needed == 0:
            self.selected_marks_list = []
            self.target_dict = {}
            self.add_to_stack(self.marks_bind, self.selected_card, [], 0)
        else:
            self.selected_marks_list = []
            self.target_dict = self.get_available_targets(self.marks_bind, self.selected_card)
            self.send_state(player=self.selected_card.player)


    def mark_clicked(self, mark, *args):
        self.selected_marks_list.append(mark)
        if self.marks_bind.marks_needed == len(self.selected_marks_list):
            self.target_dict = {}
            self.add_to_stack(self.marks_bind, self.selected_card, self.selected_marks_list, 0)
            self.selected_marks_list = []
        else:
            self.target_dict = self.get_available_targets(self.marks_bind, self.selected_card)
            self.send_state(player=self.selected_card.player)

    def eot_clicked(self):
       self.next_game_state()
       if self.mode == 'online':
           self.send_state(1)
           self.send_state(2)
       else:
           self.send_state(1)

    def ph_clicked(self):
        self.player_passed()
        if self.mode == 'online':
            self.send_state(1)
            self.send_state(2)
        else:
            self.send_state(1)
        self.handle_passes()


    def send_state(self, player):
        state = self.form_state_obj(player)
        if self.mode == 'online':
            pass
        else:
            self.gui.on_state_received(state)

    def on_reveal(self):
        cards = self.board.get_all_cards()
        for card in cards:
            if card.type_ == CreatureType.FLYER or card.type_ == CreatureType.LAND:
                self.board.game_board[card.loc] = 0
                card.loc = -1
                if card.player == 1:
                    self.board.extra1.append(card)
                else:
                    self.board.extra2.append(card)


    def start(self, *args):
        if self.mode == 'online':
            pass
        else:
            self.gui.run()


    def on_load(self, client):
        self.on_reveal()
        if self.mode == 'online':
            pass
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
        for el in self.stack:
            if len(el) == 1:
                ability, card, victim, stage = el[0]
                if ability==a_ability and card==a_card and victim==a_target and stage==a_stage:
                    ability = new_attack
                    victim = new_target

    def add_to_stack(self, ability, card, target, stage=0):
        if isinstance(ability, MultipleCardAction):
            pass
        else:
            instants = self.board.get_instants()
            if instants:
                self.in_stack = True
        if hasattr(ability, 'take_board_cells') and ability.take_board_cells:
            if ability.marks_needed == 1:
                target = target[0]
            else:
                target = target
        else:
            if ability.marks_needed == 1:
                target = target[0]
            target = self.board.get_card_by_id(target)
        self.stack.append([[ability, card, target, stage]])
        # after adding to stack we send timer updates and might start stack processing
        if self.in_stack:
            self.timer_state = {'restart': True, 'duration': self.stack_duration}
            self.player_passed()
            self.handle_passes()
        else:
            self.timer_state = {'restart': True, 'duration': self.turn_duration}
            self.handle_passes()

    def handle_passes(self):
        if self.in_stack:
            if self.curr_priority == 1:  # check if has any instants
                self.butt_state = [(1, 0), (0, 0)]
            else:
                self.butt_state = [(1, 0), (0, 0)]
        else:
            self.passed_1 = True
            self.passed_2 = True
            if self.curr_priority == 1:
                self.butt_state = [(0, 1), (0, 0)]
            else:
                self.butt_state = [(0, 0), (0, 1)]
        if self.mode == 'online':
            self.send_state(1)
            self.send_state(2)
        else:
            print(self.passed_1, self.passed_2)
            self.send_state(1)
        if not self.passed_1 or not self.passed_2:
            return
        if self.passed_1 and self.passed_2:
            self.process_stack()

    def process_stack(self):
        while self.stack:
            print('in stack!', self.passed_1, self.passed_2)
            if self.passed_1 and self.passed_2:
                self.curr_top = self.stack[-1]
                self.perform_action(self.curr_top)
                if self.mode == 'online':
                    self.send_state(1)
                    self.send_state(2)
                else:
                    self.send_state(1)
            else:
                return  # return here to get back to Kivy mainloop waiting for players to pass


    def perform_action(self, action):
        for ability, card, target, stage in action:
            if stage == 0:
                self.perform_card_action_0(ability, card, target, stage)
            elif stage == 1:
                self.perform_card_action_1(ability, card, target, stage)
            elif stage == 2:
                self.perform_card_action_2(ability, card, target, stage)

    def perform_card_action_0(self, ability, card, target, stage):
        # STAGE 0  - PODGOTOVKA
        # self.draw_red_arrow(self.cards_dict[card], self.cards_dict[victim], card, victim) TODO RED ARROW
        # for c in self.defenders: TODO FLICKERING
        #     self.start_flickering(c, player=c.player)
        all_cards = self.board.get_all_cards()
        if not card in all_cards:
            return
        defenders = self.check_for_defenders(ability, card, target, stage)
        if defenders:
            self.in_stack = True
            self.flicker_list = [x.id_on_board for x in defenders]
        if ability.a_type == ActionTypes.ZASCHITA:
            pending_attack = self.stack_return_pending_attack()
            if pending_attack:
                a_ability, a_card, a_target, a_stage = pending_attack
                defenders = self.check_for_defenders(a_ability, a_card, a_target, a_stage)
                if card in defenders:
                    # card.actions_left -= 1
                    # card.tapped = True
                    new_ability = copy(a_ability)
                    new_ability.can_be_redirected = False
                    self.correct_stack_after_defence(a_ability, a_card, a_target, a_stage, new_ability, card)
        if isinstance(ability, DefaultMovementAction):
            if not card.tapped:
                prev = card.loc
                card.loc = target
                card.curr_move -= 1
                self.board.update_board(prev, target, card)
                # TODO stroy check + gnom basaarg cb
            else:
                pass
            self.stack.pop()
            return
        # elif isinstance(ability, LambdaCardAction): ересь
        #     ability.func()
        #     return
        # if isinstance(ability, FishkaCardAction): кнопка должна быть неактивна
        #     if (isinstance(ability.cost_fishka, int) and ability.cost_fishka > card.curr_fishka) or \
        #             (callable(ability.cost_fishka) and ability.cost_fishka() > card.curr_fishka):
        #         self.destroy_target_rectangles()
        #         self.destroy_target_marks()
        #         return
        if isinstance(ability, IncreaseFishkaAction):
            self.add_fishka(card)
            self.stack.pop()
            return
        if isinstance(ability, TapToHitFlyerAction):
            card.can_hit_flyer = True
            card.actions_left -= 1
            card.tapped = True
            self.stack.pop()
            return
        if isinstance(ability, TriggerBasedCardAction):
            if ability.recieve_inc:
                ability.callback(target)
            elif ability.recieve_all:
                ability.callback(ability, card, target)
            else:
                ability.callback()
            self.stack.pop()
            return
        # if isinstance(ability, SelectCardAction):
        #     self.display_available_targets(self.backend.board, card, ability, 1, None)
        #     return
        # if ability.a_type == ActionTypes.VOZROJDENIE:
        #     new_card, place = victim
        #     if (new_card.player == 1 and self.pow == 1) or (new_card.player == 2 and self.pow == 2):
        #         self.grave_1_gl.remove_widget(self.cards_dict[new_card])
        #         self.grave_buttons_1.remove(self.cards_dict[new_card])
        #         self.backend.board.grave1.remove(new_card)
        #     elif (new_card.player == 1 and self.pow == 2) or (new_card.player == 2 and self.pow == 1):
        #         self.grave_2_gl.remove_widget(self.cards_dict[new_card])
        #         self.grave_buttons_2.remove(self.cards_dict[new_card])
        #         self.backend.board.grave2.remove(new_card)
        #     self.cleanup_card(new_card)
        #     new_card.loc = place
        #     new_card.player = card.player
        #     self.backend.board.populate_board([new_card])
        #     self.reveal_cards([new_card])
        #     if ability.is_tapped:
        #         new_card.tapped = False
        #         self.tap_card(new_card)
        #     else:
        #         new_card.tapped = True
        #         self.tap_card(new_card)
        #     if isinstance(ability, FishkaCardAction):
        #         self.remove_fishka(card, ability.cost_fishka)
        #     uq = self.check_for_uniqueness(new_card.player)
        #     if uq:
        #         a = SimpleCardAction(a_type=ActionTypes.DESTRUCTION, damage=1, range_min=1, range_max=6,
        #                              txt='Выберите какое уникальное существо оставить',
        #                              ranged=False, state_of_action=[GameStates.MAIN_PHASE], target=uq, reverse=True)
        #         self.display_available_targets(self.backend.board, new_card, a, None, None)
        #     return
        # if isinstance(ability, SelectTargetAction):
        #     return
        # if ability.a_type == ActionTypes.DESTRUCTION:
        #     try:
        #         iterator = iter(victim)
        #     except TypeError:
        #         self.destroy_card(victim, is_ubiranie_v_colodu=True)
        #     else:
        #         for t in victim:
        #             self.destroy_card(t, is_ubiranie_v_colodu=True)
        #     self.destroy_target_rectangles()
        #     self.destroy_target_marks()
        #     return
        # if isinstance(ability, PopupAction):
        #     if not hasattr(self, 'attack_popup'):
        #         self.attack_popup = self.create_selection_popup('Сделайте выбор: ',
        #                                                         button_texts=ability.options,
        #                                                         button_binds=ability.action_list,
        #                                                         show_to=ability.show_to)
        #     self.press_1 = ability.action_list[0]
        #     dur = self.timer.duration - 1
        #     self.timer_ability = Animation(duration=dur)
        #     self.timer_ability.bind(on_complete=self.press_1)
        #     self.timer_ability.start(self)
        #     return
        # if ability.a_type == ActionTypes.PERERASPREDELENIE_RAN:  # Implicitly make it as 1 damage
        #     self.remove_pereraspredelenie_ran()
        #     if isinstance(victim, list):
        #         for vi in victim:
        #             if card in all_cards and vi in all_cards:
        #                 rana = SimpleCardAction(a_type=ActionTypes.VOZDEISTVIE, damage=1, range_min=0, range_max=6,
        #                                         txt='1 рана',
        #                                         ranged=False, isinstant=False,
        #                                         state_of_action=[GameStates.MAIN_PHASE], target='all')
        #                 out.append((rana, card, vi, 1))
        #     self.reset_passage()
        #     self.backend.stack.append(out)
        #     self.destroy_flickering(card)
        #     self.process_stack()
        #     return
        if card in all_cards and target in all_cards:
            if ability.a_type == ActionTypes.TAP:
                if not target.tapped:
                    target.tapped = True
                self.stack.pop()
                return
            if (ability.a_type in ATTACK_LIST) and \
                    CardEffect.NETTED in target.active_status:
                target.active_status.remove(CardEffect.NETTED)
                target.actions_left = target.actions
                target.curr_move = target.move
                card.actions_left -= 1
                if card.actions_left <= 0:
                    if not card.tapped:
                        card.tapped = True
                self.stack.pop()
                return

        self.modify_stack_stage(ability, card, target, 1)
        self.perform_card_action_1(ability, card, target, stage)
        #self.reset_passage()

    def perform_card_action_1(self, ability, card, target, stage):
        # STAGE 1 - KUBIKI
        # Шаг броска кубика (накладываем модификаторы к броску кубика, срабатывают особенности карт "при броске кубика")
        to_add_extra = []
        bonus1 = 0
        bonus2 = 0
        all_cards = self.board.get_all_cards()
        if not card in all_cards:
            return
        ability.rolls = []
        num_die_rolls_attack = 1
        num_die_rolls_def = 0
        if ability.a_type == ActionTypes.ATAKA or ability.a_type == ActionTypes.UDAR_LETAUSHEGO:
            if not target.tapped and not card.player == target.player:
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
            if not target.tapped and not card.player == target.player:
                bonus2 = target.exp_in_def
                roll_attack = max(ability.rolls[:num_die_rolls_attack]) + bonus1
                roll_def = max(ability.rolls[num_die_rolls_attack:]) + bonus2
                outcome_list = self.get_fight_result(roll_attack, roll_def)
                # if card.player == 1: TODO DRAW DIE
                #     self.draw_die(bonus1, bonus2,
                #                   ability.rolls[:num_die_rolls_attack], ability.rolls[num_die_rolls_attack:])
                # else:
                #     self.draw_die(bonus2, bonus1,
                #                   ability.rolls[num_die_rolls_attack:], ability.rolls[:num_die_rolls_attack])
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
                    pass
                    # if outcome_list[0][0] > outcome_list[0][1]:
                    #     show_to_ = card.player
                    # else:
                    #     show_to_ = 3 - int(card.player)
                    # dmg_dict = {0: 'Промах', 1: 'Слабый', 2: 'Средний', 3: 'Cильный'}
                    # self.attack_popup = self.create_selection_popup('Выберите результат сражения: ',
                    #                                                 [dmg_dict[outcome_list[0][0]] + '-' + dmg_dict[
                    #                                                     outcome_list[0][1]],
                    #                                                  dmg_dict[outcome_list[1][0]] + '-' + dmg_dict[
                    #                                                      outcome_list[1][1]]],
                    #                                                 button_binds=[partial(self.popup_attack_bind,
                    #                                                                       outcome_list[0], ability,
                    #                                                                       card, victim),
                    #                                                               partial(self.popup_attack_bind,
                    #                                                                       outcome_list[1], ability,
                    #                                                                       card, victim)],
                    #                                                 show_to=show_to_)
                    #
                    # self.press_1 = lambda *_: self.popup_attack_bind(outcome_list[1], ability, card, victim)
                    # dur = self.timer.duration - 1
                    # self.timer_ability = Animation(duration=dur)
                    # self.timer_ability.bind(on_complete=self.press_1)
                    # self.timer_ability.start(self)
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
            draw = False  # To only show die when it matters
            roll1 = ability.rolls[0]
            if isinstance(ability.damage, int):
                d = ability.damage
            elif callable(ability.damage):
                d = ability.damage()
            elif len(ability.damage) == 3:
                draw = True
                if roll1 <= 3:
                    d = ability.damage[0]
                elif 4 <= roll1 <= 5:
                    d = ability.damage[1]
                elif roll1 > 5:
                    d = ability.damage[2]
            ability.damage_make = d
            # if ability.a_type in [ActionTypes.VYSTREL, ActionTypes.METANIE, ActionTypes.RAZRYAD]:  # bez UCHR
            #     cb = self.board.get_all_cards_with_callback(Condition.ON_RECIEVING_RANGED_ATTACK)
            #     for c, a in cb:
            #         if c == target:
            #             to_add_extra.append((a, target, ability, 0))
            # if self.current_active_player == 1 and draw:
            #     self.draw_die(bonus1, bonus2, ability.rolls, [])
            # elif self.current_active_player == 2 and draw:
            #     self.draw_die(bonus1, bonus2, [], ability.rolls)
            print('rolls: ', ability.rolls, bonus1, bonus2)

        # self.reset_passage()
        self.modify_stack_stage(ability, card, target, 2)
        self.passed_1 = False
        self.passed_2 = False
        self.curr_priority = card.player
        self.handle_passes()
        # self.perform_card_action_2(ability, card, target, stage)

    def perform_card_action_2(self, ability, card, target, stage):
        #  STAGE 2 - NALOJENIE I OPLATA
        all_cards = self.board.get_all_cards()
        if isinstance(ability, BlockAction):
            to_block = ability.to_block
            for el in reversed(self.stack):
                for a, c, v, s in el:
                    if a == to_block:
                        self.stack.remove(el)
                        if not c.tapped:
                            c.tapped = True
                        if isinstance(a, FishkaCardAction):
                            self.remove_fishka(c, a.cost_fishka)
        elif ability.a_type not in target.defences and card in all_cards and target in all_cards:
            cb_abs = self.board.cards_callback(target, Condition.ON_TAKING_DAMAGE)
            for cb_ab in cb_abs:
                cb_ab.callback(card, ability)
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
                    if card.type_ == CreatureType.FLYER or target.loc in self.backend.board.get_adjacent_cells(card.loc):
                        card.curr_life = card.life
                        if CardEffect.OTRAVLEN in card.active_status:
                            card.otravlenie = 0
                            card.active_status.remove(CardEffect.OTRAVLEN)
                self.destroy_card(target)
            card.actions_left -= 1
            if card.actions_left <= 0:
                if not card.tapped:
                    card.tapped = True

        if isinstance(ability, FishkaCardAction):
            self.remove_fishka(card, ability.cost_fishka)
        if hasattr(ability, 'failed') and not ability.failed:
            self.handle_PRI_ATAKE(ability, card, target)
            ability.failed = False
        ability.rolls = []  # cleanup
        ability.damage_make = 0
        ability.damage_receive = 0
        self.stack.pop()

    def handle_PRI_ATAKE(self, ability, card, victim, *args):
        all_cards = self.board.get_all_cards()
        if ability.a_type == ActionTypes.ATAKA or ability.a_type == ActionTypes.UDAR_LETAUSHEGO and card in all_cards and victim in all_cards:
            for ab in card.abilities:
                if isinstance(ab, TriggerBasedCardAction) and ab.condition == Condition.PRI_ATAKE:
                    if ab.recieve_inc:
                        ab.callback(victim)
                    else:
                        ab.callback()

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

    def add_fishka(self, card, flag=None):
        close = True
        if flag:
            close = flag
        if card.curr_fishka < card.max_fishka:
            card.curr_fishka += 1
            if close:
                card.actions_left -= 1
                card.tapped = True



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
    cards1 = [Elfiyskiy_voin_1(player=1, location=27, gui=game),
               Lovets_dush_1(player=1, location=13, gui=game),
              #  Lovets_dush_1(player=1, location=0, gui=game),
              # Necromant_1(player=1, location=21, gui=game),
               Pauk_peresmeshnik_1(player=1, location=12, gui=game),
               Cobold_1(player=1, location=14),
               # Otshelnik_1(player=1, location=4, gui=game),
               Gnom_basaarg_1(player=1, location=15, gui=game),
               Draks_1(player=1, location=5, gui=game)
        ]
    cards2 = [
        # Bjorn_1(player=2, location=13),
        #         Ovrajnii_gnom_1(player=2, location=22, gui=game),
                Necromant_1(player=2, location=19, gui=game),
             Lovets_dush_1(player=2, location=18, gui=game),
               Draks_1(player=2, location=16, gui=game),
             #  Voin_hrama_1(player=2, location=22, gui=gui), Draks_1(player=2, location=25, gui=gui)
            ]
    game.set_cards(cards1, cards2, game)
    game.start()

