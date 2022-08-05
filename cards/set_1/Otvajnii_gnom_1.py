from cards.card import Card
from cards.card_properties import *
from game_properties import GameStates

class Otvajnii_gnom_1(Card):

    def __init__(self, player=1, location=0, gui=None):
        super().__init__(
            life=6,
            move=1,
            attack=(1, 1, 2),
            name='Овражный Гном',
            vypusk=GameSet.VOYNA_STIHIY,
            rarity=Rarity.COMMON,
            color=CardColor.GORY,
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
            exp_in_def=1,
            exp_in_off=1
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

        a2 = TriggerBasedCardAction(txt='Нелёгкий выбор защищающегося',
                                    callback=self.a2_cb, condition=Condition.PRI_ATAKE, display=False)
        self.abilities.append(a2)


    def a2_cb(self):
        pp = PopupAction(['Закрыться', 'Получить два урона'], [], a_type=ActionTypes.POPUP, txt='Закрыться?')
        self.gui.perform_card_action(pp, self, None, 0)

    def a1_cb(self, victim):
        if self.upped:
            self.attack = self.attack[0] - 1, self.attack[1] - 1, self.attack[2] - 1
            self.upped = False
            self.a0.damage = self.attack
        if victim.tapped:
            self.attack = self.attack[0]+1, self.attack[1]+1, self.attack[2]+1
            self.upped = True
            self.a0.damage = self.attack
