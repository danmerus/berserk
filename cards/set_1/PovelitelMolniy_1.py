from cards.card import Card
from cards.card_properties import *
from game_properties import GameStates

class PovelitelMolniy_1(Card):

    def __init__(self, player=1, location=0, gui=None, *args):
        super().__init__(
            life=8,
            move=1,
            attack=(2, 2, 3),
            name='Повелитель молний',
            vypusk=GameSet.VOYNA_STIHIY,
            color=CardColor.GORY,
            rarity=Rarity.RARE,
            pic='data/cards/PovelitelMolniy_1.jpg',
            cost=(8, 0),  # gold, silver,
            defences=[ActionTypes.RAZRYAD],
            is_unique=True,
            type_=CreatureType.CREATURE,
            actions_left=1,
            active_status=[],
            description='',
            curr_fishka=0,
            max_fishka=99,
            can_tap_for_fishka=True
        )

        self.add_default_abilities()
        self._update_abilities()
        self.player = player
        self.loc = location
        self.gui = gui

    def _update_abilities(self):  # txt max length 17
        a1 = SimpleCardAction(a_type=ActionTypes.RAZRYAD, damage=2, range_min=2, range_max=6, txt='Разряд на 2',
                              can_be_redirected=False,
                              ranged=True, state_of_action=[GameStates.MAIN_PHASE])
        self.abilities.append(a1)
        a2 = FishkaCardAction(a_type=ActionTypes.RAZRYAD, damage=self.a2_dmg, range_min=2, range_max=6, txt='Разряд на 2+3X',
                              can_be_redirected=False,
                              ranged=True, state_of_action=[GameStates.MAIN_PHASE], cost_fishka=self.a2_cost)
        self.abilities.append(a2)

    def a2_dmg(self):
        return 2 + self.curr_fishka*3

    def a2_cost(self):
        return self.curr_fishka

# p = PovelitelMolniy_1(player=2, location=14)
