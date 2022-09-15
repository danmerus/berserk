from cards.card import Card
from cards.card_properties import *
from game_properties import GameStates

class Gnom_basaarg_1(Card):

    def __init__(self, player=1, location=0, gui=None, *args):
        super().__init__(
            life=10,
            move=1,
            attack=(2, 3, 4),
            name='Гном-басаарг',
            vypusk=GameSet.VOYNA_STIHIY,
            color=CardColor.GORY,
            rarity=Rarity.COMMON,
            pic='data/cards/Gnom_basaarg_1.jpg',
            cost=(0, 7),  # gold, silver,
            defences=[],
            is_unique=False,
            type_=CreatureType.CREATURE,
            card_class=CardClass.GNOME,
            actions_left=1,
            active_status=[],
            description='',
            curr_fishka=0,
            max_fishka=0,
            exp_in_off=1,
            can_tap_for_fishka=False
        )

        self.add_default_abilities()
        self._update_abilities()
        self.player = player
        self.loc = location
        self.gui = gui
        self.stroy_in = self.stroy_in_cb
        self.stroy_out = self.stroy_out_cb

    def _update_abilities(self):  # txt max length 17
        a1 = TriggerBasedCardAction(txt='Атаковать закрытое существо противника в начале своей главной фазы',
                                    callback=self.a1_cb, condition=Condition.START_MAIN_PHASE, display=False)
        self.abilities.append(a1)
        a1.check = self.a2_check
        a2 = TriggerBasedCardAction(txt='Атаковать закрытое существо противника при передвижении',
                                    callback=self.a1_cb, condition=Condition.ON_SELF_MOVING, display=False)
        a2.check = self.a2_check
        self.abilities.append(a2)
        a3 = TriggerBasedCardAction(txt='Атаковать закрытое существо противника при его внезапном закрытии',
                                    callback=self.a1_cb, condition=Condition.ON_CREATURE_TAP, display=False)
        a3.check = self.a2_check
        self.abilities.append(a3)

    def a2_check(self):
        adj = self.gui.board.get_adjacent_cells(self.loc, range_=1)
        closed_enemy = [x for x in adj if self.gui.board.game_board[x] != 0]
        closed_enemy = [self.gui.board.game_board[x] for x in closed_enemy if
                        self.gui.board.game_board[x].tapped and self.gui.board.game_board[
                            x].player != self.player]
        return len(closed_enemy) > 0


    def a1_cb(self, cause):
        if cause and cause != 'zashita':
            adj = self.gui.board.get_adjacent_cells(self.loc, range_=1)
            closed_enemy = [x for x in adj if self.gui.board.game_board[x] != 0]
            closed_enemy = [self.gui.board.game_board[x] for x in closed_enemy if self.gui.board.game_board[x].tapped and self.gui.board.game_board[x].player != self.player]
            a = SimpleCardAction(a_type=ActionTypes.ATAKA, damage=(self.attack[0]+1, self.attack[1]+1, self.attack[2]+1),
                                      range_min=1, range_max=1, can_be_redirected=False, target=closed_enemy,
                                      txt=f'Атака {self.attack[0]+1}-{self.attack[1]+1}-{self.attack[2]+1}',
                                      ranged=False, state_of_action=[GameStates.MAIN_PHASE])
            if closed_enemy and self.actions_left > 0:
                self.gui.ability_clicked_forced(a, self, self.player)

    def stroy_in_cb(self):
        self.in_stroy = True
        self.attack = self.attack[0]+1, self.attack[1]+1, self.attack[2]+1
        self.default_attack.damage = self.attack
        self.default_attack.txt = f'Атака {self.attack[0]}-{self.attack[1]}-{self.attack[2]}'
        # self.add_default_abilities()
        # self._update_abilities()

    def stroy_out_cb(self):
        self.in_stroy = False
        self.attack = self.attack[0]-1, self.attack[1]-1, self.attack[2]-1
        self.default_attack.damage = self.attack
        self.default_attack.txt = f'Атака {self.attack[0]}-{self.attack[1]}-{self.attack[2]}'
        # self.add_default_abilities()
        # self._update_abilities()
