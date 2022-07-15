from cards.card import Card
from cards.card_properties import ActionTypes, SimpleCardAction, CreatureType
from game_properties import GameStates

class Draks_1(Card):

    def __init__(self, player, location):
        super().__init__()
        self.name = 'Дракс'
        self.vypusk = 'Война стихий'
        self.color = 'Лес'
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

        # self.actions = 1
        # self.is_open = True
        # self.has_made_action = False
        # self.number_of_available_attacks = 1
        # self.tapped = False

        self._update_abilities()

        self.player = player
        self.loc = location  # -1 for flying, -2 for symbiots(??), -3 graveyard

    def _update_abilities(self):
        a0 = SimpleCardAction(a_type=ActionTypes.ATAKA, damage=self.attack, range_min=1, range_max=1,
                              txt=f'Атака {self.attack[0]}-{self.attack[1]}-{self.attack[2]}',
                              ranged=True, state_of_action=GameStates.MAIN_PHASE)
        self.abilities.append(a0)

