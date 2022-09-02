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
        self.butt_state = [(0, 0), (0, 0)]
        self.marks_list = []
        self.target_list = []

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


    def switch_priority(self, *args):
        if self.curr_priority == 1:
            self.curr_priority = 2
        else:
            self.curr_priority = 1
        # self.gui.buttons_on_priority_switch()

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
        position, picture, life(curr/max), tap/untapped,
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
        state['markers'] = self.target_list
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
        return [x.id_on_board for x in targets]


    def card_clicked(self, card, pow):
        """ send back ability list with active/passive status, move tile numbers"""
        if self.mode == 'online':
            pass
        else:
            card = self.board.get_card_by_id(card)
            ability_names = self.get_displayable_actions_for_gui(card, pow)
            moves = self.board.get_available_moves(card)
        self.selected_card = card  # it should handle two selected cards for two players
        self.marks_bind = DefaultMovementAction()
        return ability_names, moves

    def ability_clicked(self, ability_id):
        ab = self.selected_card.get_ability_by_id(ability_id)
        self.marks_bind = ab
        if self.marks_bind.marks_needed == 0:
            self.add_to_stack(self.marks_bind, self.selected_card, [], 0)
            self.marks_list = []
        else:
            self.marks_list = []
            self.target_list = self.get_available_targets(self.marks_bind, self.selected_card)
            self.send_state(player=self.selected_card.player)

        print('ability_clicked', ab)

    def mark_clicked(self, mark, *args):
        self.marks_list.append(mark)
        if self.marks_bind.marks_needed == len(self.marks_list):
            self.add_to_stack(self.marks_bind, self.selected_card, mark, 0)
            self.marks_list = []
        else:
            # self.display_available_targets()
            pass
        # print('clicked: ', mark, self.selected_card, self.marks_bind)

    def send_state(self, player):
        state = self.form_state_obj(player)
        if self.mode == 'online':
            pass
        else:
            self.gui.on_state_recieved(state)

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
            # Clock.schedule_once(lambda x: self.gui.start_timer(self.turn_duration, True), 0.1)  # TODO add text for timer
            # if not self.is_state_active(GameStates.VSKRYTIE):
            #     self.next_game_state()

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
        defenders = self.check_for_defenders(ability, card, target, stage)
        if defenders:
            self.in_stack = True
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
        elif isinstance(ability, MultipleCardAction):
            pass
        else:
            instants = self.board.get_instants()
            if instants:
                self.in_stack = True
        # self.draw_red_arrow(self.cards_dict[card], self.cards_dict[victim], card, victim) TODO RED ARROW
        # for c in self.defenders: TODO FLICKERING
        #     self.start_flickering(c, player=c.player)
        self.stack.append([(ability, card, target, stage)])
        # after adding to stack we send timer updates and might start stack processing
        if self.in_stack:
            self.timer_state = {'restart': True, 'duration': self.stack_duration}
            self.player_passed()
            self.handle_passes()
        else:
            self.timer_state = {'restart': True, 'duration': self.turn_duration}
            self.process_stack()

        # self.eot_button.disabled = True
        # self.backend.curr_priority = victim.player

    def handle_passes(self):
        if self.passed_1 and self.passed_2:
            self.process_stack()

    def process_stack(self):
        while self.stack:
            self.curr_top = self.stack[-1]
            self.perform_action(self.curr_top)
            self.send_state(1)
            # self.send_state(2) TODO FOR TEST


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
        out = []
        all_cards = self.board.get_all_cards()
        if not card in all_cards:
            return
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
                        target.tapped = True
                self.stack.pop()
                return

        self.modify_stack_stage(ability, card, target, 1)
        self.perform_card_action_1(ability, card, target, stage)
        #self.reset_passage()

    def perform_card_action_1(self, ability, card, target, stage):
        pass

    def modify_stack_stage(self, ability, card, target, new_state):
        ix = -1
        for i, (a, c, t, s) in enumerate(self.stack):
            if a == ability and c == card and t == target:
                ix = i
                break
        if ix != -1:
            self.stack[ix][3] = new_state

    def add_fishka(self, card, flag=None):
        close = True
        if flag:
            close = flag
        if card.curr_fishka < card.max_fishka:
            card.curr_fishka += 1
            if close:
                card.actions_left -= 1
                card.tapped = True

    def reset_passage(self):
        instants = self.board.get_instants()
        if instants:
            self.passed_1 = False
            self.passed_2 = False
        else:
            self.passed_1 = True
            self.passed_2 = True
        self.curr_priority = self.current_active_player



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
               # Otshelnik_1(player=1, location=4, gui=gui),
               Gnom_basaarg_1(player=1, location=15, gui=gui),
               Draks_1(player=1, location=5, gui=gui)
        ]
    cards2 = [
        # Bjorn_1(player=2, location=13),
        #         Ovrajnii_gnom_1(player=2, location=22, gui=gui),
        #        Necromant_1(player=2, location=19, gui=gui),
             Lovets_dush_1(player=2, location=18, gui=gui),
               Draks_1(player=2, location=16, gui=gui),
             #  Voin_hrama_1(player=2, location=22, gui=gui), Draks_1(player=2, location=25, gui=gui)
            ]
    game.set_cards(cards1, cards2, gui)
    game.start()

