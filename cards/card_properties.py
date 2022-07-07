import enum

@enum.unique
class ActionTypes(enum.Enum):

    ATAKA = 0
    RAZRYAD = 1
    ZAKLINANIE = 2
    VOZDEISTVIE = 3
    VYSTREL = 4
    METANIE = 5


class SimpleCardAction:

    def __init__(self, a_type: ActionTypes, damage: int, range: int, txt: str):
        self.a_type = a_type
        self.damage = damage
        self.range = range
        self.txt = txt

    def __str__(self):
        return self.txt
