from cards.card import Card
from cards.card_properties import *
from game_properties import GameStates

class Voin_hrama_1(Card):

    def __init__(self, player=1, location=0, gui=None, *args):
        super().__init__(
            life=13,
            move=2,
            attack=(2, 4, 5),
            name='Воин Храма',
            vypusk=GameSet.VOYNA_STIHIY,
            color=CardColor.NEUTRAL,
            rarity=Rarity.COMMON,
            pic='data/cards/Voin_hrama_1.jpg',
            cost=(0, 8),  # gold, silver,
            defences=[],
            is_unique=False,
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
        self.rolls_twice = True

    def _update_abilities(self):  # txt max length 17
        a1 = TriggerBasedCardAction(txt='Бросок на уворот при дальней атаке', recieve_inc=True, check=self.a1_check,
                                    callback=self.a1_cb, condition=Condition.ON_RECIEVING_RANGED_ATTACK, display=False)
        self.abilities.append(a1)

    def a1_check(self, ability, card, target):
        if not hasattr(ability, 'passed_Voin_hrama'):
            ability.passed_Voin_hrama = False
        return not ability.passed_Voin_hrama

    def a1_cb(self, ability, card, target):
        roll = self.gui.get_roll_result(1)
        print('voin hrama roll', roll, ability)
        self.gui.process_rolls(roll, 0, 0, 1, 0, self, None)
        ability.passed_Voin_hrama = True
        if roll[0] > 4:
            b = BlockAction(self.gui.curr_top)
            self.gui.add_to_stack(b, self, None, 2)