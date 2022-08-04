from cards.card import Card
from cards.card_properties import *
from game_properties import GameStates

class Korpit_1(Card):

    def __init__(self, player=1, location=0, gui=None):
        super().__init__(
            life=6,
            move=0,
            attack=(1, 2, 2),
            name='Корпит',
            vypusk=GameSet.VOYNA_STIHIY,
            rarity=Rarity.COMMON,
            color=CardColor.LES,
            pic='data/cards/Korpit_1.jpg',
            cost=(0, 5),  # gold, silver,
            defences=[],
            is_unique=False,
            type_=CreatureType.FLYER,
            actions_left=1,
            active_status=[CardEffect.NAPRAVLENNY_UDAR, CardEffect.TRUPOEDSTVO],
            description='Маленькие пожиратели падали, они вечно кружатся над полем боя, надеясь на поживу.',
            curr_fishka=0,
            max_fishka=0,
            can_tap_for_fishka=False
        )
     #   self.add_default_abilities()
        self._update_abilities()
        self.player = player
        self.loc = location
        self.gui = gui
        self.upped = False

    def _update_abilities(self):
        self.a0 = SimpleCardAction(a_type=ActionTypes.UDAR_LETAUSHEGO, damage=self.attack, range_min=1, range_max=1,
                              txt=f'Атака {self.attack[0]}-{self.attack[1]}-{self.attack[2]}',
                              ranged=False, state_of_action=[GameStates.MAIN_PHASE],
                              callback=self.a1_cb, condition=Condition.ATTACKING)
        self.abilities.append(self.a0)
        a1 = DefenceAction(a_type=ActionTypes.ZASCHITA, active=True)
        self.abilities.insert(1, a1)
        self.defence_action = a1

    def a1_cb(self, victim):
        if self.upped:
            self.attack = self.attack[0] - 1, self.attack[1] - 1, self.attack[2] - 1
            self.upped = False
        for a in victim.abilities:
            if a.a_type in [ActionTypes.RAZRYAD, ActionTypes.ZAKLINANIE, ActionTypes.MAG_UDAR]:
                self.attack = self.attack[0]+1, self.attack[1]+1, self.attack[2]+1
                self.upped = True
                self.a0.damage = self.attack
                return

