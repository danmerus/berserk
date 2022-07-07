import numpy as np

class Board():

    def __init__(self):
        self.game_board = [0 for _ in range(30)]
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
        for c in cards:
            if c.loc >= 0 and c.loc < 30:
                self.game_board[c.loc] = c
    def get_adjacent_cells(self, no):
        pre = [no+6, no-6, no+1, no-1]
        return [x for x in pre if 30 > x >= 0]
    def get_available_moves(self, card):
        pos = self.game_board.index(card)
        moves_pre = self.get_adjacent_cells(pos)
        out = []
        for move in moves_pre:
            if self.game_board[move] == 0:
                out.append(move)
        return out

    def update_board(self, prev, now, card):
        if self.game_board[now] != 0:
            raise ValueError('Card present on: ', now)
        else:
            self.game_board[now] = card
            self.game_board[prev] = 0

    def get_state(self):
        return {i:getattr(self, i) for i in self.__dict__.keys() if i[:1] != '_'}


#b = Board()
#print(b.get_adjacent_cells(15))
# print(b.game_board)