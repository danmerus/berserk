import enum

@enum.unique
class GameStates(enum.Enum):

    VSKRYTIE = 0
    BATTLE_START = 1
    AVANGARD = 2
    START_PHASE = 3
    OPENING_PHASE = 4
    MAIN_PHASE = 5
    # MAIN_CHOOSE = 5.1
    # MAIN_MOVE = 5.2
    # MAIN_ACTION = 5.3
    END_PHASE = 6
    def next(self):
        cls = self.__class__
        members = list(cls)
        index = members.index(self) + 1
        if index >= len(members):
            index = 0
        return members[index]

    def next_after_start(self):
        cls = self.__class__
        members = list(cls)
        index = members.index(self) + 1
        if index >= len(members):
            index = 3
        return members[index]

state_to_str = {
    GameStates.VSKRYTIE: 'Вскрытие',
    GameStates.BATTLE_START: 'Начало боя',
    GameStates.AVANGARD: 'Авангард',
    GameStates.START_PHASE: 'Начальная фаза',
    GameStates.OPENING_PHASE: 'Открытие',
    GameStates.MAIN_PHASE: 'Главная фаза',
    GameStates.END_PHASE: 'Заключительная фаза'
}

# k=GameStates.OPENING_PHASE
# print(state_to_str[k])