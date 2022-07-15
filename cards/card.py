from cards.card_properties import ActionTypes, SimpleCardAction, CreatureType
from game_properties import GameStates


class Card:

    def __init__(self, life, move, attack, name,
                 vypusk, color, pic, cost, defences, is_unique,
                 type_, actions_left, active_status):
        self.type_ = type_
        self.actions_left = actions_left
        self.is_unique = is_unique
        self.defences = defences
        self.cost = cost
        self.pic = pic
        self.color = color
        self.vypusk = vypusk
        self.name = name
        self.actions = 1
        self.number_of_available_attacks = 1
        self.tapped = False
        self.attack = attack
        self.abilities = []
        self.life = life
        self.curr_life = self.life
        self.move = move
        self.curr_move = move
        self.active_status = active_status

    def add_attack_ability(self):
        if self.type_ == CreatureType.CREATURE:
            a0 = SimpleCardAction(a_type=ActionTypes.ATAKA, damage=self.attack, range_min=1, range_max=1,
                                  txt=f'Атака {self.attack[0]}-{self.attack[1]}-{self.attack[2]}',
                                  ranged=True, state_of_action=GameStates.MAIN_PHASE)
        elif self.type_ == CreatureType.FLYER:
            a0 = SimpleCardAction(a_type=ActionTypes.UDAR_LETAUSHEGO, damage=self.attack, range_min=1, range_max=1,
                                  txt=f'Атака {self.attack[0]}-{self.attack[1]}-{self.attack[2]}',
                                  ranged=True, state_of_action=GameStates.MAIN_PHASE)
        self.abilities.append(a0)
