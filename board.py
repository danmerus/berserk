from itertools import chain
from cards.card_properties import *


class Board():

    def __init__(self):
        self.game_board = [0 for _ in range(30)]
        self.extra1 = []
        self.extra2 = []
        self.symb1 = []
        self.symb2 = []
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
        elif card in self.extra1:
            self.extra1.remove(card)
        elif card in self.extra1:
            self.extra1.remove(card)
        elif card in self.extra2:
            self.extra2.remove(card)
        elif card in self.symb1:
            self.symb1.remove(card)
        elif card in self.symb2:
            self.symb2.remove(card)

    def get_adjacent_with_stroy(self, no):
        out = []
        if self.game_board[no] != 0:
            player_ = self.game_board[no].player
            neigh = [self.game_board[x] for x in self.get_adjacent_cells_no_diag(no) if self.game_board[x] != 0]
            out = [x for x in neigh if x.stroy_in and x.player == player_]
        return out

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

    def get_adjacent_empty(self, card):
        candidates = self.get_adjacent_cells(card.loc, range_=1)
        return [x for x in candidates if self.game_board[x] == 0]

    def get_grave_elite(self, player):
        if player == 1:
            return [x for x in self.grave1 if x.cost[0] > 0]
        elif player == 2:
            return [x for x in self.grave2 if x.cost[0] > 0]
        else:
            return [x for x in self.grave1 if x.cost[0] > 0] +  [x for x in self.grave2 if x.cost[0] > 0]

    def get_grave_ryad(self, player):
        if player == 1:
            return [x for x in self.grave1 if x.cost[0] == 0]
        elif player == 2:
            return [x for x in self.grave2 if x.cost[0] == 0]
        else:
            return [x for x in self.grave2 if x.cost[0] == 0]+[x for x in self.grave1 if x.cost[0] == 0]
    def get_defenders(self, card, victim):
        candidates = []
        if card.player == victim.player:
            return []
        if victim.type_ == CreatureType.CREATURE and card.type_ == CreatureType.CREATURE:
            c1 = self.get_available_targets_ground(card.loc, range_=1)
            v1 = self.get_available_targets_ground(victim.loc, range_=1)
            candidates = set(c1).intersection(set(v1))
        elif (card.type_ == CreatureType.CREATURE or card.type_ == CreatureType.FLYER) and \
            victim.type_ == CreatureType.FLYER:
            if victim.player == 1:
                candidates = [x for x in self.extra1 if x != victim]
            else:
                candidates = [x for x in self.extra2 if x != victim]
        elif card.type_ == CreatureType.FLYER and victim.type_ == CreatureType.CREATURE:
            c1 = self.get_available_targets_ground(victim.loc, range_=1)
            if victim.player == 1:
                candidates = self.extra1
            else:
                candidates = self.extra2
            candidates = candidates + c1
        out = [x for x in candidates if not x.tapped]
        out = [x for x in out if x.can_defend]
        out = [x for x in out if x.player == victim.player]
        return out

    def get_all_cards_with_callback(self, condition):
        all_cards = self.get_all_cards()
        out = []
        for c in all_cards:
            for a in c.abilities:
                if isinstance(a, TriggerBasedCardAction) and a.condition == condition:
                    out.append((c, a))
        return out

    def cards_callback(self, card, condition):
        out = []
        for a in card.abilities:
            if isinstance(a, TriggerBasedCardAction) and a.condition == condition:
                out.append(a)
        return out

    def get_instants(self):
        all_cards = self.get_all_cards()
        out = []
        for c in all_cards:
            for a in c.abilities:
                if a.isinstant and not isinstance(a, DefenceAction):
                    out.append((c, a))
        return out

    def get_available_targets_ground(self, card_pos_no, range_):
        all_cells = self.get_adjacent_cells(card_pos_no, range_)
        return [self.game_board[x] for x in all_cells if self.game_board[x] != 0]

    def isinstant_card(self, card):
        for a in card.abilities:
            if a.isinstant and not a.a_type == ActionTypes.ZASCHITA:
                return True
        return False

    def get_flying_targets(self):
        extr1 = [x for x in self.extra1 if x.type_ != CreatureType.LAND]
        extr2 = [x for x in self.extra2 if x.type_ != CreatureType.LAND]
        out = list(chain(extr1, extr2))
        return out

    def get_ground_targets_min_max(self, card_pos_no, range_max, range_min, ability):
        if range_max > range_min:
            t1 = set(self.get_available_targets_ground(card_pos_no, range_max))
            t2 = set(self.get_available_targets_ground(card_pos_no, range_min))
            out = list(t1-t2)
            if ability.ranged:
                out.extend(self.get_flying_targets())
        elif range_max == range_min:
            out = self.get_available_targets_ground(card_pos_no, range_max)
        return out

    def get_available_targets_flyer(self, card):
        gr = [x for x in self.game_board if x != 0]
        extr1 = [x for x in self.extra1 if x.type_ != CreatureType.LAND]
        extr2 = [x for x in self.extra2 if x.type_ != CreatureType.LAND]
        out = list(chain(gr, self.symb1, self.symb2, extr1, extr2))
        out.remove(card)
        return out

    def get_flyer_magnets(self, player, enemy=False):
        all_card = self.get_all_cards()
        if enemy:
            return [c for c in all_card if CardEffect.FLYER_MAGNET in c.active_status and c.player != player]
        return [c for c in all_card if CardEffect.FLYER_MAGNET in c.active_status]

    def get_available_targets_uchr(self, card):
        no = card.loc
        candidates = [(no+1, no+2), (no-1, no-2), (no+6, no+12), (no-6, no-12)]
        if no in [0,6,12,24,1,7,13,25]:
            candidates = [(no+1, no+2), (no+6, no+12), (no-6, no-12)]
        if no in [4,10,16,22,28,5,11,17,23,29]:
            candidates = [(no-1, no-2), (no+6, no+12), (no-6, no-12)]
        out = []
        for over, c in candidates:
            if 30 > c >= 0:
                if self.game_board[over] == 0:
                    out.append(c)
                elif self.game_board[over].player == card.player:
                    out.append(c)
        outt = [x for x in out if self.game_board[x] != 0]
        return [self.game_board[x] for x in outt]


    def get_all_cards(self):
        gr = [x for x in self.game_board if x != 0]
        extr1 = [x for x in self.extra1 if x.type_]
        extr2 = [x for x in self.extra2 if x.type_]
        out = list(chain(gr, self.symb1, self.symb2, extr1, extr2))
        return out

    def get_available_moves(self, card):
        if card.tapped or card.type_ != CreatureType.CREATURE or card.curr_move <= 0 or card.gui.backend.curr_game_state != GameStates.MAIN_PHASE:
            return []
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

    def get_zone_count(self, attr):
        return len(getattr(self, attr))


# b = Board()
# print(b.get_adjacent_cells(0, range_=4))
# print(b.get_flyer_count('extra1'))