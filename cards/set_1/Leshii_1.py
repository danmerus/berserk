from cards.card import Card
from cards.card_properties import *
from game_properties import GameStates

class Leshii_1(Card):

    def __init__(self, player=1, location=0, gui=None):
        super().__init__(
            life=7,
            move=1,
            attack=(1, 2, 3),
            name='Леший',
            vypusk=GameSet.VOYNA_STIHIY,
            rarity=Rarity.COMMON,
            color=CardColor.LES,
            pic='data/cards/Leshii_1.jpg',
            cost=(0, 3),  # gold, silver,
            defences=[],
            is_unique=False,
            type_=CreatureType.CREATURE,
            actions_left=1,
            active_status=[],
            description='Схватка с Лешим один на один была похожа на фарс. Получив даже самую небольшую рану, эта тварь, хихикая, залезала на дерево и через пару минут была уже полностью здоровой.',
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
        a1 = SimpleCardAction(a_type=ActionTypes.LECHENIE, damage=self.a1_cb, range_min=0, range_max=0,
                              txt='Полностью излечиться', target='self',
                              ranged=True, state_of_action=[GameStates.MAIN_PHASE])
        self.abilities.append(a1)

    def a1_cb(self):
        return self.life
