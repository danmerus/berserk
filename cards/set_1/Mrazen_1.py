from cards.card import Card
from cards.card_properties import *
from game_properties import GameStates

class Mrazen_1(Card):

    def __init__(self, player=1, location=0, gui=None):
        super().__init__(
            life=8,
            move=1,
            attack=(1, 2, 2),
            name='Мразень',
            vypusk=GameSet.VOYNA_STIHIY,
            rarity=Rarity.COMMON,
            color=CardColor.GORY,
            pic='data/cards/Mrazen_1.jpg',
            cost=(0, 3),  # gold, silver,
            defences=[],
            is_unique=False,
            type_=CreatureType.CREATURE,
            actions_left=1,
            active_status=[],
            description='Ледяные сосульки, брошенные со страшной силой, разят не хуже стальных стрел...',
            curr_fishka=0,
            max_fishka=0,
            can_tap_for_fishka=False
        )
        self.add_default_abilities()
        self._update_abilities()
        self.player = player
        self.loc = location
        self.gui = gui

    def _update_abilities(self):
        self.a1 = SimpleCardAction(a_type=ActionTypes.METANIE, damage=(1,2,2), range_min=1, range_max=6,
                              txt=f'', ranged=True, state_of_action=[GameStates.MAIN_PHASE])
        self.a1.txt = f'Метание на {self.a1.damage[0]}-{self.a1.damage[1]}-{self.a1.damage[2]}'
        self.abilities.append(self.a1)
