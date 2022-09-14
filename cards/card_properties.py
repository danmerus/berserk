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
    DIE_ROLL = 13
    TRIGGER = 14
    OTRAVLENIE = 15
    UDAR_CHEREZ_RYAD = 16
    BLOCK = 17
    VOZROJDENIE = 18
    DESTRUCTION = 19
    POPUP = 20
    TAP = 21
    NET = 22
    DOBIVANIE = 23
    OSOBII_UDAR = 24
    PERERASPREDELENIE_RAN = 25
    OTHER = 26

ATTACK_LIST = [ActionTypes.VYSTREL, ActionTypes.RAZRYAD, ActionTypes.METANIE, ActionTypes.ATAKA, ActionTypes.MAG_UDAR,
               ActionTypes.UDAR_CHEREZ_RYAD, ActionTypes.UDAR_LETAUSHEGO, ActionTypes.OSOBII_UDAR]

@enum.unique
class CreatureType(enum.Enum):
    CREATURE = 1
    FLYER = 2
    ARTIFACT = 3
    LAND = 4

@enum.unique
class Rarity(enum.Enum):
    COMMON = 'частая'
    RARE = 'редкая'
    UNIQUE = 'ультраредкая'
    PROMO = 'промо'

@enum.unique
class CardColor(enum.Enum):
    NEUTRAL = 'нейтральная'
    GORY = 'горы'
    STEP = 'степь'
    BOLOTA = 'болота'
    LES = 'лес'
    TYMA = 'тьма'

@enum.unique
class CardClass(enum.Enum):
    GNOME = 'гном'
    ELF = 'эльф'

@enum.unique
class GameSet(enum.Enum):
    VOYNA_STIHIY = 'Война стихий'

@enum.unique
class CardEffect(enum.Enum):
    NAPRAVLENNY_UDAR = 1
    UDAR_CHEREZ_RYAD = 2
    REGEN = 3
    TRUPOEDSTVO = 4
    BESTELESNOE = 5
    OTRAVLEN = 6
    FLYER_MAGNET = 7
    NETTED = 8
    ORDA = 9

@enum.unique
class Condition(enum.Enum):
    ANYCREATUREDEATH = 0
    ATTACKING = 1
    ON_RECIEVING_RANGED_ATTACK = 2
    START_MAIN_PHASE = 3
    ON_SELF_MOVING = 4
    ON_DEFENCE_BEFORE_DICE = 5
    PRI_ATAKE = 6
    ON_TAKING_DAMAGE = 7
    ON_MAKING_DAMAGE_STAGE = 8

class DefenceAction:

    def __init__(self, a_type, active: bool):
        self.a_type = a_type
        self.txt = 'Защитить'
        self.fight_with = None
        self.active = active
        self.state_of_action = [GameStates.MAIN_PHASE]
        self.isinstant = True
        self.condition = None
        self.disabled = True
        self.marks_needed = 0

    def __str__(self):
        return self.txt


class DefaultMovementAction:
    def __init__(self, move=None):
        self.a_type = ActionTypes.MOVEMENT
        self.move = move
        self.isinstant = False
        self.display = False
        self.state_of_action = [GameStates.MAIN_PHASE]
        self.marks_needed = 1
        self.txt = 'Простое передвижение'
        self.take_board_cells = True


class TriggerBasedCardAction:

    def __init__(self, txt: str, callback, condition: Condition, display: bool, recieve_inc=False, recieve_all=False,
                 callback_prep=None, cleanup=None,
                 target=None, prep=None, actor=None, check=None, isinstant=False, repeat=False, impose=False, state_of_action=[]):
        self.txt = txt
        self.callback = callback
        self.condition = condition
        self.display = display
        self.isinstant = isinstant
        self.a_type = ActionTypes.TRIGGER
        self.recieve_inc = recieve_inc
        self.recieve_all = recieve_all
        self.tap_target = False
        self.disabled = True
        self.repeat = repeat
        self.check = check
        self.target = target
        self.cleanup = cleanup
        self.prep = prep
        self.actor = actor
        self.impose = impose
        self.marks_needed = 0
        self.state_of_action = state_of_action
        self.callback_prep = callback_prep

    def __str__(self):
        return self.txt

class BlockActionButton:
    def __init__(self, txt, condition):
        self.txt = txt
        self.tap_target = False
        self.rolls = []
        self.damage_make = 0
        self.damage_receive = 0
        self.a_type = ActionTypes.BLOCK
        self.txt = txt
        self.isinstant = False
        self.display = False
        self.state_of_action = [GameStates.MAIN_PHASE]
        self.tap_target = False
        self.condition = condition

    def __str__(self):
        return self.txt

class BlockAction:
    def __init__(self, to_block):
        self.a_type = ActionTypes.BLOCK
        self.txt = 'Заблокировать'
        self.isinstant = False
        self.display = False
        self.to_block = to_block
        self.state_of_action = [GameStates.MAIN_PHASE]
        self.tap_target = False
        self.marks_needed = 0

    def __str__(self):
        return self.txt


class TapToHitFlyerAction:
    def __init__(self):
        self.a_type = ActionTypes.OTHER
        self.txt = 'Удар по летающему'
        self.isinstant = False
        self.display = True
        self.state_of_action = [GameStates.MAIN_PHASE]
        self.marks_needed = 0

    def __str__(self):
        return self.txt

class IncreaseFishkaAction:
    def __init__(self, txt: str, state_of_action: [GameStates]):
        self.a_type = ActionTypes.FISHKA
        self.txt = txt
        self.state_of_action = state_of_action
        self.isinstant = False
        self.marks_needed = 0

    def __str__(self):
        return self.txt


class SimpleCardAction:

    def __init__(self, a_type: ActionTypes, damage, range_min: int, range_max: int, txt: str, ranged: bool,
                 state_of_action: [GameStates], isinstant=False, target=None, callback=None, condition=None, target_count=1,
                 on_complete=None,
                 reverse=False, target_restriction=[], can_be_redirected=True, display=True, multitarget=False, target_list=[], cellsorfieldlist=[]):
        self.a_type = a_type
        self.damage = damage
        self.range_min = range_min
        self.range_max = range_max
        self.txt = txt
        self.ranged = ranged
        self.state_of_action = state_of_action
        self.isinstant = isinstant
        self.targets = target
        self.tap_target = False
        self.multitarget = multitarget
        self.callback = callback
        self.condition = condition
        self.rolls = []
        self.cellsorfieldlist = cellsorfieldlist
        self.target_list = target_list
        self.damage_make = 0
        self.damage_receive = 0
        self.redirected = False
        self.reverse = reverse
        self.display = display
        self.target_count = target_count
        self.target_restriction = target_restriction
        self.can_be_redirected = can_be_redirected
        self.marks_needed = 1
        self.on_complete = on_complete

    def __str__(self):
        return self.txt

class SelectCardAction:

    def __init__(self, child_action, targets=None, range_min=0, range_max=0, ranged=False):
        self.child_action = child_action
        self.state_of_action = child_action.state_of_action
        self.a_type = child_action.a_type
        self.isinstant = child_action.isinstant
        self.targets = targets
        self.range_min = range_min
        self.range_max = range_max
        self.ranged = ranged
        self.marks_needed = 1

class MultipleCardAction:

    def __init__(self, a_type: ActionTypes, txt: str, ranged: bool, state_of_action: [GameStates], target_callbacks, action_list,
                 isinstant=False, take_all_targets=False, marks_needed=1,  target_list=[]):
        self.action_list = action_list
        self.state_of_action = state_of_action
        self.ranged = ranged
        self.txt = txt
        self.a_type = a_type
        self.target_callbacks = target_callbacks
        self.isinstant = isinstant
        self.take_all_targets = take_all_targets
        self.marks_needed = marks_needed
        self.target_list = target_list

    def __str__(self):
        return self.txt

class PopupAction:

    def __init__(self,  options, action_list, a_type=ActionTypes.POPUP, txt='', ranged=False, state_of_action=GameStates.MAIN_PHASE,
                  isinstant=False, show_to=1):
        self.action_list = action_list
        self.state_of_action = state_of_action
        self.ranged = ranged
        self.txt = txt
        self.a_type = a_type
        self.options = options
        self.isinstant = isinstant
        self.options = options
        self.show_to = show_to

    def __str__(self):
        return self.txt


class FishkaCardAction(SimpleCardAction):

    def __init__(self, a_type: ActionTypes, damage, range_min: int, range_max: int, txt: str, ranged: bool, cost_fishka,
                 state_of_action: [GameStates], isinstant=False, target=None, is_tapped=False, can_be_redirected=True,
                 multitarget=False, target_list=[], cellsorfieldlist=[]):
        super().__init__(a_type, damage, range_min, range_max, txt, ranged, state_of_action, can_be_redirected)
        self.cost_fishka = cost_fishka
        self.isinstant = isinstant
        self.targets = target
        self.is_tapped = is_tapped
        self.multitarget = multitarget
        self.target_list = target_list
        self.cellsorfieldlist = cellsorfieldlist

    def __str__(self):
        return self.txt

class LambdaCardAction():  #  ONLY for stage 1

    def __init__(self, func, a_type=None, isinstant=False):
        self.a_type = a_type
        self.state_of_action = []
        self.isinstant = isinstant
        self.func = func


class SelectTargetAction():

    def __init__(self, targets, a_type=None, isinstant=False):
        self.a_type = ActionTypes.OTHER
        self.state_of_action = []
        self.isinstant = isinstant
        self.targets = targets