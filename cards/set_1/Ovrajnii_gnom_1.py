from cards.card import Card
from cards.card import Card
from cards.card_properties import *
from game_properties import GameStates
from functools import partial

class Ovrajnii_gnom_1(Card):

    def __init__(self, player=1, location=0, gui=None):
        super().__init__(
            life=6,
            move=1,
            attack=(1, 1, 2),
            name='Овражный Гном',
            vypusk=GameSet.VOYNA_STIHIY,
            rarity=Rarity.COMMON,
            color=CardColor.GORY,
            card_class=CardClass.GNOME,
            pic='data/cards/Otvajnii_gnom_1.jpg',
            cost=(0, 3),  # gold, silver,
            defences=[],
            is_unique=False,
            type_=CreatureType.CREATURE,
            actions_left=1,
            active_status=[CardEffect.NAPRAVLENNY_UDAR],
            description='',
            curr_fishka=0,
            max_fishka=0,
            can_tap_for_fishka=False,
            exp_in_def=0,
            exp_in_off=0
        )
        # self.add_default_abilities()
        self._update_abilities()
        self.player = player
        self.loc = location
        self.gui = gui
        self.upped = False

    def _update_abilities(self):
        self.a0 = SimpleCardAction(a_type=ActionTypes.ATAKA, damage=self.attack, range_min=1, range_max=1,
                                   txt=f'Атака {self.attack[0]}-{self.attack[1]}-{self.attack[2]}',
                                   ranged=False, state_of_action=[GameStates.MAIN_PHASE],
                                   callback=self.a1_cb, condition=Condition.ATTACKING)
        self.abilities.append(self.a0)
        a1 = DefenceAction(a_type=ActionTypes.ZASCHITA, active=True)
        self.abilities.insert(1, a1)
        self.defence_action = a1
        self.a2 = TriggerBasedCardAction(txt='Нелёгкий выбор защищающегося', recieve_inc=True,
                                    callback=self.a2_cb, condition=Condition.PRI_ATAKE, display=False)
        self.abilities.append(self.a2)


    def a2_cb(self, target):
        if not target.tapped:
            a21 = SimpleCardAction(a_type=ActionTypes.VOZDEISTVIE, damage=2, range_min=1, range_max=1,
                                       txt=f'2 урона', #target=target,
                                       ranged=False, state_of_action=[GameStates.MAIN_PHASE])
            a22 = SimpleCardAction(a_type=ActionTypes.TAP, damage=0, range_min=1, range_max=6,
                                 txt='Закрыть атакуемого', #target=target,
                                 ranged=False, state_of_action=[GameStates.MAIN_PHASE])
            a21_action = partial(self.a_action, a22, target, 0)
            a22_action = partial(self.a_action, a21, target, 0)
            pp = PopupAction(options=['Закрыться', 'Получить два урона'], action_list=[a21_action, a22_action],
                             a_type=ActionTypes.POPUP, txt='Закрыться?', show_to=(3-int(self.player)))
            self.gui.start_stack_action(pp, self, self, 0, force=1)
            self.gui.process_stack()
            # self.gui.backend.passed_1 = True
            # self.gui.backend.passed_2 = True

    def a_action(self, a, target, state, *args):
        self.gui.timer_ability.unbind(on_complete=self.gui.press_1)
        self.gui.start_stack_action(a, self, target, state, force=1)
        self.gui.process_stack()

    def a1_cb(self, victim):
        if self.upped:
            self.attack = self.attack[0] - 1, self.attack[1] - 1, self.attack[2] - 1
            self.upped = False
            self.a0.damage = self.attack
        if victim.tapped:
            self.attack = self.attack[0]+1, self.attack[1]+1, self.attack[2]+1
            self.upped = True
            self.a0.damage = self.attack
