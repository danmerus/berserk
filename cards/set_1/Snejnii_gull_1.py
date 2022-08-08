from cards.card import Card
from cards.card_properties import *
from game_properties import GameStates

class Snejnii_gull_1(Card):

    def __init__(self, player=1, location=0, gui=None):
        super().__init__(
            life=8,
            move=1,
            attack=(1, 2, 2),
            name='Снежный Гулль',
            vypusk=GameSet.VOYNA_STIHIY,
            rarity=Rarity.COMMON,
            color=CardColor.GORY,
            pic='data/cards/Snejnii_gull_1.jpg',
            cost=(0, 4),  # gold, silver,
            defences=[],
            is_unique=False,
            type_=CreatureType.CREATURE,
            actions_left=1,
            active_status=[CardEffect.TRUPOEDSTVO, CardEffect.UDAR_CHEREZ_RYAD],
            description='Многие битвы в Халланских горах не имели ни победителей, ни побеждённых. Голодные Гулли съедали их всех...',
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
        self.a1 = SimpleCardAction(a_type=ActionTypes.UDAR_CHEREZ_RYAD, damage=1, range_min=0, range_max=2,
                               txt=f'Удар через ряд',
                               ranged=True, state_of_action=[GameStates.MAIN_PHASE])
        self.abilities.append(self.a1)
        self.a2 = SimpleCardAction(a_type=ActionTypes.DOBIVANIE, damage=2, range_min=0, range_max=1,
                              txt=f'Добивание на 2', target=self.a1_t_cb,
                              ranged=False, state_of_action=[GameStates.MAIN_PHASE])
        self.abilities.append(self.a2)


    def a1_t_cb(self):
        targets = self.gui.backend.board.get_ground_targets_min_max(card_pos_no=self.loc,
                                                   range_max=1, range_min=0,
                                                   ability=self.a1)
        return [t for t in targets if t.curr_life <= self.a2.damage and CardEffect.BESTELESNOE not in t.active_status]