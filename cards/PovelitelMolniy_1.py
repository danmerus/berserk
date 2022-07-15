from cards.card import Card
from cards.card_properties import ActionTypes, SimpleCardAction, CreatureType
from game_properties import GameStates

class PovelitelMolniy_1(Card):

    def __init__(self, player, location):
        super().__init__()
        self.name = 'Повелитель молний'
        self.vypusk = 'Война стихий'
        self.color = 'Горы'
        self.pic = 'data/cards/PovelitelMolniy_1.jpg'
        self.life = 8
        self.move = 1
        self.cost = 8, 0  # gold, silver
        self.attack = 5, 2, 3
        self.abilities = []
        self.defences = [ActionTypes.RAZRYAD]
        self.is_unique = False
        self.curr_life = self.life
        self.curr_moves = self.move
        self.type = CreatureType.CREATURE
        self.actions_left = 1

        self._update_abilities()

        self.player = player
        self.loc = location  # -1 for flying, -2 for symbiots(??), -3 graveyard

    def _update_abilities(self): # txt max length 17
        a0 = SimpleCardAction(a_type=ActionTypes.ATAKA, damage=self.attack, range_min=1, range_max=1,
                              txt=f'Атака {self.attack[0]}-{self.attack[1]}-{self.attack[2]}',
                              ranged=True, state_of_action=GameStates.MAIN_PHASE)
        self.abilities.append(a0)
        a1 = SimpleCardAction(a_type=ActionTypes.RAZRYAD, damage=2, range_min=1, range_max=6, txt='Разряд на 2',
                              ranged=True, state_of_action=GameStates.MAIN_PHASE)
        self.abilities.append(a1)


