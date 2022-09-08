from cards.card import Card
from cards.card_properties import *
from game_properties import GameStates

class Ar_gull_1(Card):

    def __init__(self, player=1, location=0, gui=None, *args):
        super().__init__(
            life=8,
            move=1,
            attack=(1, 2, 2),
            name='Ар-Гулль',
            vypusk=GameSet.VOYNA_STIHIY,
            color=CardColor.GORY,
            rarity=Rarity.COMMON,
            pic='data/cards/Ar_gull_1.jpg',
            cost=(5, 0),  # gold, silver,
            defences=[],
            is_unique=False,
            type_=CreatureType.CREATURE,
            actions_left=1,
            active_status=[],
            description='',
            curr_fishka=1,
            max_fishka=4,
            can_tap_for_fishka=True
        )

        self.add_default_abilities()
        self._update_abilities()
        self.player = player
        self.loc = location
        self.gui = gui

    def _update_abilities(self):  # txt max length 17
        a1 = FishkaCardAction(a_type=ActionTypes.RAZRYAD, damage=self.a1_dmg, range_min=2, range_max=6, txt='Разряд на 2X',
                              ranged=True, state_of_action=[GameStates.MAIN_PHASE], cost_fishka=self.a1_cost)
        self.abilities.append(a1)
        a2 = SimpleCardAction(a_type=ActionTypes.LECHENIE, damage=2, range_min=0, range_max=0,
                              txt='Излечиться на 2', target='self',
                              ranged=True, state_of_action=[GameStates.MAIN_PHASE])
        self.abilities.append(a2)

    def a1_dmg(self):
        return self.curr_fishka*2

    def a1_cost(self):
        return self.curr_fishka
