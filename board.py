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

    def remove_card(self, card):
        if card in self.game_board:
            ix = self.game_board.index(card)
            self.game_board[ix] = 0

    def get_adjacent_cells_no_diag(self, no):
        pre = [no+6, no-6]
        if no not in [5, 11, 17, 23, 29]:
            pre.append(no+1)
        if no not in [0, 6, 12, 18, 24]:
            pre.append(no-1)
        return [x for x in pre if 30 > x >= 0]

    def get_adjacent_cells(self, no, range_=1):
        traverse = [no]
        while range_ > 0:
            temp = set()
            for el in traverse:
                ret = {el+6, el-6}
                if el not in [5, 11, 17, 23, 29]:
                    ret.add(el+1)
                    ret.add(el-5)
                    ret.add(el+7)
                if el not in [0, 6, 12, 18, 24]:
                    ret.add(el-1)
                    ret.add(el-7)
                    ret.add(el+5)
                temp.update(ret)
            traverse = [x for x in temp if 30 > x >= 0]
            range_ -= 1
        if no in traverse:
            traverse.remove(no)
        return traverse

    def get_available_target_cards(self, card_pos_no, range_):
        all_cells = self.get_adjacent_cells(card_pos_no, range_)
        return [x for x in all_cells if self.game_board[x] != 0]


    def get_available_moves(self, card):
        pos = self.game_board.index(card)
        moves_pre = self.get_adjacent_cells_no_diag(pos)
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


# b = Board()
# print(b.get_adjacent_cells(0, range_=4))
# print(b.game_board)