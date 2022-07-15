from cards.card import Card
from cards.card_properties import ActionTypes, SimpleCardAction, CreatureType
from game_properties import GameStates

class Draks_1(Card):

    def __init__(self, player, location):
        super().__init__(
            life=5,
            move=0,
            attack=(1, 1, 2),
            name='Дракс',
            vypusk='Война стихий',
            color='Лес',
            pic='data/cards/Draks_1.jpg',
            cost=(0, 3),  # gold, silver,
            defences=[],
            is_unique=True,
            type_=CreatureType.FLYER,
            actions_left=1,
            active_status=[]
        )
        self.add_attack_ability()
        self._update_abilities()
        self.player = player
        self.loc = location  # -1 for flying, -2 for symbiots(??), -3 graveyard

    def _update_abilities(self):
        pass

