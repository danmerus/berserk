from cards.card import Card
from cards.card_properties import ActionTypes, SimpleCardAction, CreatureType

class Draks_1(Card):

    def __init__(self, player, location):
        super().__init__()
        self.name = 'Дракс'
        self.vypusk = 'Война стихий'
        self.pic = 'data/cards/Draks_1.jpg'
        self.life = 5
        self.move = -1 # -1=flyer, -2=symbiont
        self.cost = 0, 3  # gold, silver
        self.attack = 1, 1, 2
        self.abilities = []
        self.defences = []
        self.is_unique = True
        self.curr_life = self.life
        self.curr_moves = self.move
        self.type = CreatureType.FLYER
        self.actions_left = 1

        self._update_abilities()

        self.player = player
        self.loc = location  # -1 for flying, -2 for symbiots(??), -3 graveyard

    def _update_abilities(self):
        pass

