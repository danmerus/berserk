from cards.card import Card
from cards.card_properties import *
from game_properties import GameStates

class Gorny_velikan_1(Card):

    def __init__(self, player=1, location=0, gui=None, *args):
        super().__init__(
            life=17,
            move=1,
            attack=(2, 3, 5),
            name='Горный великан',
            vypusk=GameSet.VOYNA_STIHIY,
            color=CardColor.GORY,
            rarity=Rarity.COMMON,
            pic='data/cards/Gorny_velikan_1.jpg',
            cost=(6, 0),  # gold, silver,
            defences=[ActionTypes.OTRAVLENIE],
            is_unique=False,
            type_=CreatureType.CREATURE,
            actions_left=1,
            active_status=[],
            description='Великий Хельмир гряду горную пересекая, со всякой нечистью расправлялся. Однако ж узрил горного великана и в ращелине спешно укрылся, ибо свиреп и огромен тот великан...',
            curr_fishka=0,
            max_fishka=0,
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
        pass

    def stroy_in_cb(self):
        self.in_stroy = True
        if not self.exp_in_def:
            self.exp_in_def = 1

    def stroy_out_cb(self):  ## TODO: might cause a bug/ TEMP SOLUTION
        self.in_stroy = False
        self.exp_in_def = 0
