from cards.card import Card
from cards.card_properties import ActionTypes, SimpleCardAction, CreatureType
from game_properties import GameStates

class PovelitelMolniy_1(Card):

    def __init__(self, player, location, *args):
        super().__init__(
            life=7,
            move=1,
            attack=(1, 2, 3),
            name='Ловец душ',
            vypusk='Война стихий',
            color='Лес',
            pic='data/cards/.jpg',
            cost=(7, 0),  # gold, silver,
            defences=[ActionTypes.UDAR_LETAUSHEGO],
            is_unique=True,
            type_=CreatureType.CREATURE,
            actions_left=1,
            active_status=[]
        )

        self.add_attack_ability()
        self._update_abilities()
        self.player = player
        self.loc = location  # -1 for flying, -2 for symbiots(??), -3 graveyard

    def _update_abilities(self):  # txt max length 17
        # a1 = SimpleCardAction(a_type=ActionTypes.RAZRYAD, damage=2, range_min=1, range_max=6, txt='Разряд на 2',
        #                       ranged=True, state_of_action=GameStates.MAIN_PHASE)
        # self.abilities.append(a1)
