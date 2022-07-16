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
    UDAR_LETAUSHEGO = 6
    LECHENIE = 7
    ZASCHITA = 8
    FISHKA = 9
    OTHER = 10

@enum.unique
class CreatureType(enum.Enum):
    CREATURE = 1
    FLYER = 2
    ARTIFACT = 3
    LAND = 4

@enum.unique
class Condition(enum.Enum):
    ANYCREATUREDEATH = 0

class DefenceAction:

    def __init__(self, a_type, active: bool):
        self.a_type = a_type
        self.txt = 'Защитить'
        self.fight_with = None
        self.active = active
        self.state_of_action = GameStates.MAIN_PHASE

    def __str__(self):
        return self.txt

class TriggerBasedCardAction:

    def __init__(self, txt: str, callback, condition: Condition, display: bool):
        self.txt = txt
        self.callback = callback
        self.condition = condition
        self.display = display

    def __str__(self):
        return self.txt


class IncreaseFishkaAction:
    def __init__(self, txt: str, state_of_action: GameStates):
        self.a_type = ActionTypes.FISHKA
        self.txt = txt
        self.state_of_action = state_of_action
        self.isinstant = False

    def __str__(self):
        return self.txt

class SimpleCardAction:

    def __init__(self, a_type: ActionTypes, damage, range_min: int, range_max: int, txt: str, ranged: bool,
                 state_of_action: GameStates, isinstant=False, targets=None):
        self.a_type = a_type
        self.damage = damage
        self.range_min = range_min
        self.range_max = range_max
        self.txt = txt
        self.ranged = ranged
        self.state_of_action = state_of_action
        self.isinstant = isinstant
        self.targets = targets

    def __str__(self):
        return self.txt


class FishkaCardAction(SimpleCardAction):

    def __init__(self, a_type: ActionTypes, damage, range_min: int, range_max: int, txt: str, ranged: bool, cost_fishka,
                 state_of_action: GameStates, isinstant=False, targets=None):
        super().__init__(a_type, damage, range_min, range_max, txt, ranged, state_of_action)
        self.cost_fishka = cost_fishka
        self.isinstant = isinstant
        self.targets = targets

    def __str__(self):
        return self.txt
