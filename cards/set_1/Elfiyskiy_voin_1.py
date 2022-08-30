from cards.card import Card
from cards.card import Card
from cards.card_properties import *
from game_properties import GameStates
from functools import partial

class Elfiyskiy_voin_1(Card):

    def __init__(self, player=1, location=0, gui=None):
        super().__init__(
            life=10,
            move=1,
            attack=(2, 3, 4),
            name='Эльфийский Воин',
            vypusk=GameSet.VOYNA_STIHIY,
            rarity=Rarity.COMMON,
            color=CardColor.LES,
            card_class=CardClass.ELF,
            pic='data/cards/Elfiyskiy_voin_1.jpg',
            cost=(6, 0),  # gold, silver,
            defences=[],
            is_unique=True,
            type_=CreatureType.CREATURE,
            actions_left=1,
            active_status=[],
            description='',
            curr_fishka=0,
            max_fishka=0,
            can_tap_for_fishka=False,
            exp_in_off=1,
        )
        self.add_default_abilities()
        self._update_abilities()
        self.player = player
        self.loc = location
        self.gui = gui

    def _update_abilities(self):
        self.a2 = TriggerBasedCardAction(txt='Выстрел на 2', recieve_inc=True,
                                    callback=self.a_action, condition=Condition.PRI_ATAKE, display=False)
        self.abilities.append(self.a2)
        self.a3 = TriggerBasedCardAction(txt='-1 от аттак степных', recieve_inc=False,
                                         callback=self.on_damage, condition=Condition.ON_TAKING_DAMAGE, display=False)
        self.abilities.append(self.a3)

    def on_damage(self, target, ability):
        if target.color == CardColor.STEP and ability.a_type in ATTACK_LIST:
            ability.damage_make = max(0, ability.damage_make-1)


    def a_action(self, target):
        a = SimpleCardAction(a_type=ActionTypes.VYSTREL, damage=2, range_min=2, range_max=6,
                                   txt=f'Выстрел на 2',
                                   ranged=True, state_of_action=[GameStates.MAIN_PHASE])
        ch = SelectCardAction(child_action=a, range_min=1, range_max=6, ranged=True)
        self.gui.start_stack_action(ch, self, target, state=0, force=1)
        # self.gui.backend.stack.append((ch, self, target, 0))
        # self.gui.process_stack()
