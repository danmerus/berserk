from cards.card import Card
from cards.card_properties import *
from game_properties import GameStates

class Hobgoblin_1(Card):

    def __init__(self, player=1, location=0, gui=None):
        super().__init__(
            life=18,
            move=1,
            attack=(3, 4, 5),
            name='Хобгоблин',
            vypusk=GameSet.VOYNA_STIHIY,
            rarity=Rarity.COMMON,
            color=CardColor.LES,
            pic='data/cards/Hobgoblin_1.jpg',
            cost=(8, 0),  # gold, silver,
            defences=[ActionTypes.OTRAVLENIE],
            is_unique=False,
            type_=CreatureType.CREATURE,
            actions_left=1,
            active_status=[CardEffect.NAPRAVLENNY_UDAR],
            description='В незапамятные времена некоторые племена гоблинов были вынуждены покинуть родные болота и поселиться в негостеприимных лесах Кронга...',
            curr_fishka=0,
            max_fishka=0,
            can_tap_for_fishka=False,
        )
        self.add_default_abilities()
        self._update_abilities()
        self.player = player
        self.loc = location
        self.gui = gui

    def _update_abilities(self):
        pass

