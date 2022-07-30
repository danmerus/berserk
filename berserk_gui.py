import kivy
kivy.require('2.0.1')
from kivy import Config
Config.set('input', 'mouse', 'mouse,multitouch_on_demand')
from kivy.core.window import Window
from kivy.uix.floatlayout import FloatLayout
from kivy.app import App
from kivy.properties import ObjectProperty, StringProperty, NumericProperty, BooleanProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.scatterlayout import ScatterLayout
from kivy.uix.behaviors import ButtonBehavior, DragBehavior
from kivy.uix.scrollview import ScrollView
from kivy.uix.dropdown import DropDown
from kivy.uix.popup import Popup
from kivy.uix.button import Button
from kivy.uix.widget import Widget
from kivy.core.audio import SoundLoader
from kivy.uix.label import Label
from kivy.uix.modalview import ModalView
from kivy.graphics import Line, Color, InstructionGroup, Rectangle, Rotate, PushMatrix, Rotate, PopMatrix, Ellipse
from kivy.uix.progressbar import ProgressBar
import numpy.random as rng
from kivy.clock import Clock
from kivy.animation import Animation
from functools import partial
from itertools import chain
from kivy.uix.image import Image
from  kivy.metrics import dp
from kivy.clock import mainthread
from kivy.graphics.vertex_instructions import Triangle, BorderImage
from cards.card_properties import *
import game_properties
import card_prep
import operator
from copy import deepcopy
import collections

Window.size = (960, 540)
# Window.size = (1920, 1080)
# Window.maximize()
CARD_X_SIZE = (Window.width * 0.084375)
CARD_Y_SIZE = CARD_X_SIZE #(Window.height * 0.15)

STACK_DURATION = 10
TURN_DURATION = 12

DZ_SIZE = (CARD_X_SIZE, Window.height * 0.45)

class MainField(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # self.background_normal = bg_sorce
        # self.width = width
        # self.hight = hight


class Vertical(Widget):
    pass


class Horizontal(Widget):
    pass

class OmegaPopup(DragBehavior, Popup):
    def __init__(self, **kwargs):
        super(OmegaPopup, self).__init__(**kwargs)
        self.drag_timeout = 10000000
        self.drag_distance = 10
        self.drag_rectangle = [self.x, self.y, self.width, self.height]

    def on_pos(self, *args):
        self.drag_rectangle = [self.x, self.y, self.width, self.height]

    def on_size(self, *args):
        self.drag_rectangle = [self.x, self.y, self.width, self.height]

    def _align_center(self, *l):
        pass


class BerserkApp(App):

    def __init__(self, backend):
        super(BerserkApp, self).__init__()
        self.backend = backend
        self.title = 'Berserk Renewal'

    def destroy_x(self, list_, long=False):
        for bt in list_:
            self.root.remove_widget(bt)

    def destroy_target_marks(self):
        for btn, card in self.target_marks_cards:
            card.remove_widget(btn)


        self.target_marks_buttons = []
        self.target_marks_cards = []

    def destroy_target_rectangles(self):
        for r, canvas in self.target_rectangles:
            canvas.remove(r)
        self.target_rectangles = []

    def delete_move_marks_on_unfocus(self, window, pos):
        delete_ = True
        for nav_b in self.nav_buttons:
            if abs(pos.x-CARD_X_SIZE/2 - nav_b.x) < CARD_X_SIZE and abs(pos.y - CARD_Y_SIZE/2 - nav_b.y) < CARD_Y_SIZE:
                delete_ = False
        if delete_:
            self.destroy_x(self.nav_buttons)
            self.nav_buttons = []

    def delete_target_marks_on_unfocus(self, window, pos):
        if self.target_marks_cards:
            delete_ = True
            if pos.is_mouse_scrolling:
                delete_ = False
            for nav_b in self.target_marks_buttons:
                nav_b = self.get_pos(nav_b)
                if abs(pos.x - nav_b[0]) < CARD_X_SIZE and abs(pos.y - nav_b[1]) < CARD_Y_SIZE:
                    delete_ = False
            if delete_:
                self.destroy_target_rectangles()
                self.destroy_target_marks()
                self.multiple_targets_list = []  # здесь копятся цели для многоступенчатых действий
                Clock.schedule_once(partial(self.destroy_x, self.die_pics), 1)
                self.die_pics = []

    def destroy_flickering(self, *args):
        for c in self.selection_flicker_dict.keys():
            self.base_overlays[c].remove_widget(self.selection_flicker_dict[c])

    def popup_attack_bind(self, result, ability, card, victim, *args):
        if hasattr(self, 'attack_popup'):
            self.attack_popup.dismiss()
            del self.attack_popup
        a, b = result
        if a:
            victim.curr_life -= card.attack[a - 1]
            self.display_damage(victim, -1 * card.attack[a - 1])
            self.play_attack_sound(card.attack[a - 1])
        if b:
            card.curr_life -= victim.attack[b - 1]
            self.display_damage(card, -1 * card.attack[b - 1])

        self.draw_red_arrow(self.cards_dict[card], self.cards_dict[victim], card, victim)
        self.hp_label_dict[victim].text = f'{victim.curr_life}/{victim.life}'
        self.hp_label_dict[card].text = f'{card.curr_life}/{card.life}'

        self.destroy_target_rectangles()
        self.destroy_target_marks()
        all_cards = self.backend.board.get_all_cards()
        if card.curr_life <= 0 and card in all_cards:
            self.destroy_card(card)
        if victim.curr_life <= 0 and victim in all_cards:
            self.destroy_card(victim)
        card.actions_left -= 1
        if card.actions_left <= 0:
            if not card.tapped:
                self.tap_card(card)
        if ability.tap_target:
            self.tap_card(victim)

    def destroy_card(self, card, ):
        cb = self.backend.board.get_all_cards_with_callback(Condition.ANYCREATUREDEATH)
        if cb:
            for c, a in cb:
                a.callback()
        if card.type_ == CreatureType.FLYER:
            if card.player == 1:
                self.dop_zone_1.children[0].remove_widget(self.cards_dict[card])
            else:
                self.dop_zone_2.children[0].remove_widget(self.cards_dict[card])
        else:
            self.layout.remove_widget(self.cards_dict[card])
        self.backend.board.remove_card(card)

        rl1 = RelativeLayout(size=(CARD_X_SIZE, CARD_Y_SIZE))
        btn1 = Button(disabled=False,
                      background_normal=card.pic, pos=(0, CARD_Y_SIZE * 0.2),
                      size=(CARD_X_SIZE, CARD_Y_SIZE * 0.8), size_hint=(None, None))
        card.loc = -1
        self.base_overlays[card] = RelativeLayout()
        self.draw_card_overlay(card, 3)
        rl1.add_widget(btn1)
        rl1.add_widget(self.base_overlays[card])
        if card.player == 1:
            self.grave_1_gl.add_widget(rl1)
            self.grave_buttons_1.append(rl1)
            self.backend.board.grave1.append(card)
        elif card.player == 2:
            self.grave_2_gl.add_widget(rl1)
            self.grave_buttons_2.append(rl1)
            self.backend.board.grave2.append(card)
        self.check_game_end()
        self.update_zone_counters()
        Clock.schedule_once(lambda x: self.destroy_red_arrows(), 1)

    def destroy_red_arrows(self):
        for el in self.root.canvas.children:
            if el in self.red_arrows:
                self.root.canvas.remove(el)
        self.red_arrows = []

    def card_popup(self, window, pos):
        mouse = pos.button
        if mouse == 'right':
            for c, el in self.cards_dict.items():
                x, y = self.get_pos(c)
                if 0 < (pos.x-x)<CARD_X_SIZE and 0 < (pos.y-y) < CARD_Y_SIZE and not hasattr(self, 'card_popup_obj'):
                    if not hasattr(self, 'card_popup_obj') and not el.collide_widget(self.root):
                        #print(el.collide_widget(self.root))
                        self.card_popup_obj = Popup(title='Berserk renewal',
                                      content=Image(source=c.pic[:-4]+'_full.jpg'),
                                      size_hint=(None, None), size=(281, 400))
                        self.card_popup_obj.open()

    def play_attack_sound(self, dmg):
        if abs(dmg) < 3:
            sound = SoundLoader.load('data/sound/weak_punch.wav')
        elif 3 <= abs(dmg) < 5:
            sound = SoundLoader.load('data/sound/med_punch.wav')
        elif abs(dmg) >= 5:
            sound = SoundLoader.load('data/sound/hard_punch.wav')
        else:
            return
        sound.play()

    def card_popup_destr(self, window, pos):
        if hasattr(self, 'card_popup_obj'):
            self.card_popup_obj.dismiss()
            del self.card_popup_obj

    def draw_selection_border(self, instance, card):
        if hasattr(self, "card_border"):
            self.card_border[1].canvas.remove(self.card_border[0])
        with instance.canvas:
            if card.player == 1:
                c = Color(1, 1, 0, 1)
            else:
                c = Color(0.2, 0.2, 0.8, 1)
            self.card_border = (Line(width=1, color=c, rectangle=(0, 0, CARD_X_SIZE, CARD_Y_SIZE)), instance)

    def move_card(self, card, move, instance):
        x, y = instance.parent.x, instance.parent.y
        anim = Animation(x=x, y=y, duration=0.5)
        anim.start(self.cards_dict[card])
        self.destroy_x(self.nav_buttons)
        self.nav_buttons = []
        card.curr_move -= 1
        self.backend.board.update_board(card.loc, move, card)
        card.loc = move
        self.move_label_dict[card].text = f'{card.curr_move}/{card.move}'

    def check_game_end(self):
        cards = self.backend.board.get_all_cards()
        if not cards:
            popup = Popup(title='Berserk renewal',
                      content=Label(text='Ничья!'),
                      size_hint=(None, None), size=(400, 400))
            popup.open()
        elif len([c for c in cards if c.player == 1]) == 0:
            popup = Popup(title='Berserk renewal',
                          content=Label(text='Победа игрока 2!'),
                          size_hint=(None, None), size=(400, 400))
            popup.open()
        elif len([c for c in cards if c.player == 2]) == 0:
            popup = Popup(title='Berserk renewal',
                          content=Label(text='Победа игрока 1!'),
                          size_hint=(None, None), size=(400, 400))
            popup.open()

    def draw_red_arrow(self, from_card, to_card, card, victim):
        with self.root.canvas:
            c = Color(1, 0, 0, 0.8)
            if card.type_ == CreatureType.FLYER or card.type_ == CreatureType.LAND:
                if card.player == 1:
                    x, y = self.dop_zone_1.to_parent(from_card.x, from_card.y)
                else:
                    x, y = self.dop_zone_2.to_parent(from_card.x, from_card.y)
            else:
                x, y = self.cards_dict[card].pos
            if victim.type_ == CreatureType.FLYER or victim.type_ == CreatureType.LAND:
                if victim.player == 1:
                    n, m = self.dop_zone_1.to_parent(to_card.x, to_card.y)
                else:
                    n, m = self.dop_zone_2.to_parent(to_card.x, to_card.y)
            else:
                n, m = to_card.x, to_card.y

            l = Line(width=3, color=c, points=(x+CARD_X_SIZE/2, y+CARD_Y_SIZE/2,
                                           n+CARD_X_SIZE/2, m+CARD_Y_SIZE/2))
            # TODO
            # tri = Triangle(color=c, points=[x*0.7+(x-n)*0.15*0.57, (x-n)*0.85+n*0.1,
            #                                  n+CARD_X_SIZE/2, m+CARD_Y_SIZE/2,
            #                                 x*0.7+(x-n)*0.15*0.57, (y-m)*0.85+m])
            self.red_arrows.append(l)
            Clock.schedule_once(lambda x: self.destroy_red_arrows(), 2)
            #self.red_arrows.append(tri)

    def draw_die(self, *args):
        r1 = args[0]
        if isinstance(r1, tuple) and r1[1] == 2:
            r1_i = Image(source=f'data/dice/Alea_{r1[0]}.png', pos=(Window.width * 0.12, Window.height * 0.8),
                         size=(0.07 * Window.width, Window.height * 0.07))
        elif isinstance(r1, tuple) and r1[1] == 1:
            r1_i = Image(source=f'data/dice/Alea_{r1[0]}.png', pos=(Window.width * 0.78, Window.height * 0.8),
                         size=(0.07 * Window.width, Window.height * 0.07))
        else:
            r1_i = Image(source=f'data/dice/Alea_{r1}.png', pos=(Window.width * 0.78, Window.height * 0.8),
                         size=(0.07 * Window.width, Window.height * 0.07))
        self.root.add_widget(r1_i)
        self.die_pics.append(r1_i)
        if len(args) == 2:
            r2 = args[1]
            r2_i = Image(source=f'data/dice/Alea_{r2}.png', pos=(Window.width * 0.12, Window.height * 0.8),
                         size=(0.07 * Window.width, Window.height * 0.07))
            self.die_pics.append(r2_i)
            self.root.add_widget(r2_i)

    def get_pos(self, card):
        if card.type_ == CreatureType.CREATURE:
            return self.cards_dict[card].pos
        if card.type_ == CreatureType.FLYER:
            if card.player == 1:
                return self.dop_zone_1.to_parent(*self.cards_dict[card].pos)
            else:
                return self.dop_zone_2.to_parent(*self.cards_dict[card].pos)

    def display_damage(self, target_card, dmg):
        # MARK
        x, y = self.get_pos(target_card)
        ly = RelativeLayout(pos=(x, y))
        with ly.canvas:
            box_size = Window.height*0.02 * (1.14)**abs(dmg)
            hitbox = Rectangle(pos=(CARD_X_SIZE/2, CARD_X_SIZE/2), size=(box_size, box_size), background_color=Color(0, 0.7, 0, 1))
            lbl = Label(text=str(dmg), pos=(CARD_X_SIZE/2, CARD_X_SIZE/2), size=(box_size, box_size), color=(1,1,1,1), font_size=box_size*0.9)
            border = Line(pos=(CARD_X_SIZE / 2, CARD_X_SIZE / 2), rectangle=(CARD_X_SIZE/2, CARD_X_SIZE/2, box_size, box_size))
            self.damage_marks.append(lbl)
        self.root.add_widget(ly)
        anime = Animation(x=x-Window.height*(rng.randint(0, 5)/100), y=y+Window.height*(rng.randint(0, 5)/100), s=1/60,
                          duration=1, t='out_circ')
        anime.start(ly)
        Clock.schedule_once(lambda x: self.root.remove_widget(ly), 1)

    def handle_instant_stack(self, ability, card, victim):
        if self.backend.stack:
            for el in self.backend.stack:
                if len(el) == 3:
                    ab, _, _ = el
                    if isinstance(ab, DefaultMovementAction) and isinstance(ability, DefaultMovementAction) :
                        return
        self.backend.in_stack = True
        self.eot_button.disabled = True
        self.ph_button.disabled = False
        if self.backend.curr_priority == 1:
            self.backend.passed_2 = False
        elif self.backend.curr_priority == 2:
            self.backend.passed_1 = False
        if isinstance(ability, MultipleCardAction):
            if len(self.multiple_targets_list) == len(ability.action_list):
                out = []
                for i, a in enumerate(ability.action_list):
                    out.append((a, card, self.multiple_targets_list[i]))
            else:
                return
        else:
            out = (ability, card, victim)
        if card.actions_left > 0:
            self.backend.stack.append(out)
            self.multiple_targets_list = []
            if ability.a_type != ActionTypes.MOVEMENT:
                card.actions_left -= 1
            for b in self.selected_card_buttons:
                b.disabled = True
            self.start_timer(STACK_DURATION)

    def start_stack_action(self, ability, card, victim, instance):
        if (ability.a_type == ActionTypes.ATAKA or ability.a_type == ActionTypes.UDAR_LETAUSHEGO) and \
            not CardEffect.NAPRAVLENNY_UDAR in card.active_status:
            defenders = self.backend.board.get_defenders(card, victim)
            if defenders:
                self.backend.in_stack = True
                self.eot_button.disabled = True
                self.ph_button.disabled = False
                self.backend.curr_priority = victim.player

                self.draw_red_arrow(self.cards_dict[card], self.cards_dict[victim], card, victim)
                Clock.schedule_once(lambda x: self.start_timer(STACK_DURATION))
                self.disable_all_buttons_except_instant(defenders)  # adds to stack_cards
                card.actions_left -= 1
                for c in defenders:
                    rl = RelativeLayout()
                    self.base_overlays[c].add_widget(rl)
                    with rl.canvas:
                        col = Color(1,1,1,0.2)
                        rect = Rectangle(size=(CARD_X_SIZE, CARD_Y_SIZE),
                                  background_color=col,
                                  pos=(0, 0), size_hint=(1, 1))
                        anim = Animation(opacity=0, duration=0.5)+Animation(opacity=1, duration=0.5)
                        anim.repeat = True
                        anim.start(rl)
                    self.selection_flicker_dict[c] = rl
                    c.defence_action.fight_with = card
                self.pending_attack = ability
                self.backend.stack.append((ability, card, victim))
            elif self.backend.board.get_instants():
                self.handle_instant_stack(ability, card, victim)
            else:
                self.perform_card_action(ability, card, victim)
                self.process_stack()
        elif ability.a_type == ActionTypes.ZASCHITA:
            if hasattr(self, 'pending_attack') and self.pending_attack:
                if self.backend.curr_priority == card.player and ability.fight_with:
                    self.destroy_flickering()
                    for a, c, v in self.backend.stack:
                        if a == self.pending_attack:
                            self.backend.stack.remove((a, c, v))
                    self.defender_set = True
                    self.backend.player_passed()
                    Clock.schedule_once(lambda x: self.start_timer(STACK_DURATION))
                    temp_attack = deepcopy(self.pending_attack)
                    temp_attack.tap_target = True
                    self.pending_attack = None
                    self.backend.stack.append((temp_attack, ability.fight_with, card))
        else:
            # if isinstance(ability, FishkaCardAction):  # Separate func?
            #     if (isinstance(ability.cost_fishka, int) and ability.cost_fishka > card.curr_fishka) or \
            #             (callable(ability.cost_fishka) and ability.cost_fishka() > card.curr_fishka):
            #         self.destroy_target_rectangles()
            #         self.destroy_target_marks()
            #         return
            instants = self.backend.board.get_instants()
            self.disable_all_buttons_except_instant(instants)
            if instants:  #or self.pending_attack
                self.handle_instant_stack(ability, card, victim)
            else:
                if isinstance(ability, MultipleCardAction):
                    if len(self.multiple_targets_list) == len(ability.action_list):
                        for i, a in enumerate(ability.action_list):
                            self.perform_card_action(a, card, self.multiple_targets_list[i])
                        self.multiple_targets_list = []
                        self.process_stack()
                    else:
                        return
                else:
                    self.perform_card_action(ability, card, victim)
                    self.process_stack()

    def check_all_passed(self, instance):
        instants = self.backend.board.get_instants()
        if instants and not self.backend.passed_once:
            self.backend.in_stack = True
            self.eot_button.disabled = True
            self.ph_button.disabled = False
        if self.backend.passed_once:
            self.backend.passed_once = False
        i1 = [(c, a) for (c, a) in instants if (c.player == 1 and c.actions_left > 0)]
        i2 = [(c, a) for (c, a) in instants if (c.player == 2 and c.actions_left > 0)]
        if not i1 and not self.pending_attack and self.backend.in_stack:
            self.backend.passed_1 = True
            if self.backend.curr_priority == 1:
                self.backend.switch_priority()
        if not i2 and not self.pending_attack and self.backend.in_stack:
            self.backend.passed_2 = True
            if self.backend.curr_priority == 2:
                self.backend.switch_priority()
        if self.backend.passed_2 and self.pending_attack and not i1 and self.backend.curr_priority == 1: # cкипаем приоритетет при атаке без инстантов
            self.backend.passed_1 = True
            self.process_stack()
        if self.backend.passed_1 and self.pending_attack and not i2 and self.backend.curr_priority == 2:
            self.backend.passed_2 = True
            self.process_stack()

        if self.backend.passed_1 and self.backend.passed_2:
            self.process_stack()
        if i1 and self.backend.curr_priority == 2 and self.backend.passed_2:
            self.backend.switch_priority()
        if i2 and self.backend.curr_priority == 1 and self.backend.passed_1:
            self.backend.switch_priority()
        if not self.backend.passed_1 and not self.backend.passed_2:
            return

    def process_stack(self):
        if len(self.backend.stack) == 0:  # выход по завершении стека
            self.pending_attack = None
            self.backend.curr_priority = self.backend.current_active_player
            self.stack_cards = []
            self.backend.in_stack = False
            if self.backend.curr_game_state == GameStates.MAIN_PHASE:
                self.backend.passed_once = True  # Flag to stay in slow main phase
                self.backend.passed_1 = False
                self.backend.passed_2 = False
                self.defender_set = False
                self.eot_button.disabled = False
                self.ph_button.disabled = True
                if not hasattr(self, 'attack_popup'):
                    self.start_timer(TURN_DURATION)
                if self.backend.curr_priority != self.backend.current_active_player:
                    self.backend.switch_priority()
            else:
                self.backend.next_game_state()
            return
        while self.backend.stack:
            if self.backend.passed_2 and self.backend.passed_1:
                args = self.backend.stack.pop()
                self.perform_card_action(*args)
                self.backend.passed_1 = False
                self.backend.passed_2 = False
            else:
                if not hasattr(self, 'attack_popup'):
                    self.start_timer(STACK_DURATION)
                return

        self.process_stack()

    def perform_card_action(self, *args):
        if self.backend.in_stack and not (self.backend.passed_1 and self.backend.passed_2):
            return
        if len(args) == 3:
            ability, card, victim = args
        elif isinstance(args, tuple):
            for a, c, v in args:
                self.perform_card_action(a, c, v)
            return
        if isinstance(ability, FishkaCardAction):
            if (isinstance(ability.cost_fishka, int) and ability.cost_fishka > card.curr_fishka) or \
                    (callable(ability.cost_fishka) and ability.cost_fishka() > card.curr_fishka):
                self.destroy_target_rectangles()
                self.destroy_target_marks()
                return
        if isinstance(ability, IncreaseFishkaAction):
            self.add_fishka(card)
            return
        if isinstance(ability, TapToHitFlyerAction):
            card.can_hit_flyer = True
            card.actions_left -= 1
            self.tap_card(card)
            return
        if isinstance(ability, DefaultMovementAction):
            if not card.tapped:
                self.move_card(card, victim[0], victim[1])  # victim here is a move
            else:
                pass
            return
        all_cards = self.backend.board.get_all_cards()
        if ability.a_type not in victim.defences and card in all_cards and victim in all_cards:  # check if target and action card is valid (card is alive)
            if ability.a_type == ActionTypes.ATAKA or ability.a_type == ActionTypes.UDAR_LETAUSHEGO:
                if ability.callback:
                    ability.callback(victim)
                if card.can_hit_flyer and victim.type_ == CreatureType.FLYER:
                    card.can_hit_flyer = False
                if not victim.tapped:
                    outcome_list, roll1, roll2 = self.backend.get_fight_result()
                    print('roll1: ', roll1, 'roll2: ', roll2)
                    self.draw_die(roll1, roll2)
                    if len(outcome_list) == 1:
                        a, b = outcome_list[0]
                        if a:
                            victim.curr_life -= card.attack[a-1]
                            self.display_damage(victim, -1 * card.attack[a - 1])
                            self.play_attack_sound(card.attack[a - 1])
                        if b:
                            card.curr_life -= victim.attack[b-1]
                            self.display_damage(card, -1 * card.attack[b - 1])
                    else:
                        self.attack_popup = OmegaPopup(title='Berserk renewal',
                                  width=310, height=150, background_color=(1,0,0,1),
                                  overlay_color=(0,0,0,0), size_hint=(None, None),
                                  auto_dismiss=False)
                        rl = RelativeLayout(size=self.attack_popup.size, size_hint=(None, None))
                        self.attack_popup.content = rl
                        with rl.canvas:
                            l = Label(pos=(70, 20), size_hint=(None, None), text='Выберите результат сражения: ')
                            self.garbage.append(l)
                        dmg_dict = {0: 'Промах', 1: 'Слабый', 2: 'Средний', 3: 'Cильный'}
                        btn1 = Button(pos=(0, 0), size=(130, 30), background_color=(1,0,0,1),
                                      size_hint=(None, None), text=dmg_dict[outcome_list[0][0]]+'-'+dmg_dict[outcome_list[0][1]])
                        btn2 = Button(pos=(rl.width/2, 0), size=(130, 30), background_color=(1,0,0,1),
                                      size_hint=(None, None), text=dmg_dict[outcome_list[1][0]]+'-'+dmg_dict[outcome_list[1][1]])
                        btn1.bind(on_press=partial(self.popup_attack_bind, outcome_list[0], ability, card, victim))
                        btn2.bind(on_press=partial(self.popup_attack_bind, outcome_list[1], ability, card, victim))
                        self.timer.bind(on_complete=partial(self.popup_attack_bind, outcome_list[1], ability, card, victim))
                        rl.add_widget(btn1)
                        rl.add_widget(btn2)
                        self.attack_popup.open()
                        return
                else:
                    roll1 = self.backend.get_roll_result()
                    if roll1 <= 3:
                        d = ability.damage[0]
                    elif 4 <= roll1 <= 5:
                        d = ability.damage[1]
                    elif roll1 > 5:
                        d = ability.damage[2]
                    victim.curr_life -= d
                    self.display_damage(victim, -1 * d)
                    self.play_attack_sound(d)
                    self.draw_die((roll1, card.player))
            else:
                if isinstance(ability.damage, int):
                    d = ability.damage
                    roll1 = self.backend.get_roll_result()
                elif callable(ability.damage):
                    d = ability.damage()
                    roll1 = self.backend.get_roll_result()
                elif len(ability.damage) == 3:
                    roll1 = self.backend.get_roll_result()
                    if roll1 <= 3:
                        d = ability.damage[0]
                    elif 4 <= roll1 <= 5:
                        d = ability.damage[1]
                    elif roll1 > 5:
                        d = ability.damage[2]
                if ability.a_type == ActionTypes.LECHENIE:
                    victim.curr_life = min(victim.curr_life + d, victim.life)
                    self.display_damage(victim, d)
                elif ability.a_type == ActionTypes.EXTRA_LIFE:
                    victim.life += d
                    victim.curr_life += d
                    self.display_damage(victim, d)
                else:
                    victim.curr_life -= d
                    self.display_damage(victim, -1 * d)
                self.draw_die((roll1, card.player))

        self.draw_red_arrow(self.cards_dict[card], self.cards_dict[victim], card, victim)
        self.hp_label_dict[victim].text = f'{victim.curr_life}/{victim.life}'
        self.hp_label_dict[card].text = f'{card.curr_life}/{card.life}'

        self.destroy_target_rectangles()
        self.destroy_target_marks()

        if card.curr_life <= 0 and card in all_cards:
            self.destroy_card(card)
        if victim.curr_life <= 0 and victim in all_cards:
            self.destroy_card(victim)

        card.actions_left -= 1
        if card.actions_left <= 0:
            if not card.tapped:
                self.tap_card(card)
        if ability.tap_target:
            self.tap_card(victim)

        if isinstance(ability, FishkaCardAction):
            self.remove_fishka(card, ability.cost_fishka)

    def on_new_turn(self):
        self.damage_marks = []
        for b in self.selected_card_buttons:
            b.disabled = True
        self.destroy_target_marks()
        self.destroy_target_rectangles()
        for c, rl in self.cards_dict.items():
            if c.player == self.backend.current_active_player:
                self.move_label_dict[c].text = f'{c.move}/{c.move}'
        if self.selected_card:
            if self.selected_card.player == self.backend.current_active_player:
                self.display_card_actions(self.selected_card, False, None)

    def on_click_on_card(self, card, instance):
        self.destroy_target_marks()
        #if self.stack_cards and card not in self.stack_cards:
        if card.player != self.backend.curr_priority and not self.backend.board.isinstant_card(card):
            return
        if card.actions_left <= 0:
            return
        if self.selected_card:
            Clock.schedule_once(partial(self.draw_card_overlay, self.selected_card, 0))
        self.selected_card = card
        self.destroy_x(self.selected_card_buttons)
        self.selected_card_buttons = []
        # Draw border
        self.draw_selection_border(instance.parent, card)
        # Higlight name
        self.bright_card_overlay(card)
        # Display card action buttons
        self.display_card_actions(card, True, instance)
        # Display navigation buttons
        moves = self.backend.board.get_available_moves(card)
        if card.player != self.backend.current_active_player or self.backend.in_stack:
            moves = []
        if self.nav_buttons:
            self.destroy_x(self.nav_buttons)
            self.nav_buttons = []
        for move in moves:
            x, y = self.card_position_coords[move][0], self.card_position_coords[move][1]
            rl = RelativeLayout(pos=(x, y), size=(CARD_X_SIZE, CARD_Y_SIZE), size_hint=(None, None))
            btn = Button(size=(CARD_X_SIZE, CARD_Y_SIZE), size_hint=(None, None), background_color=(0, 0, 0, 0))
            ability = DefaultMovementAction(move=move)
            btn.bind(on_press=partial(self.start_stack_action, ability, card, (move, btn)))
            with rl.canvas:
                Color(1, 0, 0, 1)
                Ellipse(pos=(CARD_X_SIZE / 2 - 10, CARD_Y_SIZE / 2 - 10), size=(20, 20))
            rl.add_widget(btn)
            self.root.add_widget(rl)
            self.nav_buttons.append(rl)

    def tap_card(self, card):
        scatter_obj = self.cards_dict[card]
        for obj_ in scatter_obj.children:
            if isinstance(obj_, Button):
                ch = obj_
        if not card.tapped:
            ch.background_normal = card.pic[:-4]+'_rot90.jpg'
            ch.pos = (CARD_X_SIZE*0.2, 0)
            ch.size = (CARD_X_SIZE*0.8, CARD_Y_SIZE)
            self.draw_card_overlay(card, 1)
            card.tapped = True
            for b in self.selected_card_buttons:
                b.disabled = True
        else:
            ch.background_normal = card.pic
            self.draw_card_overlay(card, 2)
            ch.pos = (0, CARD_Y_SIZE * 0.2)
            ch.size = (CARD_X_SIZE, CARD_Y_SIZE*0.8)
            card.tapped = False
            for b in self.selected_card_buttons:  # Re-activate card buttons on untap
                b.disabled = False

    def bind_multiple_actions(self, card, multiple_ability, ix, target, *args):
        self.destroy_target_rectangles()
        self.destroy_target_marks()
        self.multiple_targets_list.append(target)
        if len(multiple_ability.action_list)-1 == ix and (len(self.multiple_targets_list)==len(multiple_ability.action_list)):
            self.start_stack_action(multiple_ability, card, None, None)
        else:
            bind_ = partial(self.bind_multiple_actions, card, multiple_ability, ix+1)
            self.display_available_targets(self.backend.board, card, multiple_ability.action_list[ix+1], bind_, None)

    def handle_multiple_actions(self, ability, card, instance):
        if ability.isinstant:
            for b in self.selected_card_buttons:
                b.disabled = True
            self.display_card_actions(card, False, None)
        self.display_available_targets(self.backend.board, card, ability.action_list[0],
                                           partial(self.bind_multiple_actions, card, ability, 0),  None)

    def display_available_targets(self, board, card, ability, bind_, instance):
        self.destroy_target_marks()
        b_size = 30  # размер квадратика
        if ability.targets == 'all':
            targets = board.get_all_cards()
        elif ability.targets == 'ally':
            all_cards = board.get_all_cards()
            targets = [x for x in all_cards if x.player == card.player]
        elif ability.targets == 'enemy':
            all_cards = board.get_all_cards()
            targets = [x for x in all_cards if x.player != card.player]
        elif callable(ability.targets):
            targets = ability.targets()
        elif card.type_ == CreatureType.CREATURE and not card.can_hit_flyer:
            targets = board.get_ground_targets_min_max(card_pos_no=board.game_board.index(card),
                                        range_max=ability.range_max, range_min=ability.range_min, ability=ability)
        elif card.type_ == CreatureType.FLYER or card.can_hit_flyer:
            targets = board.get_available_targets_flyer(card)
        for t in targets:
            with self.cards_dict[t].canvas:
                btn = Button(pos=(0,0),
                             background_color=(1, 1, 1, 0.0),
                             size=(CARD_X_SIZE, CARD_Y_SIZE), size_hint=(None, None))
                if t.player == card.player:
                    c = Color(1, 1, 1, 0.8)
                else:
                    c = Color(1, 0, 0, 1)
                rect1 = Rectangle(pos=(CARD_X_SIZE / 2 - b_size / 2,
                              CARD_Y_SIZE / 2 - b_size / 2),
                         background_color=c,
                         size=(b_size, b_size), size_hint=(1, 1))
                c = Color(1, 1, 1, 0.15)
                rect2 = Rectangle(size=(CARD_X_SIZE, CARD_Y_SIZE ),
                                  background_color=c,
                                  pos=(0,0), size_hint=(1, 1))
                self.target_rectangles.append((rect1, self.cards_dict[t].canvas))
                self.target_rectangles.append((rect2, self.cards_dict[t].canvas))
                if bind_:
                    btn.bind(on_press=partial(bind_, t))
                else:
                    btn.bind(on_press=partial(self.start_stack_action, ability, card, t))
                self.cards_dict[t].add_widget(btn)

                self.target_marks_buttons.append(t)
                self.target_marks_cards.append([btn, self.cards_dict[t]])

    def add_fishka(self, card, *args):
        # self.check_all_passed(None)
        close = True
        self.destroy_target_marks()
        if args:
            close = args[0]
        if card.curr_fishka < card.max_fishka:
            card.curr_fishka += 1
            if card not in self.fishka_label_dict:
                self.add_fishki_gui(card)
            else:
                self.fishka_label_dict[card].text = str(card.curr_fishka)
            if close:
                card.actions_left -= 1
                self.tap_card(card)

    def add_fishki_gui(self, card):
        base_overlay = self.base_overlays[card]
        rl = RelativeLayout()
        with rl.canvas:
            Color(0, 0, 0.8)
            Rectangle(size=(CARD_X_SIZE * 0.15, CARD_Y_SIZE * 0.15), color=(1, 1, 1, 0.3),
                      pos=(0, CARD_Y_SIZE * 0.70))  # pos_hint={'x':0, 'y':0.8}
            Color(1, 1, 1)
            Line(width=0.5, color=(1, 1, 1, 0),
                 rectangle=(0, CARD_Y_SIZE * 0.70, CARD_X_SIZE * 0.15, CARD_Y_SIZE * 0.15))
            lbl = Label(pos=(0, CARD_Y_SIZE * 0.70), text=f'{card.curr_fishka}', color=(1, 1, 1, 1),
                        size=(CARD_X_SIZE * 0.15, CARD_Y_SIZE * 0.15),
                        font_size=Window.height * 0.02, valign='top')
            self.fishka_label_dict[card] = lbl
        base_overlay.add_widget(rl)
        self.fishka_dict[card] = rl

    def remove_fishki_gui(self, card):
        if card in self.fishka_label_dict:
            del self.fishka_label_dict[card]
        try:
            base_overlay = self.base_overlays[card]
            base_overlay.remove_widget(self.fishka_dict[card])
        except:
            pass

    def remove_fishka(self, card, no, *args):
        if callable(no):
            cost = no()
        else:
            cost = no
        if card.curr_fishka >= cost:
            card.curr_fishka -= cost
        if card.curr_fishka == 0:
            self.remove_fishki_gui(card)
        else:
            self.fishka_label_dict[card].text = str(card.curr_fishka)

    def display_card_actions(self, card, show_slow, instance):
        if self.backend.curr_priority == card.player:
            disabled_ = operator.not_(bool(card.actions_left))
        else:
            disabled_ = True

        ground_1 = [x for x in [x for x in self.backend.board.game_board if not isinstance(x, int)] if x.player == 1]
        ground_2 = [x for x in [x for x in self.backend.board.game_board if not isinstance(x, int)] if x.player == 2]
        add_tap_for_flyer_flag = True
        for el in card.abilities:
            if isinstance(el, TapToHitFlyerAction):
                add_tap_for_flyer_flag = False
        if self.backend.current_active_player == 1 and card.player == 1 and len(ground_2) == 0 \
                and card.type_ == CreatureType.CREATURE and add_tap_for_flyer_flag:
            card.abilities.append(TapToHitFlyerAction())
        elif self.backend.current_active_player == 2 and card.player == 2 and len(ground_1) == 0 \
                and card.type_ == CreatureType.CREATURE and add_tap_for_flyer_flag:
            card.abilities.append(TapToHitFlyerAction())

        displayable = [x for x in card.abilities if not (isinstance(x, TriggerBasedCardAction) and not x.display)]
        for i, ability in enumerate(displayable):
            if self.backend.in_stack:
                if not ability.isinstant:
                    disabled_ = True
                elif card.player == self.backend.curr_priority:
                    disabled_ = False
            if not show_slow and not ability.isinstant:
                disabled_ = True
            elif not show_slow and ability.isinstant:
                disabled_ = False
            btn = Button(text=ability.txt,
                          pos=(Window.width * 0.84, Window.height * 0.20 - i * 0.04 * Window.height),
                          disabled=disabled_, background_color=(1,0,0,1), border=[1,1,1,1],
                          size=(Window.width * 0.14, Window.height * 0.04),)# size_hint=(None, None))
            if isinstance(ability, SimpleCardAction) or isinstance(ability, FishkaCardAction):
                btn.bind(on_press=partial(self.display_available_targets, self.backend.board, card, ability, None))
            elif isinstance(ability, DefenceAction) or isinstance(ability, IncreaseFishkaAction)\
                    or isinstance(ability, TapToHitFlyerAction):
                btn.bind(on_press=partial(self.start_stack_action, ability, card, ability))
            elif isinstance(ability, MultipleCardAction):
                btn.bind(on_press=partial(self.handle_multiple_actions, ability, card))
            self.root.add_widget(btn)
            self.selected_card_buttons.append(btn)

    def draw_card_overlay(self, *args):
        card = args[0]
        turned = args[1]  # 0 - initial, 1 - tapped, 2 - untapped
        if turned == 3:
            size_ = (CARD_X_SIZE, CARD_Y_SIZE * 0.2)
            lyy = self.base_overlays[card]
            ly = RelativeLayout()
            with ly.canvas:
                if card.player == 1:
                    c = Color(1, 1, 0.6, 1)
                    c1 = (0, 0, 0, 1)
                else:
                    c = Color(0.4, 0.5, 1, 1)
                    c1 = (1, 1, 1, 1)
                rect = Rectangle(pos=(0, 0), background_color=c,
                                 size=size_,
                                 font_size=Window.height * 0.02)
                name = (card.name[:12] + '..') if len(card.name) > 14 else card.name
                lbl_ = Label(pos=(0, 0), text=f'{name}', color=c1,
                             size=size_,
                             font_size=Window.height * 0.02, )
                self.card_nameplates.append(lbl_)
                lyy.add_widget(ly)
                self.card_nameplates_dict[card] = ly
        if turned == 1:
            size_ = (CARD_Y_SIZE * 0.2, CARD_X_SIZE)
            lx = self.base_overlays[card]
            with lx.canvas.before:
                PushMatrix()
                self.rotation = Rotate()
                self.rotation.origin = (lx.x+CARD_X_SIZE/2, lx.y+CARD_Y_SIZE/2)
                self.rotation.angle = -90
            with lx.canvas.after:
                PopMatrix()
        else:
            size_ = (CARD_X_SIZE, CARD_Y_SIZE * 0.2)
            if not self.selected_card == card or turned:
                lyy = self.base_overlays[card]
                ly = RelativeLayout()
                self.cards_dict[card].remove_widget(self.card_nameplates_dict[card])
                if turned == 2:
                    with lyy.canvas.before:
                        PushMatrix()
                        self.rotation = Rotate()
                        self.rotation.origin = (ly.x + CARD_X_SIZE / 2, ly.y + CARD_Y_SIZE / 2)
                        self.rotation.angle = 90
                    with lyy.canvas.after:
                        PopMatrix()
                with ly.canvas:
                    if card.player == 1:
                        c = Color(1, 1, 0.6, 1)
                        c1 = (0, 0, 0, 1)
                    else:
                        c = Color(0.4, 0.5, 1, 1)
                        c1 = (1, 1, 1, 1)
                    rect = Rectangle(pos=(0, 0), background_color=c,
                                 size=size_,
                                 font_size=Window.height * 0.02)
                    name = (card.name[:12] + '..') if len(card.name) > 14 else card.name
                    lbl_ = Label(pos=(0, 0), text=f'{name}', color=c1,
                                 size=size_,
                                 font_size=Window.height * 0.02,)
                    self.card_nameplates.append(lbl_)
                    lyy.add_widget(ly)
                    self.card_nameplates_dict[card] = ly

    def bright_card_overlay(self, card):
        lyy = self.base_overlays[card]
        self.cards_dict[card].remove_widget(self.card_nameplates_dict[card])
        ly = RelativeLayout()
        with ly.canvas:
            if card.player == 1:
                c = Color(1, 1, 0, 1)
                c1 = (0, 0, 0, 1)
            else:
                c = Color(0.1, 0.1, 1, 1)
                c1 = (1, 1, 1, 1)
            rect = Rectangle(pos=(0, 0), background_color=c,
                             size=(CARD_X_SIZE, CARD_Y_SIZE * 0.2),
                             font_size=Window.height * 0.02)
            name = (card.name[:12] + '..') if len(card.name) > 14 else card.name
            lbl_ = Label(pos=(0, 0), text=f'{name}', color=c1,
                         size=(CARD_X_SIZE, CARD_Y_SIZE * 0.2),
                         font_size=Window.height * 0.02, )
            self.card_nameplates.append(lbl_)
            self.card_nameplates_dict[card] = ly
        lyy.add_widget(ly)

    def reveal_cards(self, cards):
        for card in cards:
            loc = card.loc
            if card.type_ == CreatureType.FLYER:
                x, y = self.dz1_btn.pos
                rl1 = RelativeLayout(size=(CARD_X_SIZE, CARD_Y_SIZE))
                btn1 = Button(disabled=False,
                              background_normal=card.pic, pos=(0, CARD_Y_SIZE*0.2),
                              size=(CARD_X_SIZE, CARD_Y_SIZE*0.8), size_hint=(None, None))
                # update backend
                self.backend.board.game_board[card.loc] = 0
                card.loc = -1
                if card.player == 1:
                    self.dop_zone_1_gl.add_widget(rl1)
                    self.dop_zone_1_buttons.append(rl1)
                    self.backend.board.extra1.append(card)
                elif card.player == 2:
                    self.dop_zone_2_gl.add_widget(rl1)
                    self.dop_zone_2_buttons.append(rl1)
                    self.backend.board.extra2.append(card)
            else:
                x, y = self.card_position_coords[loc]
                rl1 = RelativeLayout(pos=(x, y))
                btn1 = Button(disabled=False,  pos=(0, CARD_Y_SIZE*0.2),
                          background_normal=card.pic, size=(CARD_X_SIZE, CARD_Y_SIZE*0.8)
                          , size_hint=(None, None))

            btn1.bind(on_press=partial(self.on_click_on_card, card))
            rl1.add_widget(btn1)

            base_overlay_layout = RelativeLayout()
            with base_overlay_layout.canvas:
                # Life
                Color(0, 0.3, 0.1)
                Rectangle(size=(CARD_X_SIZE*0.33, CARD_Y_SIZE*0.15), color=(1,1,1,0.3),
                          pos=(0, CARD_Y_SIZE*0.85)) #pos_hint={'x':0, 'y':0.8}
                Color(1, 1, 1)
                Line(width=0.5, color=(1,1,1,0), rectangle=(0,CARD_Y_SIZE*0.85, CARD_X_SIZE*0.33, CARD_Y_SIZE*0.15))
                lbl = Label(pos=(0, CARD_Y_SIZE*0.85), text=f'{card.life}/{card.life}', color=(1, 1, 1, 1), size=(CARD_X_SIZE * 0.3, CARD_Y_SIZE * 0.15),
                   font_size=Window.height*0.02, valign='top')
                self.hp_label_dict[card] = lbl
                # Movement
                Color(0.6, 0, 0)
                Rectangle(pos=(CARD_X_SIZE * 0.73, CARD_Y_SIZE * 0.85), size=(CARD_X_SIZE * 0.27, CARD_Y_SIZE * 0.15),
                          color=(1, 1, 1, 0.3), pos_hint=(None, None))
                Color(1, 1, 1)
                Line(width=0.5, color=(1, 1, 1, 0),
                     rectangle=(CARD_X_SIZE * 0.74, CARD_Y_SIZE*0.85, CARD_X_SIZE * 0.25, CARD_Y_SIZE*0.15))
                lbl = Label(pos=(CARD_X_SIZE * 0.73, CARD_Y_SIZE * 0.85), text=f'{card.move}/{card.move}', color=(1, 1, 1, 1),
                            size=(CARD_X_SIZE * 0.3, CARD_Y_SIZE * 0.15),
                            pos_hint=(None, None), font_size=Window.height*0.02)
                self.move_label_dict[card] = lbl
                if card.curr_fishka > 0:
                    self.add_fishki_gui(card)


            self.base_overlays[card] = base_overlay_layout
            Clock.schedule_once(partial(self.draw_card_overlay, card, 0), 0.1)
            rl1.add_widget(base_overlay_layout)
            self.cards_dict[card] = rl1
            if card.type_ == CreatureType.CREATURE:
                self.layout.add_widget(rl1)
            self.update_zone_counters()

    def update_zone_counters(self):
        zones = [(self.dz1_btn, 'extra1', 'Доп. зона'), (self.dz2_btn, 'extra2', 'Доп. зона'),
                 (self.grave1_btn, 'grave1', 'Кладбище'), (self.grave2_btn, 'grave2', 'Кладбище')]
        for btn, fld, base_txt in zones:
            btn.text = base_txt + ' ('+str(self.backend.board.get_zone_count(fld))+')'

    def hide_scroll(self, sv, butt, pos1, pos2, border, player, instance):
        """
        Hides scroll + border
        """
        sv.size = DZ_SIZE
        l1_x, l1_y = sv.size
        border.rectangle = (*sv.pos, l1_x, l1_y)
        sv.disabled = False
        sv.opacity = 1
        butt.pos = pos1
        if player == 1:
            for scroll, butt1, border1, p1 in self.extra_scrolls_1:
                if scroll != sv:
                    scroll.disabled = True
                    scroll.opacity = 0
                    scroll.size = (0, 0)
                    border1.rectangle = (0, 0, 0, 0)
                    if butt == self.deck1_btn and butt1==self.grave1_btn:
                        x, y = p1
                        butt1.pos = (x, y-0.021*Window.width)
                    else:
                        butt1.pos = p1
        else:
            for scroll, butt1, border1, p1 in self.extra_scrolls_2:
                if scroll != sv:
                    scroll.disabled = True
                    scroll.opacity = 0
                    scroll.size = (0, 0)
                    border1.rectangle = (0, 0, 0, 0)
                    butt1.pos = p1

    def update_timer_text(self, instance):
        if self.backend.curr_game_state == game_properties.GameStates.MAIN_PHASE:
            self.timer_label.text = game_properties.state_to_str[self.backend.curr_game_state] + ' игрока ' + str(self.backend.current_active_player)
        else:
            self.timer_label.text = game_properties.state_to_str[self.backend.curr_game_state]

    def timer_update(self, duration, instance, value, completion_ratio):
        try:
            minutes = int(completion_ratio * duration) // 60
            rem_m = (duration - int(completion_ratio * duration)) // 60
        except ZeroDivisionError:
            minutes = 0
            rem_m = 0
        total_min = duration//60
        seconds = completion_ratio * duration - minutes * 60
        # Weired bar behaviour for low width values
        if (Window.width * 0.15) * (1 - completion_ratio) > Window.width * 0.01:
            bar_w = (Window.width * 0.15) * (1 - completion_ratio)
        else:
            bar_w = Window.width * 0.01
        self.timer_bar.size = (bar_w, Window.height * 0.03)
        if self.backend.in_stack:
            txt = game_properties.state_to_str[self.backend.curr_game_state] + ' Прио ' + str(self.backend.curr_priority)
        else:
            if self.backend.curr_game_state == game_properties.GameStates.MAIN_PHASE:
                txt = game_properties.state_to_str[self.backend.curr_game_state] + ' игрока ' + str(self.backend.current_active_player)
            else:
                txt = game_properties.state_to_str[self.backend.curr_game_state]
        self.timer_label.text = txt + ' ' + str(int(total_min-minutes))+':'+str(int(duration-rem_m*60-seconds)).zfill(2)

    def start_timer(self, *args):
        duration = args[0]
        if hasattr(self, 'timer'):
            self.timer.cancel(self.timer_label)
        if hasattr(self, 'timer_ly'):
            self.root.remove_widget(self.timer_ly)
        self.timer_ly = RelativeLayout()
        with self.timer_ly.canvas:
            self.timer_bar_back = BorderImage(size=(Window.width * 0.15, Window.height * 0.03),
                                              pos=(Window.width * 0.83, Window.height * 0.35),
                                              color=Color(0.6, 0.15, 0, 1), minimum_width=0)
            self.timer_bar = BorderImage(size=(Window.width * 0.15, Window.height * 0.03),
                                         pos=(Window.width * 0.83, Window.height * 0.35),
                                        color=Color(1,1,0.3,1), minimum_width=0)
            if self.backend.in_stack:
                txt = 'Приоритет игрока '+str(self.backend.curr_priority)
            else:
                txt = game_properties.state_to_str[self.backend.curr_game_state]
            self.lbl = Label(text=txt,
                        pos=(Window.width * 0.88, Window.height * 0.35), color=(0, 0, 0, 1),
                        size=(CARD_X_SIZE * 0.3, CARD_Y_SIZE * 0.2),
                        pos_hint=(None, None), font_size=str(Window.height * 0.016))
            self.timer_label = self.lbl
        self.root.add_widget(self.timer_ly)
        self.timer = Animation(s=1 / 30, duration=duration)
        self.timer.bind(on_progress=partial(self.timer_update, duration))
        self.timer.start(self.timer_label)
        if self.backend.in_stack:
            self.timer.bind(on_complete=self.backend.player_passed)
            self.timer.bind(on_complete=Clock.schedule_once(self.check_all_passed))
            self.timer.bind(on_complete=partial(self.start_timer, STACK_DURATION))
            #Clock.schedule_once(self.check_all_passed)
        else:
            if self.selected_card:
                if self.backend.passed_once and self.backend.current_active_player == self.selected_card.player\
                        and self.backend.curr_game_state == GameStates.MAIN_PHASE and self.selected_card.actions_left > 0:
                    self.display_card_actions(self.selected_card, True, None)
            self.timer.bind(on_complete=self.backend.next_game_state)
        self.timer.bind(on_complete=partial(self.start_timer, duration))

    def disable_all_buttons_except_instant(self, cards):
        self.destroy_target_marks()
        self.destroy_target_rectangles()
        if self.selected_card.player not in cards:
            for b in self.selected_card_buttons:
                b.disabled = True
        self.stack_cards = cards

    def disable_all_non_instant_actions(self):
        if self.selected_card:
            self.display_card_actions(self.selected_card, False, None)

    def buttons_on_priority_switch(self):
        if self.selected_card and not self.selected_card.tapped and self.selected_card.actions_left > 0:
            if self.selected_card.player != self.backend.curr_priority:
                for b in self.selected_card_buttons:
                    if not b.disabled:
                        b.disabled = True
            else:
                self.display_card_actions(self.selected_card, True, None)

    def add_dopzones(self, position_scroll, position_butt, position_butt2, zone_name, button_name, gl_name, txt, player):
        if zone_name == 'dop_zone_1' or zone_name == 'dop_zone_2':
            size_ = (CARD_X_SIZE, Window.height * 0.45)
        else:
            size_ = (0, 0)
        scroll = ScrollView(bar_pos_x='top', always_overscroll=False, do_scroll_x=False,
                                     size=size_, size_hint=(None, None),
                                     pos=position_scroll)

        gl = GridLayout(cols=1, size_hint=(1, None), row_default_height=CARD_Y_SIZE)
        gl.bind(minimum_height=gl.setter('height'))
        scroll.add_widget(gl)
        butt = Button(text=txt, size_hint=(None, None), size=(Window.width * 0.12, Window.height * 0.04),
                              pos=position_butt2, background_color=(1,0,0,1))

        with self.layout.canvas:  # zone borders
            l1_x, l1_y = scroll.size
            c = Color(0.8, 0.4, 0, 1)
            border = Line(width=3, color=c, rectangle=(*scroll.pos, l1_x, l1_y))
        butt.bind(on_press=partial(self.hide_scroll, scroll, butt, position_butt, position_butt2, border,
                                   player))

        if player == 1:
            self.extra_scrolls_1.append((scroll, butt, border, position_butt2))
        else:
            self.extra_scrolls_2.append((scroll, butt, border, position_butt2))

        setattr(self, gl_name, gl)
        setattr(self, zone_name, scroll)
        setattr(self, button_name, butt)
        self.root.add_widget(scroll)
        self.root.add_widget(butt)

    def build(self):
        root = MainField()
        with root.canvas:
            root.bg_rect = Rectangle(source='data/bg/dark_bg_7.jpg', pos=root.pos, size=Window.size)
        root.add_widget(Vertical())
        root.add_widget(Horizontal())

        # generate board coords
        self.layout = FloatLayout(size=(Window.width * 0.8, Window.height))
        self.card_position_coords = []
        self.nav_buttons = []
        self.selected_card_buttons = []
        self.selected_card = None
        self.defender_set = False
        self.pending_attack = None
        self.target_marks_buttons = []
        self.hp_label_dict = {}
        self.move_label_dict = {}
        self.fishka_label_dict = {}
        self.cards_dict = {}
        self.fishka_dict = {}
        self.die_pics = []
        self.red_arrows = []
        self.card_nameplates = []
        self.target_rectangles = []
        self.target_marks_cards = []
        self.card_nameplates_dict = collections.defaultdict(RelativeLayout)
        self.base_overlays = {}
        self.damage_marks = []
        self.count_of_flyers_1 = 0
        self.selection_flicker_dict = {}
        self.stack_cards = []
        self.multiple_targets_list = []
        self.grave_buttons_1 = []
        self.grave_buttons_2 = []
        self.garbage = []

        for i in range(5):
            for j in range(6):
                btn1 = Button(text=str(i * 6 + j), disabled=False, opacity=0.8,
                              pos=(Window.width * 0.25 + i * CARD_X_SIZE,
                                   Window.height * 0.03 + j * CARD_Y_SIZE),
                              size=(CARD_X_SIZE, CARD_Y_SIZE), size_hint=(None, None))
                self.card_position_coords.append((btn1.x, btn1.y))
                #self.layout.add_widget(btn1)

        # when user clicked on square outside red move marks
        Window.bind(on_touch_down=self.delete_move_marks_on_unfocus)
        # when user clicked on square outside target card
        Window.bind(on_touch_down=self.delete_target_marks_on_unfocus)
        # popup on right click
        Window.bind(on_touch_down=self.card_popup)
        Window.bind(on_touch_up=self.card_popup_destr)
        root.add_widget(self.layout)

        # Button for phase skip
        self.ph_button = Button(text="Пропустить", disabled=True,
                              pos=(Window.width * 0.83, Window.height * 0.28), background_color=(1,0,0,1),
                                   size=(Window.width * 0.08, Window.height * 0.05), size_hint=(None, None))
        self.ph_button.bind(on_press=self.backend.player_passed)
        self.ph_button.bind(on_press=Clock.schedule_once(self.check_all_passed))
        self.ph_button.bind(on_press=partial(self.start_timer, STACK_DURATION))
        self.ph_button.bind(on_press=self.destroy_flickering)
        self.layout.add_widget(self.ph_button)

        # Button for end of turn
        self.eot_button = Button(text="Сл. Фаза", disabled=False,
                           pos=(Window.width * 0.91, Window.height * 0.28), background_color=(1,0,0,1),
                           size=(Window.width * 0.08, Window.height * 0.05), size_hint=(None, None))
        self.eot_button.bind(on_press=self.backend.next_game_state)
        self.eot_button.bind(on_press=Clock.schedule_once(self.update_timer_text, ))
        self.eot_button.bind(on_press=partial(self.start_timer, TURN_DURATION))
        self.layout.add_widget(self.eot_button)

        self.timer_label = Label()
        self.backend.start()
        Clock.schedule_once(lambda x: self.start_timer(TURN_DURATION), 1)  # BUGGY?

        # Extra zones sliders
        self.dop_zone_1_buttons = []
        self.dop_zone_2_buttons = []
        self.extra_scrolls_1 = []
        self.extra_scrolls_2 = []
        Clock.schedule_once(lambda x: self.add_dopzones(position_scroll=(Window.width * 0.85, Window.height * 0.48),  # 1-ая доп. зона
                                                         position_butt=(Window.width * 0.84, Window.height * 0.93),
                                                        position_butt2=(Window.width * 0.84, Window.height * 0.93),
                                                        zone_name='dop_zone_1', player=1,
                                                        button_name='dz1_btn', gl_name='dop_zone_1_gl', txt='Доп. зона'))
        Clock.schedule_once(lambda x: self.add_dopzones(position_scroll=(Window.width * 0.03, Window.height * 0.48),  # 2-ая доп. зона
                                                        position_butt=(Window.width * 0.01, Window.height * 0.93),
                                                        position_butt2=(Window.width * 0.01, Window.height * 0.93),
                                                        zone_name='dop_zone_2', player=2,
                                                        button_name='dz2_btn', gl_name='dop_zone_2_gl', txt='Доп. зона'))
        Clock.schedule_once(lambda x: self.add_dopzones(position_scroll=(Window.width * 0.85, Window.height * 0.43),  #  1-ое кладбище
                                                        position_butt=(Window.width * 0.84, Window.height * 0.89),
                                                        position_butt2=(Window.width * 0.84, Window.height * 0.43),
                                                        zone_name='grave_1', player=1,
                                                        button_name='grave1_btn', gl_name='grave_1_gl', txt='Кладбище'))
        Clock.schedule_once(lambda x: self.add_dopzones(position_scroll=(Window.width * 0.03, Window.height * 0.43),  #  2-ое кладбище
                                                        position_butt=(Window.width * 0.01, Window.height * 0.89),
                                                        position_butt2=(Window.width * 0.01, Window.height * 0.43),
                                                        zone_name='grave_2', player=2,
                                                        button_name='grave2_btn', gl_name='grave_2_gl', txt='Кладбище'))
        Clock.schedule_once(lambda x: self.add_dopzones(position_scroll=(Window.width * 0.85, Window.height * 0.43),  # 1-ая колода
                                        position_butt=(Window.width * 0.84, Window.height * 0.89),
                                        position_butt2=(Window.width * 0.84, Window.height * 0.39),
                                        zone_name='deck_1', player=1,
                                        button_name='deck1_btn', gl_name='deck_1_gl', txt='Колода'))

        # timeout otherwise some parts are not rendered
        Clock.schedule_once(lambda x: self.reveal_cards(self.backend.input_cards1))
        Clock.schedule_once(lambda x: self.reveal_cards(self.backend.input_cards2))

        return root



