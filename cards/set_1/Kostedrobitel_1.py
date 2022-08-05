from cards.card import Card
from cards.card_properties import *
from game_properties import GameStates

class Kostedrobitel_1(Card):

    def __init__(self, player=1, location=0, gui=None):
        super().__init__(
            life=12,
            move=1,
            attack=(3, 5, 7),
            name='Костедробитель',
            vypusk=GameSet.VOYNA_STIHIY,
            rarity=Rarity.COMMON,
            color=CardColor.GORY,
            pic='data/cards/Kostedrobitel_1.jpg',
            cost=(7, 0),  # gold, silver,
            defences=[],
            is_unique=False,
            type_=CreatureType.CREATURE,
            actions_left=1,
            active_status=[],
            description='Однажды монахи Тарга выкрали Рунный камень из пещер Ханеранга. Горные варвары не стали штурмовать неприступные ворота Тул-Бараг. Они пробились внутрь прямо через стену.',
            curr_fishka=0,
            max_fishka=0,
            can_tap_for_fishka=False,
            exp_in_def=1,
            exp_in_off=1
        )
        self.add_default_abilities()
        self._update_abilities()
        self.player = player
        self.loc = location
        self.gui = gui

    def _update_abilities(self):
        pass
