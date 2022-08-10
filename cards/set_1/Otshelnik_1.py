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
        # self.abilities.append(a1)

        self.a2 = TriggerBasedCardAction(txt='Перераспределение ран', recieve_inc=False, target=None,
                                         check=self.a2_check, prep=self.a2_prep, recieve_all=True,
                                         callback=self.a1_cb, condition=Condition.ON_MAKING_DAMAGE_STAGE, display=True)
        self.a2.repeat = False
        self.a2.clear_cb = self.a2_non_ins
        self.abilities.append(self.a2)

    def a1_cb(self, ability, card, victim):
        N = self.a2.inc_ability.damage_make
        if N < 1:
            return
        a32 = SimpleCardAction(a_type=ActionTypes.PERERASPREDELENIE_RAN, damage=0, range_min=1, range_max=6,
                               txt='Перераспределение ран simple',
                               target=self.a3_trg,
                               ranged=False, state_of_action=[GameStates.MAIN_PHASE])
        action_list = [SelectTargetAction(targets=self.a3_trg) for _ in range(N - 1)]
        action_list.append(a32)
        print('N ', N)
        a3 = MultipleCardAction(a_type=ActionTypes.VOZDEISTVIE, txt='Перераспределение ран multi',
                                action_list=action_list,
                                target_callbacks=None,
                                ranged=True, state_of_action=[GameStates.MAIN_PHASE], take_all_targets=True,
                                isinstant=False)
        self.a2.disabled = True
        self.a2.isinstant = False
        self.a2.stay_disabled = True
        self.gui.start_stack_action(a3, self, self, 0, -1)

    def a2_prep(self):
         #(LambdaCardAction(func=self.a1_non_ins), None, None, 1)])
        self.gui.start_flickering(self)

    def a2_check(self, card, victim, ability):
        return ability.a_type in [ActionTypes.ATAKA, ActionTypes.UDAR_LETAUSHEGO, ActionTypes.OSOBII_UDAR, ActionTypes.MAG_UDAR] and\
            not CardEffect.BESTELESNOE in victim.active_status and victim != self and victim.player == self.player and not self.tapped and \
               ability.damage_make > 0 and not self.a2.repeat

    def a3_trg(self):
        all_ = self.gui.backend.board.get_all_cards()
        return [x for x in all_ if x!=self and  not CardEffect.BESTELESNOE in x.active_status and x.player==self.player]

    def a2_non_ins(self):
        self.a2.repeat = False
        self.a2.disabled = True
        self.a2.stay_disabled = True
        self.a2.isinstant = False
        self.a2.inc_ability = None
