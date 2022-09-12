from cards.card import Card
from cards.card_properties import *
from game_properties import GameStates
from functools import partial

class Otshelnik_1(Card):

    def __init__(self, player=1, location=0, gui=None, *args):
        super().__init__(
            life=6,
            move=1,
            attack=(1, 1, 2),
            name='Отшельник',
            vypusk=GameSet.VOYNA_STIHIY,
            rarity=Rarity.COMMON,
            color=CardColor.NEUTRAL,
            pic='data/cards/Otshelnik_1.jpg',
            cost=(0, 7),  # gold, silver,
            defences=[],
            is_unique=True,
            type_=CreatureType.CREATURE,
            actions_left=1,
            active_status=[],
            description='',
            curr_fishka=0,
            max_fishka=0,
            can_tap_for_fishka=False
        )

        self.add_default_abilities()
        self._update_abilities()
        self.player = player
        self.loc = location
        self.gui = gui


    def _update_abilities(self):  # txt max length 17
        a1 = SimpleCardAction(a_type=ActionTypes.LECHENIE, damage=1, range_min=0, range_max=6, txt='Лечение на 1',
                              ranged=True,  isinstant=True,
                              state_of_action=[GameStates.OPENING_PHASE, GameStates.END_PHASE, GameStates.MAIN_PHASE],
                              target='all')
        self.abilities.append(a1)

        self.a2 = TriggerBasedCardAction(txt='Перераспределение ран', recieve_inc=False, target=None,
                                         check=self.a2_check, prep=self.a2_prep, recieve_all=True,
                                         cleanup=self.a2_non_ins,
                                         isinstant=True, impose=False, state_of_action=[GameStates.MAIN_PHASE],
                                         callback=self.a2_cb, condition=Condition.ON_MAKING_DAMAGE_STAGE, display=True)
        self.a2.passed = False
        self.a2.clear_cb = self.a2_non_ins
        self.abilities.append(self.a2)
        # self.a32 = SimpleCardAction(a_type=ActionTypes.PERERASPREDELENIE_RAN, damage=0, range_min=1, range_max=6,
        #                        txt='Перераспределение ран simple',
        #                        target=self.a3_trg, display=False,
        #                        ranged=False, state_of_action=[GameStates.MAIN_PHASE])
        # self.abilities.append(self.a32)

    def a2_cb(self, ability, card, victim):
        N = self.a2.inc_ability.damage_make
        if N < 1:
            return
        print('N:', N)
        self.a2.cleanup()
        pereraspr = SimpleCardAction(a_type=ActionTypes.VOZDEISTVIE, damage=1, range_min=1, range_max=6,
                                    txt='Перераспределение ран simple',
                                    target='ally', display=False, #self.a3_trg
                                    ranged=False, state_of_action=[GameStates.MAIN_PHASE])
        # self.tapped = True  # TODO TAP SELF
        pereraspr.marks_needed = N
        self.gui.stack.pop()
        self.gui.ability_clicked_forced(pereraspr, self, self.player)

        # action_list = [SelectTargetAction(targets=self.a3_trg) for _ in range(N - 1)]
        # action_list.append(self.a32)
        # a3 = MultipleCardAction(a_type=ActionTypes.VOZDEISTVIE, txt='Перераспределение ран multi',
        #                         action_list=action_list,
        #                         target_callbacks=None,
        #                         ranged=True, state_of_action=[GameStates.MAIN_PHASE], take_all_targets=True,
        #                         isinstant=True)
        # self.a2.inc_ability.damage_make = 0

    def a2_prep(self, ability, card, target):
        print('prepped!')
        self.a2.disabled = False
        self.a2.passed = True
        self.a2.inc_ability = ability
        self.gui.flicker_dict = {self.player: [self.id_on_board]}
        self.gui.in_stack = True
        self.gui.passed_1 = False
        self.gui.passed_2 = False
        self.gui.curr_priority = self.player
        print(vars(self.a2))
        self.gui.handle_passes()

    def a2_check(self, ability, card, target):
        return ability.a_type in [ActionTypes.ATAKA, ActionTypes.UDAR_LETAUSHEGO, ActionTypes.OSOBII_UDAR, ActionTypes.MAG_UDAR] and\
            not CardEffect.BESTELESNOE in target.active_status and target != self and target.player == self.player and not self.tapped and \
               ability.damage_make > 0 and not self.a2.passed  #and not self.a2.repeat

    def a3_trg(self):
        all_ = self.gui.board.get_all_cards()
        return [x for x in all_ if x != self and not CardEffect.BESTELESNOE in x.active_status and x.player == self.player and x!= self.a2.victim]

    def a2_non_ins(self, *args):
        self.gui.flicker_dict = {}
        self.a2.disabled = True

