import enum
from game_properties import GameStates

@enum.unique
class ActionTypes(enum.Enum):

    ATAKA = 0
    RAZRYAD = 1
    ZAKLINANIE = 2
    VOZDEISTVIE = 3
    VYSTREL = 4
    METANIE = 5

@enum.unique
class CreatureType(enum.Enum):
    CREATURE = 1
    FLYER = 2
    ARTIFACT = 3
    LAND = 4

class SimpleCardAction:

    def __init__(self, a_type: ActionTypes, damage, range_min: int, range_max: int, txt: str, ranged: bool,
                 state_of_action: GameStates):
        self.a_type = a_type
        self.damage = damage
        self.range_min = range_min
        self.range_max = range_max
        self.txt = txt
        self.range = ranged
        self.state_of_action = state_of_action

    def __str__(self):
        return self.txt
