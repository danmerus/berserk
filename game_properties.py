import enum

@enum.unique
class GameStates(enum.Enum):

    VSKRYTIE = 0
    BATTLE_START = 1
    AVANGARD = 2
    START_PHASE = 3
    OPENING_PHASE = 4
    MAIN_PHASE = 5
    MAIN_CHOOSE = 5.1
    MAIN_MOVE = 5.2
    MAIN_ACTION = 5.3
    END_PHASE = 6
