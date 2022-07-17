from cards.card_properties import *
from game_properties import GameStates


class Card:

    def __init__(self, life, move, attack, name,
                 vypusk, color, pic, cost, defences, is_unique,
                 type_, actions_left, active_status, description, curr_fishka,
                 max_fishka, can_tap_for_fishka):
        self.curr_fishka = curr_fishka
        self.max_fishka = max_fishka
        self.description = description
        self.type_ = type_
        self.is_unique = is_unique
        self.defences = defences
        self.cost = cost
        self.pic = pic
        self.color = color
        self.vypusk = vypusk
        self.name = name
        self.actions = 1
        self.actions_left = actions_left
        self.number_of_available_attacks = 1
        self.tapped = False
        self.attack = attack
        self.abilities = []
        self.life = life
        self.curr_life = self.life
        self.move = move
        self.curr_move = move
        self.active_status = active_status
        self.can_defend = True
        self.can_tap_for_fishka = can_tap_for_fishka
        if self.can_tap_for_fishka:
            self.abilities.append(IncreaseFishkaAction(txt='Накопить фишку', state_of_action=[GameStates.MAIN_PHASE]))

    def add_default_abilities(self):
        if self.type_ == CreatureType.CREATURE:
            a0 = SimpleCardAction(a_type=ActionTypes.ATAKA, damage=self.attack, range_min=1, range_max=1,
                                  txt=f'Атака {self.attack[0]}-{self.attack[1]}-{self.attack[2]}',
                                  ranged=False, state_of_action=[GameStates.MAIN_PHASE])
            self.abilities.insert(0, a0)
        elif self.type_ == CreatureType.FLYER:
            a0 = SimpleCardAction(a_type=ActionTypes.UDAR_LETAUSHEGO, damage=self.attack, range_min=1, range_max=1,
                                  txt=f'Атака {self.attack[0]}-{self.attack[1]}-{self.attack[2]}',
                                  ranged=False, state_of_action=[GameStates.MAIN_PHASE])
            self.abilities.insert(0, a0)
        if not (self.type_ == CreatureType.LAND or self.type_ == CreatureType.ARTIFACT):
            a1 = DefenceAction(a_type=ActionTypes.ZASCHITA, active=True)
            self.abilities.insert(1, a1)
            self.defence_action = a1

