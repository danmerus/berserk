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
        self.a2.display_fast = True
        self.a2.passed = False
        self.a2.clear_cb = self.a2_non_ins
        self.abilities.append(self.a2)

    def a2_cb(self):
        N = self.a2.inc_ability.damage_make
        if N < 1:
            return
        # print('N:', N)
        self.a2.cleanup()
        self.a2.passed = False
        pereraspr = SimpleCardAction(a_type=ActionTypes.VOZDEISTVIE, damage=1, range_min=1, range_max=6,
                                    txt='Перераспределение ран simple', multitarget=True,
                                    target=self.a3_trg, display=False,
                                    on_complete=self.a2_on_complete,
                                    ranged=False, state_of_action=[GameStates.MAIN_PHASE])
        pereraspr.marks_needed = N
        pereraspr.target_list = [self.a3_trg for _ in range(N)]
        pereraspr.cellsorfieldlist = ['card' for _ in range(N)]
        self.gui.red_fishki_bool = True
        self.gui.send_state(self.player)
        self.gui.ability_clicked_forced(pereraspr, self, self.player, red_fishki=True)

    def a2_on_complete(self):
        self.a2.inc_ability.damage_make = 0


    def a2_prep(self, ability, card, target):
        self.a2.disabled = False
        self.a2.passed = True
        self.a2.inc_ability = ability
        self.a2.card = card
        self.a2.target = target
        self.gui.flicker_dict = {self.player: [self.id_on_board]}
        # if not self.gui.in_stack:
        # self.gui.in_stack = True
        if self.player == 1:
            self.gui.passed_2 = False
        else:
            self.gui.passed_1 = False
        # self.gui.curr_priority = self.player
        print(self.gui.passed_1, self.gui.passed_2)
        # self.gui.handle_passes()

    def a2_check(self, ability, card, target):
        return ability.a_type in [ActionTypes.ATAKA, ActionTypes.UDAR_LETAUSHEGO, ActionTypes.OSOBII_UDAR, ActionTypes.MAG_UDAR] and\
            not CardEffect.BESTELESNOE in target.active_status and target != self and target.player == self.player and not self.tapped and \
               ability.damage_make > 0 and not self.a2.passed  #and not self.a2.repeat

    def a3_trg(self):
        all_ = self.gui.board.get_all_cards()
        return [x for x in all_ if x != self and not CardEffect.BESTELESNOE in x.active_status and x.player == self.player and x != self.a2.target]

    def a2_non_ins(self, *args):
        self.gui.flicker_dict = {}
        self.a2.disabled = True
        self.a2.passed = False

