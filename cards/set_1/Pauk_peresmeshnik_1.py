from cards.card import Card
from cards.card_properties import *
from game_properties import GameStates

class Pauk_peresmeshnik_1(Card):

    def __init__(self, player=1, location=0, gui=None):
        super().__init__(
            life=7,
            move=1,
            attack=(1, 2, 2),
            name='Паук-пересмешник',
            vypusk=GameSet.VOYNA_STIHIY,
            rarity=Rarity.COMMON,
            color=CardColor.LES,
            pic='data/cards/Pauk_peresmeshnik_1.jpg',
            cost=(0, 4),  # gold, silver,
            defences=[],
            is_unique=False,
            type_=CreatureType.CREATURE,
            actions_left=1,
            active_status=[CardEffect.FLYER_MAGNET],
            description='',
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
        a1 = SimpleCardAction(a_type=ActionTypes.NET, damage=0, range_min=0, range_max=2,
                               txt=f'Бросок сети', target='not flyer',
                               ranged=False, state_of_action=[GameStates.MAIN_PHASE])
        self.abilities.append(a1)
