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
        self.add_default_abilities()
        self._update_abilities()
        self.player = player
        self.loc = location
        self.gui = gui

    def _update_abilities(self):
        pass
