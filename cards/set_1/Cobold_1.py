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

    def _update_abilities(self):  # txt max length 17
        self.a1 = TriggerBasedCardAction(txt='Блок щитом', recieve_inc=False, target=None, prep=self.a1_prep,
                                         check=self.a1_check,
                                    callback=self.a1_cb, condition=Condition.ON_DEFENCE_BEFORE_DICE, display=True)
        self.a1.repeat = False
        self.abilities.append(self.a1)
        a2 = SimpleCardAction(a_type=ActionTypes.LECHENIE, damage=3, range_min=0, range_max=0,
                              txt='Излечиться на 3', target='self',
                              ranged=True, state_of_action=[GameStates.MAIN_PHASE])
        self.abilities.append(a2)

    def a1_check(self, ability):
        return not self.a1.repeat and not self.tapped and not ability.redirected

    def a1_prep(self):
        if self.tapped:
            return
        elif self.a1.target and self.a1.actor:
            self.gui.start_flickering(self)
            self.gui.backend.stack.append([(self.a1.target, self.a1.actor, self, 1), (LambdaCardAction(func=self.a1_non_ins), None, None, 1)])

    def a1_cb(self):
        if self.tapped:
            return
        elif self.a1.target:
            b = BlockAction(self.a1.target)
            self.gui.backend.stack.append((b, self, self, 2))
        self.actions_left -= 1
        self.gui.tap_card(self)
        self.a1.isinstant = False
        self.a1.repeat = False
        self.a1.disabled = True
        self.gui.destroy_flickering(self)
        self.gui.process_stack()

    def a1_non_ins(self):
        self.a1.repeat = False
        self.a1.isinstant = False
        self.gui.destroy_flickering(self)

    def stroy_in_cb(self):
        self.in_stroy = True
        if ActionTypes.UDAR_CHEREZ_RYAD not in self.defences:
            self.defences.append(ActionTypes.UDAR_CHEREZ_RYAD)

    def stroy_out_cb(self):  ## TODO: might cause a bug/ TEMP SOLUTION
        self.in_stroy = False
        try:
            self.defences.remove(ActionTypes.UDAR_CHEREZ_RYAD)
        except:
            pass
