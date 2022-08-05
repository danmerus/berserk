from cards.card import Card
from cards.card_properties import *
from game_properties import GameStates

class Ledyanoy_ohotnik_1(Card):

    def __init__(self, player=1, location=0, gui=None):
        super().__init__(
            life=7,
            move=2,
            attack=(1, 2, 3),
            name='Ледяной охотник',
            vypusk=GameSet.VOYNA_STIHIY,
            rarity=Rarity.COMMON,
            color=CardColor.GORY,
            pic='data/cards/Ledyanoy_ohotnik_1.jpg',
            cost=(5, 0),  # gold, silver,
            defences=[],
            is_unique=False,
            type_=CreatureType.CREATURE,
            actions_left=1,
            active_status=[CardEffect.UDAR_CHEREZ_RYAD],
            description='Охотники торосов Йора издревле славились своими длинными копьями, сделанными из ребер выброшенных на берег китов.',
            curr_fishka=0,
            max_fishka=0,
            can_tap_for_fishka=False,
        )
        self.uchr_damage = (2, 3, 4)
        self.add_default_abilities()
        self._update_abilities()
        self.player = player
        self.loc = location
        self.gui = gui

    def _update_abilities(self):
        a1 = SimpleCardAction(a_type=ActionTypes.UDAR_CHEREZ_RYAD, damage=self.uchr_damage, range_min=1, range_max=1,
                              txt=f'Удар через ряд {self.uchr_damage[0]}-{self.uchr_damage[1]}-{self.uchr_damage[2]}',
                              ranged=False, state_of_action=[GameStates.MAIN_PHASE])
        self.abilities.append(a1)
