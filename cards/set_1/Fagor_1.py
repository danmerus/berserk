from cards.card import Card
from cards.card_properties import *
from game_properties import GameStates

class Fagor_1(Card):

    def __init__(self, player=1, location=0, gui=None):
        super().__init__(
            life=12,
            move=1,
            attack=(2, 3, 4),
            name='Фагор',
            vypusk=GameSet.VOYNA_STIHIY,
            rarity=Rarity.COMMON,
            color=CardColor.LES,
            pic='data/cards/Fagor_1.jpg',
            cost=(0, 7),  # gold, silver,
            defences=[],
            is_unique=False,
            type_=CreatureType.CREATURE,
            actions_left=1,
            active_status=[],
            description='Могучая магия друидов заключена в неказистом на вид топоре Норда. Каким образом это легендарное оружие досталось дикому Фагору, навсегда осталось загадкой...',
            curr_fishka=0,
            max_fishka=0,
            can_tap_for_fishka=False,
        )
        self.add_default_abilities()
        self._update_abilities()
        self.player = player
        self.loc = location
        self.gui = gui

    def _update_abilities(self):
        a1 = SimpleCardAction(a_type=ActionTypes.MAG_UDAR, damage=2, range_min=0, range_max=1, txt='Магический удар на 2',
                               ranged=False, state_of_action=[GameStates.MAIN_PHASE],
                               )
        self.abilities.append(a1)
