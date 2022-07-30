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
    EXTRA_LIFE = 10
    MAG_UDAR = 11
    MOVEMENT = 12
    OTHER = 13

@enum.unique
class CreatureType(enum.Enum):
    CREATURE = 1
    FLYER = 2
    ARTIFACT = 3
    LAND = 4

@enum.unique
class CardEffect(enum.Enum):
    NAPRAVLENNY_UDAR = 1

@enum.unique
class Condition(enum.Enum):
    ANYCREATUREDEATH = 0
    ATTACKING = 1

class DefenceAction:

    def __init__(self, a_type, active: bool):
        self.a_type = a_type
        self.txt = 'Защитить'
        self.fight_with = None
        self.active = active
        self.state_of_action = [GameStates.MAIN_PHASE]
        self.isinstant = True

    def __str__(self):
        return self.txt

class DefaultMovementAction:
    def __init__(self, move=None):
        self.a_type = ActionTypes.MOVEMENT
        self.move = move
        self.isinstant = False
        self.display = False
       # self.txt = ''


class TriggerBasedCardAction:

    def __init__(self, txt: str, callback, condition: Condition, display: bool):
        self.txt = txt
        self.callback = callback
        self.condition = condition
        self.display = display
        self.isinstant = False

    def __str__(self):
        return self.txt

class TapToHitFlyerAction:
    def __init__(self):
        self.a_type = ActionTypes.OTHER
        self.txt = 'Удар по летающему'
        self.isinstant = False
        self.display = True
        self.state_of_action = [GameStates.MAIN_PHASE]

    def __str__(self):
        return self.txt

class IncreaseFishkaAction:
    def __init__(self, txt: str, state_of_action: [GameStates]):
        self.a_type = ActionTypes.FISHKA
        self.txt = txt
        self.state_of_action = state_of_action
        self.isinstant = False

    def __str__(self):
        return self.txt

class SimpleCardAction:

    def __init__(self, a_type: ActionTypes, damage, range_min: int, range_max: int, txt: str, ranged: bool,
                 state_of_action: [GameStates], isinstant=False, targets=None, callback=None, condition=None):
        self.a_type = a_type
        self.damage = damage
        self.range_min = range_min
        self.range_max = range_max
        self.txt = txt
        self.ranged = ranged
        self.state_of_action = state_of_action
        self.isinstant = isinstant
        self.targets = targets
        self.tap_target = False
        self.callback = callback
        self.condition = condition

    def __str__(self):
        return self.txt

class MultipleCardAction():

    def __init__(self, a_type: ActionTypes, txt: str, ranged: bool, state_of_action: [GameStates], 
                 target_callbacks, action_list, isinstant=False):
        self.action_list = action_list
        self.state_of_action = state_of_action
        self.ranged = ranged
        self.txt = txt
        self.a_type = a_type
        self.target_callbacks = target_callbacks
        self.isinstant = isinstant

    def __str__(self):
        return self.txt


class FishkaCardAction(SimpleCardAction):

    def __init__(self, a_type: ActionTypes, damage, range_min: int, range_max: int, txt: str, ranged: bool, cost_fishka,
                 state_of_action: [GameStates], isinstant=False, targets=None):
        super().__init__(a_type, damage, range_min, range_max, txt, ranged, state_of_action)
        self.cost_fishka = cost_fishka
        self.isinstant = isinstant
        self.targets = targets

    def __str__(self):
        return self.txt
