from cards.card import Card
from cards.card_properties import *
from game_properties import GameStates

class Lovets_dush_1(Card):

    def __init__(self, player, location, gui, *args):
        super().__init__(
            life=7,
            move=1,
            attack=(1, 2, 3),
            name='Ловец душ',
            vypusk='Война стихий',
            color='Лес',
            pic='data/cards/Lovets_dush_1.jpg',
            cost=(7, 0),  # gold, silver,
            defences=[ActionTypes.UDAR_LETAUSHEGO],
            is_unique=True,
            type_=CreatureType.CREATURE,
            actions_left=1,
            active_status=[],
            description='',
            curr_fishka=0,
            max_fishka=1,
            can_tap_for_fishka=False
        )

        self.add_default_abilities()
        self._update_abilities()
        self.player = player
        self.loc = location
        self.gui = gui

    def _update_abilities(self):  # txt max length 17
        a1 = TriggerBasedCardAction(txt='Получить фишку при гибели существа',
                                    callback=self.a1_cb, condition=Condition.ANYCREATUREDEATH, display=False)
        self.abilities.append(a1)

        a2 = FishkaCardAction(a_type=ActionTypes.LECHENIE, damage=4, range_min=0, range_max=6, txt='Лечение на 4',
                              ranged=True, state_of_action=[GameStates.MAIN_PHASE], cost_fishka=1, targets='all')
        self.abilities.append(a2)

        a31 = SimpleCardAction(a_type=ActionTypes.ZAKLINANIE, damage=1, range_min=1, range_max=6, txt='Ранить на 1',
                              ranged=True, state_of_action=[GameStates.START_PHASE, GameStates.OPENING_PHASE,
                                                            GameStates.END_PHASE, GameStates.MAIN_PHASE], targets='enemy')
        a32 = SimpleCardAction(a_type=ActionTypes.EXTRA_LIFE, damage=1, range_min=0, range_max=6, txt='Доп. жизнь на 1',
                               ranged=True, state_of_action=[GameStates.START_PHASE, GameStates.OPENING_PHASE,
                                                             GameStates.END_PHASE, GameStates.MAIN_PHASE], targets='ally')

        a3 = MultipleCardAction(a_type=ActionTypes.ZAKLINANIE, txt='Часть души', action_list=[a31, a32], target_callbacks=None,
                              ranged=True, state_of_action=[GameStates.START_PHASE, GameStates.OPENING_PHASE,
                                                            GameStates.END_PHASE, GameStates.MAIN_PHASE], isinstant=True)
        self.abilities.append(a3)

    def a1_cb(self):
        if self.curr_fishka < self.max_fishka:
            self.gui.add_fishka(self, False)
