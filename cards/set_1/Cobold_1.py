from cards.card import Card
from cards.card_properties import *
from game_properties import GameStates

class Cobold_1(Card):

    def __init__(self, player=1, location=0, gui=None, *args):
        super().__init__(
            life=11,
            move=1,
            attack=(2, 3, 4),
            name='Кобольд',
            vypusk=GameSet.VOYNA_STIHIY,
            color=CardColor.LES,
            rarity=Rarity.COMMON,
            pic='data/cards/Cobold_1.jpg',
            cost=(5, 0),  # gold, silver,
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
        self.stroy_in = self.stroy_in_cb
        self.stroy_out = self.stroy_out_cb

    def _update_abilities(self):
        self.a1 = TriggerBasedCardAction(txt='Блок щитом', recieve_inc=False, target=None, prep=self.a1_prep,
                                         recieve_all=True, callback=self.a2_cb, callback_prep=self.a1_cb,
                                         isinstant=True, state_of_action=[GameStates.MAIN_PHASE],
                                         check=self.a1_check, cleanup=self.a1_non_ins,
                                          condition=Condition.ON_DEFENCE_BEFORE_DICE, display=True)
        self.abilities.append(self.a1)
        a2 = SimpleCardAction(a_type=ActionTypes.LECHENIE, damage=3, range_min=0, range_max=0,
                              txt='Излечиться на 3', target='self',
                              ranged=True, state_of_action=[GameStates.MAIN_PHASE])
        self.abilities.append(a2)

    def a1_check(self, ability, card, target):
        return target == self and not self.tapped and not ability.redirected and not ability.passed and\
               (ability.a_type == ActionTypes.ATAKA or ability.a_type == ActionTypes.UDAR_LETAUSHEGO)

    def a1_prep(self):
        if self.tapped:
            return
        elif self.a1.target and self.a1.actor:
            self.gui.start_flickering(self, player=self.player)
            self.gui.backend.stack.append([(LambdaCardAction(func=self.a1_non_ins), None, None, 1), (self.a1.target, self.a1.actor, self, 1)])

    def a1_cb(self, ability, card, target):
        if self.a1_check(ability, card, target):
            self.a1.disabled = False
            self.gui.flicker_dict = {self.player: [self.id_on_board]}
            self.gui.in_stack = True
            self.gui.passed_1 = False
            self.gui.passed_2 = False
            self.gui.curr_priority = self.player
            # self.gui.player_passed()
            # self.gui.stack.pop()
            self.a1.to_remove = self.gui.curr_top
            ability.passed = True
            self.gui.handle_passes()

    def a2_cb(self, ability, card, target):
        self.a1.cleanup()
        b = BlockAction(self.a1.to_remove)
        self.tapped = True  # TODO TAP SELF
        self.gui.add_to_stack(b, self, None, 2)

    def a1_non_ins(self):
        self.gui.flicker_dict = {}
        # self.in_stack = False
        self.a1.disabled = True

    def stroy_in_cb(self):
        self.in_stroy = True
        if ActionTypes.UDAR_CHEREZ_RYAD not in self.defences:
            self.defences.append(ActionTypes.UDAR_CHEREZ_RYAD)
            # print('self.defences', self.defences)

    def stroy_out_cb(self):  ## TODO: might cause a bug/ TEMP SOLUTION
        self.in_stroy = False
        try:
            self.defences.remove(ActionTypes.UDAR_CHEREZ_RYAD)
        except:
            pass
