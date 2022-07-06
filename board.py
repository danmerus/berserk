import numpy as np

class Board():

    def __init__(self):
        self.game_board = np.zeros(30)
        self.fly1 = []
        self.fly2 = []
        self.symb1 = []
        self.symb2 = []
        self.city1 = []
        self.city2 = []
        self.grave1 = []
        self.grave2 = []
        self.deck1 = []
        self.deck2 = []

    def populate_board(self, cards):
        for i, c in cards:
            if i >= 0 and i < 30:
                self.game_board[i] = c

    def get_state(self):
        return {i:getattr(self, i) for i in self.__dict__.keys() if i[:1] != '_'}

    def get_available_moves(self, card):
        return [1,2,29]


b = Board()
b.populate_board([(1, 1)])
#print(b.game_board)
#print(b.get_state())