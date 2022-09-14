from cards.card import Card
from cards.card_properties import *
from game_properties import GameStates
from functools import partial

class Necromant_1(Card):

    def __init__(self, player=1, location=0, gui=None, *args):
        super().__init__(
            life=8,
            move=1,
            attack=(1, 2, 3),
            name='Некромант',
            vypusk=GameSet.VOYNA_STIHIY,
            color=CardColor.GORY,
            rarity=Rarity.COMMON,
            pic='data/cards/Necromant_1.jpg',
            cost=(0, 5),  # gold, silver,
            defences=[],
            is_unique=False,
            type_=CreatureType.CREATURE,
            actions_left=1,
            active_status=[],
            description='',
            curr_fishka=0,
            max_fishka=99,
            can_tap_for_fishka=True
        )

        self.gui = gui
        self.player = player
        self.loc = location
        self.add_default_abilities()
        self._update_abilities()

    def _update_abilities(self):  # txt max length 17
        a2 = FishkaCardAction(a_type=ActionTypes.VOZROJDENIE, damage=0, range_min=1, range_max=6,
                               txt='Возрождение рядового существа', multitarget=True,
                               target_list=[partial(self.gui.board.get_grave_ryad, 3), partial(self.gui.board.get_adjacent_empty, self)],
                               target=partial(self.gui.board.get_grave_ryad, 3), cellsorfieldlist=['card', 'cell'],
                               ranged=False, state_of_action=[GameStates.MAIN_PHASE], cost_fishka=3, is_tapped=True)
        # a2.take_board_cells = True
        a2.marks_needed = 2
        self.abilities.append(a2)

        a3 = FishkaCardAction(a_type=ActionTypes.VOZROJDENIE, damage=0, range_min=1, range_max=6,
                               txt='Возрождение элитного существа', multitarget=True,
                               target_list=[partial(self.gui.board.get_grave_elite, 3), partial(self.gui.board.get_adjacent_empty, self)],
                               target=partial(self.gui.board.get_grave_elite, 3), cellsorfieldlist=['card', 'cell'],
                               ranged=False, state_of_action=[GameStates.MAIN_PHASE], cost_fishka=4, is_tapped=True)
        # a3.take_board_cells = True
        a3.marks_needed = 2
        self.abilities.append(a3)

        a1 = SimpleCardAction(a_type=ActionTypes.RAZRYAD, damage=1, range_min=2, range_max=6, txt='Разряд на 1',
                              ranged=True, state_of_action=[GameStates.MAIN_PHASE])
        self.abilities.append(a1)

    def a2_t_cb(self):
        self.gui.grave_1_func(None)
        self.gui.grave_2_func(None)
        return self.gui.board.get_grave_elite(3)

    def a3_t_cb(self):
        self.gui.grave_1_func(None)
        self.gui.grave_2_func(None)
        return self.gui.board.get_grave_ryad(3)

