from cards.card_properties import *
from game_properties import GameStates


class Card:

    def __init__(self, life, move, attack, name,
                 vypusk, color, pic, cost, defences, is_unique,
                 type_, actions_left, active_status, description, curr_fishka, rarity,
                 max_fishka, can_tap_for_fishka, card_class=None,
                 exp_in_def=0, exp_in_off=0):
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
        self.rarity = rarity
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
        self.can_hit_flyer = False
        self.stroy_in = None
        self.stroy_out = None
        self.in_stroy = False
        self.rolls_twice = False
        self.otravlenie = 0
        self.card_class = card_class
        self.exp_in_def = exp_in_def
        self.exp_in_off = exp_in_off

    def add_default_abilities(self):
        self.abilities = []
        if self.can_tap_for_fishka:
            self.abilities.append(IncreaseFishkaAction(txt='Накопить фишку', state_of_action=[GameStates.MAIN_PHASE]))
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

