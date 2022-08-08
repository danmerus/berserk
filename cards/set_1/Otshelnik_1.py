from cards.card import Card
from cards.card_properties import *
from game_properties import GameStates

class Otshelnik_1(Card):

    def __init__(self, player=1, location=0, gui=None, *args):
        super().__init__(
            life=6,
            move=1,
            attack=(1, 1, 2),
            name='Отшельник',
            vypusk=GameSet.VOYNA_STIHIY,
            rarity=Rarity.COMMON,
            color=CardColor.NEUTRAL,
            pic='data/cards/Otshelnik_1.jpg',
            cost=(0, 7),  # gold, silver,
            defences=[],
            is_unique=True,
            type_=CreatureType.CREATURE,
            actions_left=1,
            active_status=[],
            description='',
            curr_fishka=0,
            max_fishka=0,
            can_tap_for_fishka=False
        )

        self.add_default_abilities()
        self._update_abilities()
        self.player = player
        self.loc = location
        self.gui = gui

    def _update_abilities(self):  # txt max length 17
        a1 = SimpleCardAction(a_type=ActionTypes.LECHENIE, damage=1, range_min=0, range_max=6, txt='Лечение на 1',
                              ranged=True,  isinstant=True,
                              state_of_action=[GameStates.OPENING_PHASE, GameStates.END_PHASE, GameStates.MAIN_PHASE],
                              target='all')
        self.abilities.append(a1)

        self.a2 = TriggerBasedCardAction(txt='Перераспределение ран', recieve_inc=False, target=None,
                                         check=self.a1_check, # prep=self.a1_prep,
                                         callback=self.a1_cb, condition=Condition.ON_MAKING_DAMAGE_STAGE, display=True)
        self.abilities.append(self.a2)

    def a1_cb(self, card, victim, ability):
        print(f'Распределить {ability.damage_make} урона')

    def a1_check(self, card, victim, ability):
        return ability.a_type in [ActionTypes.ATAKA, ActionTypes.UDAR_LETAUSHEGO, ActionTypes.OSOBII_UDAR, ActionTypes.MAG_UDAR] and\
            not CardEffect.BESTELESNOE in victim.active_status and victim != self and victim.player == self.player


