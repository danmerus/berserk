from cards.card import Card
from cards.card_properties import ActionTypes, SimpleCardAction

class C1():

    def __init__(self, player, location):
        super(C1, self).__init__()
        self.pic = 'data/cards/c1.jpg'
        self.life = 8
        self.move = 1
        self.cost = 8, 0  # gold, silver
        self.attack = 2, 2, 3
        self.abilities = []
        self.defences = [ActionTypes.RAZRYAD]
        self.is_unique = False
        self.curr_life = self.life
        self.curr_moves = self.move
        self.actions = 1
        self._update_abilities()

        self.player = player
        self.loc = location  # -1 for flying, -2 for symbiots(??), -3 graveyard

    def _update_abilities(self):
        a1 = SimpleCardAction(a_type=ActionTypes.RAZRYAD, damage=2, range=6, txt='Разряд на 2')  # max length 17
        self.abilities.append(a1)


