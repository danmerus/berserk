from cards.card import Card
from cards.card_properties import *
from game_properties import GameStates

class Draks_1(Card):

    def __init__(self, player, location, gui):
        super().__init__(
            life=5,
            move=0,
            attack=(1, 1, 2),
            name='Дракс',
            vypusk='Война стихий',
            rarity = 'common',
            color='Лес',
            pic='data/cards/Draks_1.jpg',
            cost=(0, 3),  # gold, silver,
            defences=[],
            is_unique=True,
            type_=CreatureType.FLYER,
            actions_left=1,
            active_status=[CardEffect.NAPRAVLENNY_UDAR],
            description='Величайшие колдуны Лаара хмурят брови и крепче сжимают свои посохи при одном лишь упоминании о Драксах, чьей излюбленной пищей служит магия...',
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

