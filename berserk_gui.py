import os
import kivy
kivy.require('2.0.1')
from kivy import Config
Config.set('input', 'mouse', 'mouse,multitouch_on_demand')
from kivy.core.window import Window
from kivy.uix.floatlayout import FloatLayout
from kivy.app import App
from kivy.uix.gridlayout import GridLayout
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.behaviors import DragBehavior
from kivy.uix.scrollview import ScrollView
from kivy.uix.popup import Popup
from kivy.uix.button import Button
from kivy.uix.widget import Widget
from kivy.core.audio import SoundLoader
from kivy.uix.label import Label
from kivy.graphics import Line, Color, Rectangle, PushMatrix, Rotate, PopMatrix, Ellipse
import numpy.random as rng
from kivy.clock import Clock
from kivy.animation import Animation
from functools import partial
from kivy.uix.image import Image
from kivy.graphics.vertex_instructions import BorderImage
import game_properties
import operator
from cards.card_properties import *
from copy import copy
from collections import defaultdict

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
        self.title = ''
        self.separator_height = 0

    def on_pos(self, *args):
        self.drag_rectangle = [self.x, self.y, self.width, self.height]

    def on_size(self, *args):
        self.drag_rectangle = [self.x, self.y, self.width, self.height]

    def _align_center(self, *l):
        pass


class BerserkApp(App):

    def __init__(self, backend, window_size, stack_duration=30, turn_duration=60):
        super(BerserkApp, self).__init__()
        self.backend = backend
        Window.size = window_size
        if window_size == (1920, 1080):
            Window.maximize()
        global CARD_X_SIZE, CARD_Y_SIZE, STACK_DURATION, TURN_DURATION, DZ_SIZE
        CARD_X_SIZE = (Window.width * 0.084375)
        CARD_Y_SIZE = CARD_X_SIZE  # (Window.height * 0.15)

        STACK_DURATION = stack_duration
        TURN_DURATION = turn_duration

        DZ_SIZE = (CARD_X_SIZE, Window.height * 0.45)
        self.title = 'Berserk Renewal'

    def open_settings(self, *largs):
        pass

    def destroy_x(self, list_, long=False):
        if long==True:
            for bt, a in list_:
                self.root.remove_widget(bt)
        else:
            for bt in list_:
                self.root.remove_widget(bt)

    def lambda_disabled_actions(self, *args):
        self.disabled_actions = True
        self.eot_button.disabled = True

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
        if self.disabled_actions:
            return
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
                self.destroy_flickering()
                self.multiple_targets_list = []  # здесь копятся цели для многоступенчатых действий
                Clock.schedule_once(partial(self.destroy_x, self.die_pics), 1)
                self.die_pics = []

    def destroy_flickering(self, *args):
        for c in self.selection_flicker_dict.keys():
            self.base_overlays[c].remove_widget(self.selection_flicker_dict[c])

    def check_displayable_card_actions(self, card):
        out = []
        for ability in card.abilities:
            if isinstance(ability, MultipleCardAction):
                code = 1
                for abil in ability.action_list:
                    if isinstance(abil, FishkaCardAction):
                        if (isinstance(abil.cost_fishka, int) and abil.cost_fishka > card.curr_fishka) or \
                                (callable(abil.cost_fishka) and abil.cost_fishka() > card.curr_fishka):
                            code = 0
                out.append((ability, code))
            elif isinstance(ability, FishkaCardAction):
                if (isinstance(ability.cost_fishka, int) and ability.cost_fishka <= card.curr_fishka) or \
                        (callable(ability.cost_fishka) and ability.cost_fishka() <= card.curr_fishka):
                            out.append((ability, 1))
                else:
                    out.append((ability, 0))
            elif isinstance(ability, IncreaseFishkaAction) and card.curr_fishka >= card.max_fishka:
                out.append((ability, 0))
            elif isinstance(ability, TriggerBasedCardAction) and ability.disabled:
                out.append((ability, 0))
            elif isinstance(ability, DefenceAction) and ability.disabled:
                out.append((ability, 0))
            elif card.actions_left < 0:
                out.append((ability, 0))
            else:
                out.append((ability, 1))
        displayable = [x for x in out if not (isinstance(x[0], TriggerBasedCardAction) and not x[0].display)]
        return displayable

    def add_pereraspredelenie_marker(self, card):
        ly = self.base_overlays[card]
        if self.pereraspredelenie_label_dict[card] == 0:
            self.pereraspredelenie_label_dict[card] += 1
            rl = RelativeLayout()
            with rl.canvas:
                Color(0.8, 0, 0)
                Rectangle(size=(CARD_X_SIZE * 0.15, CARD_Y_SIZE * 0.15), color=(1, 1, 1, 0.3),
                          pos=(CARD_X_SIZE*0.85, CARD_Y_SIZE * 0.70))
                Color(1, 1, 1)
                Line(width=0.5, color=(1, 1, 1, 0),
                     rectangle=(CARD_X_SIZE*0.85, CARD_Y_SIZE * 0.70, CARD_X_SIZE * 0.15, CARD_Y_SIZE * 0.15))
                lbl = Label(pos=(CARD_X_SIZE*0.85, CARD_Y_SIZE * 0.70), text=str(self.pereraspredelenie_label_dict[card]), color=(1, 1, 1, 1),
                            size=(CARD_X_SIZE * 0.15, CARD_Y_SIZE * 0.15),
                            font_size=Window.height * 0.02, valign='top')
                self.garbage_dict[card] = lbl
                ly.add_widget(rl)
                self.pereraspredelenie_dict[card] = rl
        else:
            self.pereraspredelenie_label_dict[card] += 1
            self.garbage_dict[card].text = str(self.pereraspredelenie_label_dict[card])

    def unhide(self, card):
        if hasattr(card, 'hidden') and card.hidden:
            card.hidden = False
            rl = self.cards_dict[card]
            try:
                del self.base_overlays[card]
            except:
                pass
            self.layout.remove_widget(rl)
            self.reveal_cards([card])

    def remove_pereraspredelenie_ran(self):
        all_cards = self.backend.board.get_all_cards()
        try:
            for card in all_cards:
                if card in self.pereraspredelenie_dict.keys():
                    ly = self.base_overlays[card]
                    self.pereraspredelenie_label_dict[card] = 0
                    ly.remove_widget(self.pereraspredelenie_dict[card])
        except Exception as e:
            print('Error on remove_pereraspredelenie_ran', e)

    def popup_attack_bind(self, result, ability, card, victim, *args):
        self.timer_ability.unbind(on_complete=self.press_1)
        if hasattr(self, 'attack_popup'):
            self.attack_popup.dismiss()
            del self.attack_popup
        a, b = result
        if a:
            ability.damage_make = ability.damage[a - 1]
        else:
            ability.damage_make = 0
        if b:
            ability.damage_receive = victim.attack[b - 1]
        else:
            ability.damage_receive = 0

        instants = self.backend.board.get_instants()
        # if instants: TODO
        #     self.backend.passed_1 = False
        #     self.backend.passed_2 = False
        # else:
        Clock.schedule_once(lambda x: self.destroy_red_arrows(), 2)
        self.backend.passed_1 = True
        self.backend.passed_2 = True
        self.perform_card_action((ability, card, victim, 2))

    def destroy_card(self, card, is_ubiranie_v_colodu=False):
        cb = self.backend.board.get_all_cards_with_callback(Condition.ANYCREATUREDEATH)
        if cb and not is_ubiranie_v_colodu:
            for c, a in cb:
                self.reset_passage()
                self.backend.stack.append((a, c, None, 0))
                self.process_stack()
        if card.type_ == CreatureType.FLYER:
            if card.player == 1:
                self.dop_zone_1.children[0].remove_widget(self.cards_dict[card])
            else:
                self.dop_zone_2.children[0].remove_widget(self.cards_dict[card])
        else:
            self.layout.remove_widget(self.cards_dict[card])
        self.backend.board.remove_card(card)
        del self.cards_dict[card]
        card.alive = False

        rl1 = RelativeLayout(size=(CARD_X_SIZE, CARD_Y_SIZE))
        btn1 = Button(disabled=False,
                      background_normal=card.pic, pos=(0, CARD_Y_SIZE * 0.16),
                      size=(CARD_X_SIZE, CARD_Y_SIZE * 0.84), size_hint=(None, None))
        card.loc = -1
        self.base_overlays[card] = RelativeLayout()
        if card.player == 1:
            self.grave_1_gl.add_widget(rl1)
            self.grave_buttons_1.append(rl1)
            self.backend.board.grave1.append(card)
        elif card.player == 2:
            self.grave_2_gl.add_widget(rl1)
            self.grave_buttons_2.append(rl1)
            self.backend.board.grave2.append(card)
        self.cards_dict[card] = rl1
        self.draw_card_overlay(card, 3)
        rl1.add_widget(btn1)
        rl1.add_widget(self.base_overlays[card])
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
        try:
            if abs(dmg) < 3:
                sound = SoundLoader.load('data/sound/weak_punch.wav')
            elif 3 <= abs(dmg) < 5:
                sound = SoundLoader.load('data/sound/med_punch.wav')
            elif abs(dmg) >= 5:
                sound = SoundLoader.load('data/sound/hard_punch.wav')
            else:
                return
            sound.play()
        except Exception as e:
            print(e)

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
        stroy_neighbors_old = self.backend.board.get_adjacent_with_stroy(card.loc)
        self.backend.board.update_board(card.loc, move, card)
        card.loc = move
        self.move_label_dict[card].text = f'{card.curr_move}/{card.move}'

        stroy_neighbors_new = self.backend.board.get_adjacent_with_stroy(card.loc)  # Строй
        if len(stroy_neighbors_new) != 0 and not card.in_stroy and card.stroy_in:
            card.stroy_in()
            for neigh in stroy_neighbors_new:
                if not neigh.in_stroy:
                    neigh.stroy_in()
        elif len(stroy_neighbors_new) == 0 and card.in_stroy:
            card.stroy_out()
        if len(stroy_neighbors_old) != 0:
            for neigh in stroy_neighbors_old:
                if len(self.backend.board.get_adjacent_with_stroy(neigh.loc)) == 0 and neigh.stroy_out:
                    neigh.stroy_out()

        cb = self.backend.board.get_all_cards_with_callback(Condition.ON_SELF_MOVING)
        for c, a in cb:
            if c.player == self.backend.current_active_player and a.check():
                self.start_stack_action(a, c, c, 0)
                #Clock.schedule_once(self.process_stack)

    def check_game_end(self):
        cards = self.backend.board.get_all_cards()
        if not cards:
            popup = OmegaPopup(title='', separator_height=0, overlay_color=(0, 0, 0, 0),
                      content=Label(text='Ничья!', font_size=Window.height*0.07), background_color=(1, 0, 0, 1),
                      size_hint=(None, None), size=(Window.width*0.4, Window.height / 4))
            popup.open()
        elif len([c for c in cards if c.player == 1]) == 0:
            popup = OmegaPopup(title='', separator_height=0,overlay_color=(0, 0, 0, 0),
                          content=Label(text='Победа игрока 2!', font_size=Window.height*0.07),background_color=(1, 0, 0, 1),
                          size_hint=(None, None), size=(Window.width*0.4, Window.height / 4))
            popup.open()
        elif len([c for c in cards if c.player == 2]) == 0:
            popup = OmegaPopup(title='', separator_height=0, overlay_color=(0, 0, 0, 0),
                          content=Label(text='Победа игрока 1!', font_size=Window.height*0.07),background_color=(1, 0, 0, 1),
                               size_hint=(None, None), size=(Window.width*0.4, Window.height / 4))
            popup.open()

    def handle_PRI_ATAKE(self, ability, card, victim, *args):
        all_cards = self.backend.board.get_all_cards()
        if ability.a_type == ActionTypes.ATAKA or ability.a_type == ActionTypes.UDAR_LETAUSHEGO and card in all_cards and victim in all_cards:
            for ab in card.abilities:
                if isinstance(ab, TriggerBasedCardAction) and ab.condition == Condition.PRI_ATAKE:
                    if ab.recieve_inc:
                        ab.callback(victim)
                    else:
                        ab.callback()

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
            #self.red_arrows.append(tri)

    def draw_die(self, bonus1, bonus2, gr1, gr2):
        if isinstance(gr1, int):
            gr1 = [gr1]
        if isinstance(gr2, int):
            gr2 = [gr2]
        if gr1:
            for i, roll in enumerate(gr1):
                r1_i = Image(source=f'data/dice/Alea_{roll}.png', pos=(Window.width * 0.78 - 0.07 * Window.width * i, Window.height * 0.8),
                             size=(0.07 * Window.width, Window.height * 0.07))
                with r1_i.canvas:
                    if bonus1:
                        l = Label(text='+'+str(bonus1), pos=(Window.width * 0.78 - 0.07 * Window.width * i, Window.height * 0.7))
                        self.die_pics.append(l)
                self.root.add_widget(r1_i)
                self.die_pics.append(r1_i)
        if gr2:
            for i, roll in enumerate(gr2):
                r2_i = Image(source=f'data/dice/Alea_{roll}.png', pos=(Window.width * 0.12 + 0.07 * Window.width * i, Window.height * 0.8),
                             size=(0.07 * Window.width, Window.height * 0.07))
                with r2_i.canvas:
                    if bonus2:
                        l = Label(text='+'+str(bonus2), pos=(Window.width * 0.12 + 0.07 * Window.width * i, Window.height * 0.7))
                        self.die_pics.append(l)
                self.root.add_widget(r2_i)
                self.die_pics.append(r2_i)

        Clock.schedule_once(partial(self.destroy_x, self.die_pics), 2)

    def get_pos(self, card):
        if card.type_ == CreatureType.CREATURE and card.alive or card.hidden:
            return self.cards_dict[card].pos
        elif not card.alive:
            if card.player == 1:
                return self.grave_1_gl.to_window(*self.cards_dict[card].pos)
            else:
                return self.grave_2_gl.to_window(*self.cards_dict[card].pos)
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

    def reset_passage(self):
        instants = self.backend.board.get_instants()
        if instants:
            self.backend.passed_1 = False
            self.backend.passed_2 = False
        else:
            self.backend.passed_1 = True
            self.backend.passed_2 = True

    def start_flickering(self, card):
        rl = RelativeLayout()
        self.base_overlays[card].add_widget(rl)
        with rl.canvas:
            col = Color(1, 1, 1, 0.2)
            rect = Rectangle(size=(CARD_X_SIZE, CARD_Y_SIZE),
                             background_color=col,
                             pos=(0, 0), size_hint=(1, 1))
            anim = Animation(opacity=0, duration=0.5) + Animation(opacity=1, duration=0.5)
            anim.repeat = True
            anim.start(rl)
            self.selection_flicker_dict[card] = rl

    def check_for_uniqueness(self, player):
        """ returns for zero or one card """
        all_cards = self.backend.board.get_all_cards()
        consider = [x.name for x in all_cards if x.player == player and x.is_unique]
        d = defaultdict(int)
        for key in consider:
            d[key] += 1
        temp = None
        for key in d.keys():
            if d[key] > 1:
                temp = key
        if temp:
            return [x for x in [x for x in all_cards if x.player == player and x.is_unique] if x.name == temp]
        else:
            return None

    def handle_instant_stack(self, ability, card, victim, state=0, force=0):
        if self.backend.stack:
            for el in self.backend.stack:
                if len(el) == 4:
                    ab, _, _, _ = el
                    if isinstance(ab, DefaultMovementAction) and isinstance(ability, DefaultMovementAction):
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
                if ability.take_all_targets:  # выполняем последний акшен
                    out.append((ability.action_list[-1], card, self.multiple_targets_list, 0))
                else:
                    for i, a in enumerate(ability.action_list):
                        out.append((a, card, self.multiple_targets_list[i], 0))
                if self.proxi_ability:
                    if hasattr(ability, 'inc_ability'):
                        ability.inc_ability = None
                    self.backend.stack.remove(self.proxi_ability)
                    if len(self.proxi_ability) == 2:
                        self.proxi_ability = self.proxi_ability[-1]
                    self.handle_PRI_ATAKE(*self.proxi_ability)
                    # if self.proxi_ability[1].actions_left <= 0:  # tap attacking creature and replace its attack on stack
                    if not card.tapped:
                        self.tap_card(self.proxi_ability[1])
                    self.proxi_ability = None
            else:
                self.multiple_targets_list = []
                self.start_timer(STACK_DURATION)
                self.handle_multiple_actions(ability, card, None)
                return
        else:
            out = (ability, card, victim, 0)
        if (card.actions_left > 0 or force) and not force == -1:
            self.backend.stack.append(out)
            self.multiple_targets_list = []
            if ability.a_type != ActionTypes.MOVEMENT and not isinstance(ability, TriggerBasedCardAction):
                card.actions_left -= 1
            self.able_selected(enable=False)
            self.start_timer(STACK_DURATION)

    def start_stack_action(self, ability, card, victim, state=0, force=0):
        self.destroy_target_rectangles()
        self.destroy_target_marks()
        if (ability.a_type == ActionTypes.ATAKA or ability.a_type == ActionTypes.UDAR_LETAUSHEGO) and \
            not CardEffect.NAPRAVLENNY_UDAR in card.active_status and hasattr(ability, 'can_be_redirected') and ability.can_be_redirected:
            self.defenders = self.backend.board.get_defenders(card, victim)
            if self.defenders:  # Предварительный этап ("при объявлении [текст]")
                self.backend.in_stack = True
                self.eot_button.disabled = True
                self.ph_button.disabled = False
                self.backend.curr_priority = victim.player

                self.draw_red_arrow(self.cards_dict[card], self.cards_dict[victim], card, victim)
                Clock.schedule_once(lambda x: self.destroy_red_arrows(), 3)
                Clock.schedule_once(lambda x: self.start_timer(STACK_DURATION))
                self.disable_all_buttons_except_instant(self.defenders)  # adds to stack_cards
                card.actions_left -= 1
                for c in self.defenders:
                    self.start_flickering(c)
                    c.defence_action.disabled = False
                    c.defence_action.fight_with = card
                self.pending_attack = ability
                self.backend.stack.append((ability, card, victim, 0))
            elif self.backend.board.get_instants():
                self.handle_instant_stack(ability, card, victim)
            else:
                self.perform_card_action(ability, card, victim, 0)
                self.process_stack()
        elif ability.a_type == ActionTypes.ZASCHITA:
            if hasattr(self, 'pending_attack') and self.pending_attack:
                if self.backend.curr_priority == card.player and ability.fight_with:
                    self.destroy_flickering()
                    for c in self.defenders:
                        c.defence_action.disabled = True
                    for a, c, v, stage in self.backend.stack:
                        if a == self.pending_attack:
                            self.backend.stack.remove((a, c, v, stage))
                    self.defender_set = True
                    self.backend.player_passed()
                    Clock.schedule_once(lambda x: self.start_timer(STACK_DURATION))
                    temp_attack = copy(self.pending_attack)  #  deepcopy
                    temp_attack.tap_target = True
                    temp_attack.redirected = True
                    self.pending_attack = None
                    self.backend.stack.append((temp_attack, ability.fight_with, card, 0))
        else:
            instants = self.backend.board.get_instants()
            if instants:  #or self.pending_attack
                self.disable_all_buttons_except_instant(instants)
                self.handle_instant_stack(ability, card, victim, state, force)
            else:
                if isinstance(ability, MultipleCardAction):
                    if len(self.multiple_targets_list) == len(ability.action_list):
                        if ability.take_all_targets:  # выполняем последний акшен
                            self.perform_card_action(ability.action_list[-1], card, self.multiple_targets_list, 0)
                            self.multiple_targets_list = []
                        else:
                            for i, a in enumerate(ability.action_list):
                                self.perform_card_action(a, card, self.multiple_targets_list[i], 0)
                            self.multiple_targets_list = []
                        if self.proxi_ability:
                            if len(self.proxi_ability) == 2:
                                self.proxi_ability = self.proxi_ability[-1]
                            if not card.tapped:  # Might need a check
                                self.tap_card(self.proxi_ability[1])
                            self.handle_PRI_ATAKE(*self.proxi_ability)
                            self.proxi_ability = None
                        self.process_stack()
                    else:
                        if hasattr(ability, 'inc_ability'):
                            ability.inc_ability = None
                        self.handle_multiple_actions(ability, card, None)
                else:
                    self.start_timer(self.timer.duration)
                    self.perform_card_action(ability, card, victim, 0)
                    # self.process_stack()

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

    def process_stack(self, *args):
        # self.disabled_actions = False
        if self.exit_stack:
            return
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
                if not self.eot_button_disabled and not self.disabled_actions:
                    self.eot_button.disabled = False
                self.ph_button.disabled = True
                if not hasattr(self, 'attack_popup'):
                    self.start_timer(self.timer.duration)
                if self.backend.curr_priority != self.backend.current_active_player:
                    self.backend.switch_priority()
            else:
                self.backend.next_game_state()
            return
        while self.backend.stack:
            if self.exit_stack:
                return
            if self.backend.passed_2 and self.backend.passed_1:
                args = self.backend.stack.pop()
                self.perform_card_action(*args)
                self.backend.passed_1 = False
                self.backend.passed_2 = False
            elif not self.backend.board.get_instants():
                args = self.backend.stack.pop()
                self.perform_card_action(*args)
                self.backend.passed_1 = False
                self.backend.passed_2 = False
            else:
                if not hasattr(self, 'attack_popup'):
                    self.start_timer(self.timer.duration)
                    return
                if hasattr(self, 'attack_popup'):
                    try:
                        self.attack_popup.dismiss()
                        del self.attack_popup
                    except:
                        pass
        self.process_stack()

    def cleanup_card(self, new_card):
        try:
            del self.cards_dict[new_card]
            del self.base_overlays[new_card]
            del self.card_signs_imgs[new_card]
            del self.card_signs[new_card]
            del self.hp_label_dict[new_card]
            del self.move_label_dict[new_card]
            del self.pereraspredelenie_label_dict[new_card]
            del self.fishka_label_dict[new_card]
            del self.fishka_dict[new_card]
        except:
            pass
        new_card.curr_life = new_card.life
        new_card.curr_fishka = new_card.start_fishka
        new_card.curr_move = new_card.move
        new_card.alive = True

    def create_selection_popup(self, text, button_texts, button_binds):
        popup_ = OmegaPopup(width=310, height=110, background_color=(1, 0, 0, 1),
                                       overlay_color=(0, 0, 0, 0), size_hint=(None, None),
                                       auto_dismiss=False)
        rl = RelativeLayout(size=popup_.size, size_hint=(None, None))
        popup_.content = rl
        with rl.canvas:
            l = Label(pos=(70, 20), size_hint=(None, None), text=text, valign='top')
            self.garbage.append(l)

        for i, b_text in enumerate(button_texts):
            btn1 = Button(pos=(0+i*rl.width/len(button_texts), 0), size=(130, 30), background_color=(1, 0, 0, 1),
                          size_hint=(None, None),
                          text=b_text)
            btn1.bind(on_press=button_binds[i])
            rl.add_widget(btn1)
        popup_.open()
        return popup_

    def perform_card_action_0(self, args):
        # STAGE 0  - PODGOTOVKA
        out = []
        all_cards = self.backend.board.get_all_cards()
        if len(args) == 4 and not isinstance(args[0], tuple):
            args = tuple([args])
        for ability, card, victim, stage in args:
            if not card in all_cards:
                return
            if isinstance(ability, DefaultMovementAction):
                if not card.tapped:
                    self.move_card(card, victim[0], victim[1])  # victim here is a move
                else:
                    pass
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
            if isinstance(ability, TriggerBasedCardAction):
                if ability.recieve_inc:
                    ability.callback(victim)
                elif ability.recieve_all:
                    ability.callback(ability, card, victim)
                else:
                    ability.callback()
                return
            if isinstance(ability, SelectCardAction):
                self.disabled_actions = True
                self.exit_stack = True
                # self.eot_button_disabled = True
                # self.eot_button.disabled = True
                self.display_available_targets(self.backend.board, card, ability, 1, None)
                return
            if ability.a_type == ActionTypes.VOZROJDENIE:
                new_card, place = victim
                if new_card.player == 1:
                    self.grave_1_gl.remove_widget(self.cards_dict[new_card])
                    self.grave_buttons_1.remove(self.cards_dict[new_card])
                    self.backend.board.grave1.remove(new_card)
                elif new_card.player == 2:
                    self.grave_2_gl.remove_widget(self.cards_dict[new_card])
                    self.grave_buttons_2.remove(self.cards_dict[new_card])
                    self.backend.board.grave2.remove(new_card)
                self.cleanup_card(new_card)
                new_card.loc = place
                new_card.player = card.player
                self.backend.board.populate_board([new_card])
                self.reveal_cards([new_card])
                if ability.is_tapped:
                    new_card.tapped = False
                    self.tap_card(new_card)
                else:
                    new_card.tapped = True
                    self.tap_card(new_card)
                if isinstance(ability, FishkaCardAction):
                    self.remove_fishka(card, ability.cost_fishka)
                uq = self.check_for_uniqueness(new_card.player)
                if uq:
                    a = SimpleCardAction(a_type=ActionTypes.DESTRUCTION, damage=1, range_min=1, range_max=6,
                                         txt='Выберите какое уникальное существо оставить',
                                         ranged=False, state_of_action=[GameStates.MAIN_PHASE], target=uq, reverse=True)
                    self.display_available_targets(self.backend.board, new_card, a, None, None)
                return
            if isinstance(ability, SelectTargetAction):
                return
            if ability.a_type == ActionTypes.DESTRUCTION:
                try:
                    iterator = iter(victim)
                except TypeError:
                    self.destroy_card(victim, is_ubiranie_v_colodu=True)
                else:
                    for t in victim:
                        self.destroy_card(t, is_ubiranie_v_colodu=True)
                self.destroy_target_rectangles()
                self.destroy_target_marks()
                return
            if isinstance(ability, PopupAction):
                if not hasattr(self, 'attack_popup'):
                    self.attack_popup = self.create_selection_popup('Сделайте выбор: ',
                                                                    button_texts=ability.options,
                                                                    button_binds=ability.action_list)
                self.press_1 = ability.action_list[0]
                dur = self.timer.duration-1
                self.timer_ability = Animation(duration=dur)
                self.timer_ability.bind(on_complete=self.press_1)
                self.timer_ability.start(self)
                return
            if ability.a_type == ActionTypes.PERERASPREDELENIE_RAN:  # Implicitly make it as 1 damage
                self.remove_pereraspredelenie_ran()
                if isinstance(victim, list):
                    for vi in victim:
                        if card in all_cards and vi in all_cards:
                            rana = SimpleCardAction(a_type=ActionTypes.VOZDEISTVIE, damage=1, range_min=0, range_max=6, txt='1 рана',
                                  ranged=False,  isinstant=False, state_of_action=[GameStates.MAIN_PHASE], target='all')
                            out.append((rana, card, vi, 1))
                self.reset_passage()
                self.backend.stack.append(out)
                self.destroy_flickering(card)
                self.process_stack()
                return
            if card in all_cards and victim in all_cards:
                if ability.a_type == ActionTypes.TAP:
                    if not victim.tapped:
                        self.tap_card(victim)
                    return
                if (ability.a_type in ATTACK_LIST) and\
                    CardEffect.NETTED in victim.active_status:
                    victim.active_status.remove(CardEffect.NETTED)
                    victim.actions_left = victim.actions
                    victim.curr_move = victim.move
                    card.actions_left -= 1
                    if card.actions_left <= 0:
                        if not card.tapped:
                            self.tap_card(card)
                    self.move_label_dict[victim].text = f'{victim.curr_move}/{victim.move}'
                    self.add_defence_signs(victim)
                    self.destroy_target_rectangles()
                    self.destroy_target_marks()
                    return


            out.append((ability, card, victim, 1))
        self.reset_passage()
        self.backend.stack.append(out)
        self.process_stack()

    def perform_card_action_1(self, args):
        # STAGE 1 - KUBIKI
        # Шаг броска кубика (накладываем модификаторы к броску кубика, срабатывают особенности карт "при броске кубика")
        out = []
        to_add_extra = []
        bonus1 = 0
        bonus2 = 0
        if len(args) == 4 and not isinstance(args[0], tuple):
            args = tuple([args])
        for ability, card, victim, stage in args:
            if isinstance(ability, LambdaCardAction):
                ability.func()
                continue
            ability.rolls = []
            if isinstance(victim, list):
                pass
            else:
                self.draw_red_arrow(self.cards_dict[card], self.cards_dict[victim], card, victim)
            Clock.schedule_once(lambda x: self.destroy_red_arrows(), 3)
            num_die_rolls_attack = 1
            num_die_rolls_def = 0
            if ability.a_type == ActionTypes.ATAKA or ability.a_type == ActionTypes.UDAR_LETAUSHEGO:
                if not victim.tapped and not card.player == victim.player:
                    num_die_rolls_def = 1
                    if victim.rolls_twice:
                        num_die_rolls_def += 1
                if card.rolls_twice:
                    num_die_rolls_attack += 1
            for _ in range(num_die_rolls_attack+num_die_rolls_def):
                ability.rolls.append(self.backend.get_roll_result())
            if ability.a_type == ActionTypes.ATAKA or ability.a_type == ActionTypes.UDAR_LETAUSHEGO:
                bonus1 = card.exp_in_off
                if ability.callback and ability.condition == Condition.ATTACKING:
                    ability.callback(victim)
                if not victim.tapped and not card.player == victim.player:
                    bonus2 = victim.exp_in_def
                    roll_attack = max(ability.rolls[:num_die_rolls_attack]) + bonus1
                    roll_def = max(ability.rolls[num_die_rolls_attack:]) + bonus2
                    outcome_list = self.backend.get_fight_result(roll_attack, roll_def)
                    if card.player == 1:
                        self.draw_die(bonus1, bonus2,
                                      ability.rolls[:num_die_rolls_attack], ability.rolls[num_die_rolls_attack:])
                    else:
                        self.draw_die(bonus2, bonus1,
                                      ability.rolls[num_die_rolls_attack:], ability.rolls[:num_die_rolls_attack])
                    print('rolls: ', ability.rolls, bonus1, bonus2)
                    if len(outcome_list) == 1:
                        a, b = outcome_list[0]
                        if a:
                            ability.damage_make = ability.damage[a - 1]
                        else:
                            ability.damage_make = 0
                        if b:
                            ability.damage_receive = victim.attack[b - 1]
                        else:
                            ability.damage_receive = 0
                    else:
                        dmg_dict = {0: 'Промах', 1: 'Слабый', 2: 'Средний', 3: 'Cильный'}
                        self.attack_popup = self.create_selection_popup('Выберите результат сражения: ',
                                            [dmg_dict[outcome_list[0][0]] + '-' + dmg_dict[outcome_list[0][1]],
                                            dmg_dict[outcome_list[1][0]] + '-' + dmg_dict[outcome_list[1][1]]],
                                        button_binds=[partial(self.popup_attack_bind, outcome_list[0], ability, card, victim),
                                                      partial(self.popup_attack_bind, outcome_list[1], ability, card, victim)])

                        self.press_1 = lambda *_: self.popup_attack_bind(outcome_list[1], ability, card, victim)
                        dur = self.timer.duration - 1
                        self.timer_ability = Animation(duration=dur)
                        self.timer_ability.bind(on_complete=self.press_1)
                        self.timer_ability.start(self)
                        return
                else:
                    roll1 = max(ability.rolls[:num_die_rolls_attack]) + bonus1
                    if roll1 <= 3:
                        d = ability.damage[0]
                    elif 4 <= roll1 <= 5:
                        d = ability.damage[1]
                    elif roll1 > 5:
                        d = ability.damage[2]
                    ability.damage_make = d
                    if card.player == 1:
                        self.draw_die(bonus1, bonus2,ability.rolls, [])
                    else:
                        self.draw_die(bonus2, bonus1, [], ability.rolls)
                    print('rolls: ', ability.rolls, bonus1, bonus2)
            else:
                draw = False  # To only show die when it meatters
                roll1 = ability.rolls[0]
                if isinstance(ability.damage, int):
                    d = ability.damage
                elif callable(ability.damage):
                    d = ability.damage()
                elif len(ability.damage) == 3:
                    draw = True
                    if roll1 <= 3:
                        d = ability.damage[0]
                    elif 4 <= roll1 <= 5:
                        d = ability.damage[1]
                    elif roll1 > 5:
                        d = ability.damage[2]
                ability.damage_make = d
                if ability.a_type in [ActionTypes.VYSTREL, ActionTypes.METANIE, ActionTypes.RAZRYAD]:  # bez UCHR
                    cb = self.backend.board.get_all_cards_with_callback(Condition.ON_RECIEVING_RANGED_ATTACK)
                    for c, a in cb:
                        if c == victim:
                            to_add_extra.append((a, victim, ability, 0))
                if self.backend.current_active_player == 1 and draw:
                    self.draw_die(bonus1, bonus2, ability.rolls, [])
                elif self.backend.current_active_player == 2 and draw:
                    self.draw_die(bonus1, bonus2, [], ability.rolls)
                print('rolls: ', ability.rolls, bonus1, bonus2)
            out.append((ability, card, victim, 2))

        self.reset_passage()
        self.backend.stack.append(out)
        for el in to_add_extra:
            self.backend.stack.append(el)
        self.process_stack()

    def perform_card_action_2(self, args):
        #  STAGE 2 - NALOJENIE I OPLATA
        if len(args) == 4 and not isinstance(args[0], tuple):
            args = tuple([args])
        for ability, card, victim, stage in args:
            all_cards = self.backend.board.get_all_cards()
            if isinstance(ability, BlockAction):
                to_block = ability.to_block
                self.disabled_actions = False
                for el in reversed(self.backend.stack):
                    for a, c, v, s in el:
                        if a == to_block:
                            self.backend.stack.remove(el)
                            self.tap_card(c)
                            if isinstance(a, FishkaCardAction):
                                self.remove_fishka(c, a.cost_fishka)
            elif isinstance(ability, LambdaCardAction):
                ability.func()
                continue
            elif ability.a_type not in victim.defences and card in all_cards and victim in all_cards:
                cb_abs = self.backend.board.cards_callback(victim, Condition.ON_TAKING_DAMAGE)
                for cb_ab in cb_abs:
                    cb_ab.callback(card, ability)
                if ability.a_type == ActionTypes.ATAKA or ability.a_type == ActionTypes.UDAR_LETAUSHEGO:
                    if card.can_hit_flyer and victim.type_ == CreatureType.FLYER:
                        card.can_hit_flyer = False
                    if ability.damage_make:
                        victim.curr_life -= ability.damage_make
                        self.display_damage(victim, -1 * ability.damage_make)
                        self.play_attack_sound(ability.damage_make)
                    if ability.damage_receive:
                        card.curr_life -= ability.damage_receive
                        self.display_damage(card, -1 * ability.damage_receive)
                else:
                    if ability.a_type == ActionTypes.LECHENIE:
                        victim.curr_life = min(victim.curr_life + ability.damage_make, victim.life)
                        self.display_damage(victim, ability.damage_make)
                    elif ability.a_type == ActionTypes.EXTRA_LIFE:
                        victim.life += ability.damage_make
                        victim.curr_life += ability.damage_make
                        self.display_damage(victim, ability.damage_make)
                    elif ability.a_type in [ActionTypes.VYSTREL, ActionTypes.METANIE, ActionTypes.RAZRYAD]: # bez UCHR
                        victim.curr_life -= ability.damage_make
                        self.display_damage(victim, -1 * ability.damage_make)
                    elif ability.a_type == ActionTypes.NET:
                        victim.active_status.append(CardEffect.NETTED)
                        self.add_defence_signs(victim)
                    elif ability.a_type == ActionTypes.DOBIVANIE and victim.curr_life <= ability.damage and \
                            CardEffect.BESTELESNOE not in victim.active_status:
                        victim.curr_life = 0
                    else:
                        victim.curr_life -= ability.damage_make
                        self.display_damage(victim, -1 * ability.damage_make)

            if card and victim:
                self.destroy_target_rectangles()
                self.destroy_target_marks()

                if card.curr_life <= 0 and card in all_cards:
                    self.destroy_card(card)
                if victim.curr_life <= 0 and victim in all_cards:
                    if CardEffect.TRUPOEDSTVO in card.active_status and not CardEffect.BESTELESNOE in victim.active_status:
                        if card.type_ == CreatureType.FLYER or victim.loc in self.backend.board.get_adjacent_cells(card.loc):
                            card.curr_life = card.life
                            if CardEffect.OTRAVLEN in card.active_status:
                                card.otravlenie = 0
                                card.active_status.remove(CardEffect.OTRAVLEN)
                    self.destroy_card(victim)

                self.hp_label_dict[victim].text = f'{victim.curr_life}/{victim.life}'
                self.hp_label_dict[card].text = f'{card.curr_life}/{card.life}'

                card.actions_left -= 1
                if card.actions_left <= 0:
                    if not card.tapped:
                        self.tap_card(card)
                if ability.tap_target:
                    self.tap_card(victim)

            if isinstance(ability, FishkaCardAction):
                self.remove_fishka(card, ability.cost_fishka)
            self.handle_PRI_ATAKE(ability, card, victim)
            ability.rolls = []  # cleanup
            ability.damage_make = 0
            ability.damage_receive = 0
            self.disabled_actions = False

    def perform_card_action(self, *args):
        try:
            self.attack_popup.dismiss()
            del self.attack_popup
        except:
            pass
        inst = self.backend.board.get_instants()
        if inst and self.backend.in_stack and not (self.backend.passed_1 and self.backend.passed_2):
            return
        if len(args) == 4 and not isinstance(args[0], tuple):
            ability, card, victim, stage = args
            self.unhide(card)
            self.unhide(victim)
        elif isinstance(args, tuple):
            ability, card, victim, stage = args[0]
            for a, c, v, s in args:
                self.unhide(c)
                self.unhide(v)
        if stage == 0:
            self.perform_card_action_0(args)
        elif stage == 1:
            ability, card, victim, stage = args[0]  # !
            if ability.a_type == ActionTypes.ATAKA or ability.a_type == ActionTypes.UDAR_LETAUSHEGO:
                cb = self.backend.board.get_all_cards_with_callback(Condition.ON_DEFENCE_BEFORE_DICE)
                for c, a in cb:
                    if c == victim and a.check(ability):
                        a.disabled = False
                        a.repeat = True
                        a.target = ability
                        a.actor = card
                        a.prep()
                        a.isinstant = True
                        self.backend.in_stack = True
                        self.eot_button.disabled = True
                        self.ph_button.disabled = False
                        self.backend.curr_priority = victim.player
                        self.backend.passed_1 = False
                        self.backend.passed_2 = False
                        Clock.schedule_once(lambda x: self.start_timer(STACK_DURATION))
                        return
                    # self.disable_all_buttons_except_instant(defenders)
            self.perform_card_action_1(args)
        elif stage == 2:
            cb = self.backend.board.get_all_cards_with_callback(Condition.ON_MAKING_DAMAGE_STAGE)
            for c, a in cb:
                if (isinstance(args[0], tuple) or isinstance(args[0], list)):
                    for ability, card, victim, stage in args:
                        if a.check(card, victim, ability):
                            a.disabled = False
                            a.repeat = True
                            a.actor = card
                            a.isinstant = True
                            a.victim = victim
                            a.inc_ability = ability
                            a.prep()
                            if hasattr(a, 'clear_cb'):
                                temp = [(LambdaCardAction(func=a.clear_cb), self, None, 2), (ability, card, victim, 2)]
                            else:
                                temp = (ability, card, victim, 2)
                            self.proxi_ability = temp
                            self.backend.stack.append(temp)
                            self.backend.in_stack = True
                            self.eot_button.disabled = True
                            self.ph_button.disabled = False
                            self.backend.curr_priority = victim.player
                            self.reset_passage()
                            Clock.schedule_once(lambda x: self.start_timer(STACK_DURATION))
                            return
            self.perform_card_action_2(args)

    def on_new_turn(self):
        self.garbage = []
        self.garbage_dict = {}
        self.disabled_actions = False
        self.damage_marks = []
        self.able_selected(enable=False)
        self.destroy_target_marks()
        self.destroy_target_rectangles()
        self.destroy_flickering()
        for c, rl in self.cards_dict.items():
            if c.player == self.backend.current_active_player:
                if c.tapped:
                    self.tap_card(c)
                if CardEffect.NETTED in c.active_status:
                    c.actions_left = 0
                    c.curr_move = 0
                else:
                    c.actions_left = c.actions
                    c.curr_move = c.move
                self.move_label_dict[c].text = f'{c.curr_move}/{c.move}'
        if self.selected_card:
            if self.selected_card.player == self.backend.current_active_player:
                self.display_card_actions(self.selected_card, False, None)

    def on_click_on_card(self, card, instance):
        # print('Опыт в защите: ', card.defences)
        # print(card.actions_left)
        if self.disabled_actions:
            return
        self.destroy_target_marks()
        if card.player != self.backend.curr_priority and not self.backend.board.isinstant_card(card):
            return
        if card.actions_left <= 0:
            return
        if self.selected_card:
            Clock.schedule_once(partial(self.draw_card_overlay, self.selected_card, 0))
        self.selected_card = card
        self.destroy_x(self.selected_card_buttons, long=True)
        self.selected_card_buttons = []
        # Draw border
        self.draw_selection_border(instance.parent, card)
        # Higlight name
        self.bright_card_overlay(card)
        # Display card action buttons
        if self.backend.in_stack:
            self.display_card_actions(card, False, instance)
        else:
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
            ch.background_down = card.pic[:-4] + '_rot90.jpg'
            ch.pos = (CARD_X_SIZE*0.16, 0)
            ch.size = (CARD_X_SIZE*0.84, CARD_Y_SIZE)
            self.draw_card_overlay(card, 1)
            card.tapped = True
            self.able_selected(enable=False)
            # if card.player == self.backend.current_active_player:
            #     end_turn = True
            #     all_cards = self.backend.board.get_all_cards()
                # for c in all_cards:
                #     if not c.tapped and c.player == self.backend.current_active_player:
                #         end_turn = False
                # if end_turn:
                #     print('there')
                #     self.backend.next_game_state()
        else:
            ch.background_normal = card.pic
            ch.background_down = card.pic
            self.draw_card_overlay(card, 2)
            ch.pos = (0, CARD_Y_SIZE * 0.16)
            ch.size = (CARD_X_SIZE, CARD_Y_SIZE*0.84)
            card.tapped = False
            card.actions_left = card.actions
            card.curr_move = card.move
            self.able_selected(enable=True)

    def bind_multiple_actions(self, card, multiple_ability, ix, target, *args):
        if len(self.multiple_targets_list) > 0 and ix == 0:
            self.multiple_targets_list = []
        if multiple_ability.action_list[-1].a_type == ActionTypes.PERERASPREDELENIE_RAN:
            self.add_pereraspredelenie_marker(target)
        self.disabled_actions = True
        self.destroy_target_rectangles()
        self.destroy_target_marks()
        self.multiple_targets_list.append(target)
        if len(multiple_ability.action_list)-1 == ix and (len(self.multiple_targets_list) == len(multiple_ability.action_list)):
            self.start_stack_action(multiple_ability, card, None, None)
        else:
            bind_ = partial(self.bind_multiple_actions, card, multiple_ability, ix+1)
            self.display_available_targets(self.backend.board, card, multiple_ability.action_list[ix+1], bind_, None)

    def handle_multiple_actions(self, ability, card, instance):
        if ability.isinstant:
            self.able_selected(enable=False)
            #self.display_card_actions(card, False, None)
        self.display_available_targets(self.backend.board, card, ability.action_list[0],
                                           partial(self.bind_multiple_actions, card, ability, 0),  None)

    def handle_selection_action(self, ability, card, t, *args):  # cobold?
        self.timer_ability.unbind(on_complete=self.press_2)
        self.ph_button.unbind(on_press=self.press_2)
        self.ph_button.disabled = True
        self.eot_button.disabled = True
        self.destroy_target_rectangles()
        self.destroy_target_marks()
        self.exit_stack = False
        self.disabled_actions = False
        self.start_stack_action(ability.child_action, card, t, force=1)
        Clock.schedule_once(self.process_stack)

    def display_available_targets_helper(self, board, card, ability, bind_, *args):
        b_size = 30  # размер квадратика
        if ability.targets == 'all':
            targets = board.get_all_cards()
        elif ability.targets == 'ally':
            all_cards = board.get_all_cards()
            targets = [x for x in all_cards if x.player == card.player]
        elif ability.targets == 'enemy':
            all_cards = board.get_all_cards()
            targets = [x for x in all_cards if x.player != card.player]
        elif ability.targets == 'self':
            targets = [card]
        elif ability.a_type == ActionTypes.UDAR_CHEREZ_RYAD:
            targets = self.backend.board.get_available_targets_uchr(card)
        elif callable(ability.targets):
            targets = ability.targets()
        elif isinstance(ability.targets, list):
            targets = ability.targets
        elif card.type_ == CreatureType.CREATURE and not card.can_hit_flyer:
            targets = board.get_ground_targets_min_max(card_pos_no=board.game_board.index(card),
                                                       range_max=ability.range_max, range_min=ability.range_min,
                                                       ability=ability)
            if hasattr(ability, 'target_restriction') and 'not_flyer' in ability.target_restriction:
                targets = [x for x in targets if x.type_ != CreatureType.FLYER]
            if hasattr(ability, 'target_restriction') and 'enemy' in ability.target_restriction:
                targets = [x for x in targets if x.player != card.player]
        elif card.can_hit_flyer:  # NO TARGETS ON GROUND ONLY FLYING  CREATURES
            targets = board.get_available_targets_flyer(card)
        elif card.type_ == CreatureType.FLYER:
            magnets = self.backend.board.get_flyer_magnets(card.player, enemy=True)
            if magnets:
                targets = magnets
            else:
                targets = board.get_available_targets_flyer(card)
        if bind_ == 1:
            if targets:
                dur = self.timer.duration-1
                self.timer_ability = Animation(duration=dur)
                self.press_2 = lambda *_: self.handle_selection_action(ability, card, targets[0])
                self.timer_ability.bind(on_complete=self.press_2)
                self.ph_button.bind(on_press=self.press_2)
                # self.ph_button.disabled = True
                self.eot_button.disabled = True
                self.timer_ability.start(self)  # TODO доделать что бы как по закрытому
            else:
                self.disabled_actions = False
                self.exit_stack = False
        for t in targets:
            if isinstance(t, int):
                pos = self.card_position_coords[t]
                c = Color(1, 1, 1, 0.8)
                rl = RelativeLayout(pos=pos)
                with rl.canvas:
                    btn = Button(pos=(0,0),
                                 background_color=(1, 1, 1, 0.0),
                                 size=(CARD_X_SIZE, CARD_Y_SIZE), size_hint=(None, None))
                    rect1 = Rectangle(pos=(CARD_X_SIZE / 2 - b_size / 2,
                                           CARD_Y_SIZE / 2 - b_size / 2),
                                      background_color=c,
                                      size=(b_size, b_size), size_hint=(1, 1))
                    c = Color(1, 1, 1, 0.15)
                    rect2 = Rectangle(size=(CARD_X_SIZE, CARD_Y_SIZE),
                                      background_color=c,
                                      pos=(0, 0), size_hint=(1, 1))
                    self.target_rectangles.append((rect1, rl.canvas))
                    self.target_rectangles.append((rect2, rl.canvas))
                    rl.add_widget(btn)
                    self.target_marks_cards.append([btn, rl])
                self.root.add_widget(rl)
            else:
                with self.cards_dict[t].canvas:
                    btn = Button(pos=(0, 0),
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
                    rect2 = Rectangle(size=(CARD_X_SIZE, CARD_Y_SIZE),
                                      background_color=c,
                                      pos=(0, 0), size_hint=(1, 1))
                self.target_rectangles.append((rect1, self.cards_dict[t].canvas))
                self.target_rectangles.append((rect2, self.cards_dict[t].canvas))
                self.cards_dict[t].add_widget(btn)
                self.target_marks_cards.append([btn, self.cards_dict[t]])
            if bind_ == 1:
                btn.bind(on_press=partial(self.handle_selection_action, ability, card, t))
            elif callable(bind_):
                btn.bind(on_press=partial(bind_, t))
            else:
                t0 = t
                if hasattr(ability, 'reverse'):
                    if ability.reverse:
                        t0 = targets.copy()
                        t0.remove(t)
                btn.bind(on_press=partial(self.start_stack_action, ability, card, t0))
            self.target_marks_buttons.append(t)

    def display_available_targets(self, board, card, ability, bind_, instance):
        self.destroy_target_marks()
        self.display_available_targets_helper(board, card, ability, bind_)

    def add_fishka(self, card, *args):
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

        displayable = self.check_displayable_card_actions(card)
        for i, ab in enumerate(displayable):  #TODO Убрать show_slow
            ability, code = ab
            if self.backend.curr_priority == card.player:
                disabled_ = operator.not_(bool(card.actions_left))
            else:
                disabled_ = True
            if disabled_ or (not show_slow and not ability.isinstant) or (code == 0)\
                    or (self.backend.in_stack and not ability.isinstant):
                disabled_ = True
            else:
                disabled_ = False
            btn = Button(text=ability.txt,
                          pos=(Window.width * 0.84, Window.height * 0.24 - i * 0.04 * Window.height),
                          disabled=disabled_, background_color=(1,0,0,1), border=[1,1,1,1],
                          size=(Window.width * 0.14, Window.height * 0.04),)# size_hint=(None, None))
            if isinstance(ability, SimpleCardAction) or isinstance(ability, FishkaCardAction):
                btn.bind(on_press=partial(self.display_available_targets, self.backend.board, card, ability, None))
            elif isinstance(ability, DefenceAction) or isinstance(ability, IncreaseFishkaAction)\
                    or isinstance(ability, TapToHitFlyerAction):
                btn.bind(on_press=partial(self.start_stack_action, ability, card, ability))
            elif isinstance(ability, MultipleCardAction):
                btn.bind(on_press=partial(self.handle_multiple_actions, ability, card))
            elif isinstance(ability, TriggerBasedCardAction):  # and not ability.disabled:
                if hasattr(ability, 'clear_cb'):
                    btn.bind(on_press=ability.clear_cb)
                btn.bind(on_press=self.lambda_disabled_actions)
                btn.bind(on_press=partial(self.start_stack_action, ability, card, ability.target))
            self.root.add_widget(btn)
            ability.button = btn
            self.selected_card_buttons.append((btn, ability))

    def able_selected(self, enable=True):
        if enable:
            for b, a in self.selected_card_buttons:
                if hasattr(a, 'stay_disabled') and not a.stay_disabled:
                    b.disabled = False
        else:
            for b, a in self.selected_card_buttons:
                b.disabled = True

    def draw_card_overlay(self, *args):
        card = args[0]
        turned = args[1]  # 0 - initial, 1 - tapped, 2 - untapped
        name = (card.name[:11] + '..') if len(card.name) > 11 else card.name
        if turned == 3:
            size_ = (CARD_X_SIZE-2, CARD_Y_SIZE * 0.16)
            lyy = self.base_overlays[card]
            ly = RelativeLayout()
            with ly.canvas:
                if card.player == 1:
                    c = Color(1, 1, 0.6, 1)
                    c1 = (0, 0, 0, 1)
                else:
                    c = Color(0.4, 0.5, 1, 1)
                    c1 = (1, 1, 1, 1)
                rect = Rectangle(pos=(1, 0), background_color=c,
                                 size=size_,
                                 font_size=Window.height * 0.02)
                lbl_ = Label(pos=(0, 0), text=f'{name}', color=c1,
                             size=size_,
                             font_size=Window.height * 0.02, )
                self.card_nameplates.append(lbl_)
                lyy.add_widget(ly)
                self.card_nameplates_dict[card] = ly
        if turned == 1:
            size_ = (CARD_Y_SIZE * 0.16, CARD_X_SIZE)
            lx = self.base_overlays[card]
            with lx.canvas.before:
                PushMatrix()
                self.rotation = Rotate()
                self.rotation.origin = (lx.x+CARD_X_SIZE/2, lx.y+CARD_Y_SIZE/2)
                self.rotation.angle = -90
            with lx.canvas.after:
                PopMatrix()
        else:
            size_ = (CARD_X_SIZE-2, CARD_Y_SIZE * 0.16)
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
                    rect = Rectangle(pos=(1, 0), background_color=c,
                                 size=size_,
                                 font_size=Window.height * 0.02)
                    # name = (card.name[:12] + '..') if len(card.name) > 12 else card.name
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
            rect = Rectangle(pos=(2, 0), background_color=c,
                             size=(CARD_X_SIZE-2, CARD_Y_SIZE * 0.16),
                             font_size=Window.height * 0.02)
            name = (card.name[:12] + '..') if len(card.name) > 14 else card.name
            lbl_ = Label(pos=(0, 0), text=f'{name}', color=c1,
                         size=(CARD_X_SIZE, CARD_Y_SIZE * 0.16),
                         font_size=Window.height * 0.02, )
            self.card_nameplates.append(lbl_)
            self.card_nameplates_dict[card] = ly
        lyy.add_widget(ly)

    def reveal_cards(self, cards):
        for card in cards:
            loc = card.loc
            # if card.hidden:
            #     pic = 'data/cards/cardback.jpg'
            #     x, y = self.card_position_coords[loc]
            #     rl1 = RelativeLayout(pos=(x, y))
            #     btn1 = Button(disabled=False, pos=(0, 0), background_down=pic,
            #                   background_normal=pic, size=(CARD_X_SIZE, CARD_Y_SIZE), border=(0, 0, 0, 0),
            #                   size_hint=(None, None))
            #     rl1.add_widget(btn1)
            #     self.layout.add_widget(rl1)
            #     self.cards_dict[card] = rl1
            #     self.base_overlays[card] = RelativeLayout()
            #     btn1.bind(on_press=partial(self.on_click_on_card, card))
            #     continue
            # else:
            pic = card.pic
            if card.type_ == CreatureType.FLYER:
                rl1 = RelativeLayout(size=(CARD_X_SIZE, CARD_Y_SIZE))
                btn1 = Button(disabled=False,
                              background_normal=pic, background_down=pic,
                              pos=(0, CARD_Y_SIZE*0.16), border=(0,0,0,0),
                              size=(CARD_X_SIZE, CARD_Y_SIZE*0.84), size_hint=(None, None))
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
                btn1 = Button(disabled=False,  pos=(0, CARD_Y_SIZE*0.16), background_down=pic,
                          background_normal=pic, size=(CARD_X_SIZE, CARD_Y_SIZE*0.84),  border=(0,0,0,0),
                          size_hint=(None, None))

            btn1.bind(on_press=partial(self.on_click_on_card, card))
            rl1.add_widget(btn1)

            base_overlay_layout = RelativeLayout()
            with base_overlay_layout.canvas:
                # Life
                Color(0, 0.3, 0.1)
                Rectangle(size=(CARD_X_SIZE*0.33, CARD_Y_SIZE*0.15), color=(1,1,1,0.3),
                          pos=(1, CARD_Y_SIZE*0.85)) #pos_hint={'x':0, 'y':0.8}
                Color(1, 1, 1)
                Line(width=0.5, color=(1,1,1,0), rectangle=(1, CARD_Y_SIZE*0.85, CARD_X_SIZE*0.33, CARD_Y_SIZE*0.15))
                lbl = Label(pos=(3, CARD_Y_SIZE*0.85), text=f'{card.life}/{card.life}', color=(1, 1, 1, 1), size=(CARD_X_SIZE * 0.3, CARD_Y_SIZE * 0.15),
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


            self.base_overlays[card] = base_overlay_layout
            Clock.schedule_once(partial(self.draw_card_overlay, card, 0))#, 0.1)
            rl1.add_widget(base_overlay_layout)
            self.cards_dict[card] = rl1
            if card.curr_fishka > 0:
                self.add_fishki_gui(card)
            if card.type_ == CreatureType.CREATURE:
                self.layout.add_widget(rl1)
            self.update_zone_counters()
            self.add_defence_signs(card)
        # Строй
        for card in cards:
            stroy_neighbors = self.backend.board.get_adjacent_with_stroy(card.loc)
            if len(stroy_neighbors) != 0 and not card.in_stroy and card.stroy_in:
                card.stroy_in()

    def add_defence_signs(self, card):
        base_overlay = self.base_overlays[card]
        try:
            base_overlay.remove_widget(self.card_signs_imgs[card])
        except:
            pass
        self.card_signs[card] = []
        if ActionTypes.RAZRYAD in card.defences and ActionTypes.ZAKLINANIE in card.defences and ActionTypes.MAG_UDAR in card.defences:
            self.card_signs[card].append('data/icons/zom.png')
        if ActionTypes.VYSTREL in card.defences:
            self.card_signs[card].append('data/icons/zov.png')
        if ActionTypes.OTRAVLENIE in card.defences:
            self.card_signs[card].append('data/icons/zoya.png')
        if CardEffect.NAPRAVLENNY_UDAR in card.active_status:
            self.card_signs[card].append('data/icons/naprav.png')
        if CardEffect.UDAR_CHEREZ_RYAD in card.active_status:
            self.card_signs[card].append('data/icons/uchr.png')
        if CardEffect.REGEN in card.active_status:
            self.card_signs[card].append('data/icons/regen.png')
        if CardEffect.NETTED in card.active_status:
            self.card_signs[card].append('data/icons/spider-web.png')
        rl = RelativeLayout()
        with rl.canvas:
            for i, p in enumerate(self.card_signs[card]):
                im = Image(source=p, pos=(CARD_X_SIZE * 0.01 + i*CARD_X_SIZE * 0.18, CARD_Y_SIZE * 0.16),
                                          size=(CARD_X_SIZE * 0.18, CARD_X_SIZE * 0.18), opacity=0.88)
        self.card_signs_imgs[card] = rl
        base_overlay.add_widget(rl)

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
            for scroll, butt1, border1, p1, gl in self.extra_scrolls_1:
                if scroll != sv:
                    scroll.disabled = True
                    scroll.opacity = 0
                    scroll.size = (0, 0)
                    gl.size = (0, 0)
                    border1.rectangle = (0, 0, 0, 0)
                    if butt == self.deck1_btn and butt1==self.grave1_btn:
                        x, y = p1
                        butt1.pos = (x, y-0.021*Window.width)
                    else:
                        butt1.pos = p1
        else:
            for scroll, butt1, border1, p1, gl in self.extra_scrolls_2:
                if scroll != sv:
                    scroll.disabled = True
                    scroll.opacity = 0
                    scroll.size = (0, 0)
                    gl.size = (0, 0)
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
        total_min = (duration-1)//60
        self.curr_timer_left = duration - completion_ratio*duration
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
    #
    # def restart_timer(self, *args):
    #     if hasattr(self, 'timer'):
    #         self.timer.cancel(self.timer_label)
    #         self.timer.start(self.timer_label)

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
            self.able_selected(enable=False)
        self.stack_cards = cards

    def disable_all_non_instant_actions(self):
        if self.selected_card:
            self.display_card_actions(self.selected_card, False, None)

    def buttons_on_priority_switch(self):
        if self.selected_card and not self.selected_card.tapped and self.selected_card.actions_left > 0:
            if self.selected_card.player != self.backend.curr_priority:
                self.able_selected(enable=False)
            else:
                self.display_card_actions(self.selected_card, True, None)

    def add_dopzones(self, position_scroll, position_butt, position_butt2, zone_name, button_name, gl_name, txt, player, button_func):
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
        f = partial(self.hide_scroll, scroll, butt, position_butt, position_butt2, border,
                                   player)
        butt.bind(on_press=f)

        if player == 1:
            self.extra_scrolls_1.append((scroll, butt, border, position_butt2, gl))
        else:
            self.extra_scrolls_2.append((scroll, butt, border, position_butt2, gl))

        setattr(self, button_func, f)
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
        self.layout = FloatLayout(size=(0, 0))
        self.card_position_coords = []
        self.nav_buttons = []
        self.selected_card_buttons = []
        self.selected_card = None
        self.defender_set = False
        self.eot_button_disabled = False
        self.pending_attack = None
        self.disabled_actions = False
        self.exit_stack = False
        self.proxi_ability = None
        self.target_marks_buttons = []
        self.hp_label_dict = {}
        self.move_label_dict = {}
        self.pereraspredelenie_label_dict = defaultdict(int)
        self.pereraspredelenie_dict = {}
        self.fishka_label_dict = {}
        self.cards_dict = {}
        self.fishka_dict = {}
        self.die_pics = []
        self.red_arrows = []
        self.card_nameplates = []
        self.target_rectangles = []
        self.target_marks_cards = []
        self.card_nameplates_dict = defaultdict(RelativeLayout)
        self.base_overlays = {}
        self.damage_marks = []
        self.count_of_flyers_1 = 0
        self.selection_flicker_dict = {}
        self.card_signs = defaultdict(list)
        self.card_signs_imgs = {}
        self.stack_cards = []
        self.multiple_targets_list = []
        self.grave_buttons_1 = []
        self.grave_buttons_2 = []
        self.garbage = []
        self.garbage_dict = {}

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
        Clock.schedule_once(lambda x: self.start_timer(TURN_DURATION))  # BUGGY?

        # Extra zones sliders
        self.dop_zone_1_buttons = []
        self.dop_zone_2_buttons = []
        self.extra_scrolls_1 = []
        self.extra_scrolls_2 = []
        Clock.schedule_once(lambda x: self.add_dopzones(position_scroll=(Window.width * 0.85, Window.height * 0.48),  # 1-ая доп. зона
                                                         position_butt=(Window.width * 0.84, Window.height * 0.93),
                                                        position_butt2=(Window.width * 0.84, Window.height * 0.93),
                                                        zone_name='dop_zone_1', player=1, button_func='dop_zone_1_func',
                                                        button_name='dz1_btn', gl_name='dop_zone_1_gl', txt='Доп. зона'))
        Clock.schedule_once(lambda x: self.add_dopzones(position_scroll=(Window.width * 0.03, Window.height * 0.48),  # 2-ая доп. зона
                                                        position_butt=(Window.width * 0.01, Window.height * 0.93),
                                                        position_butt2=(Window.width * 0.01, Window.height * 0.93),
                                                        zone_name='dop_zone_2', player=2, button_func='dop_zone_2_func',
                                                        button_name='dz2_btn', gl_name='dop_zone_2_gl', txt='Доп. зона'))
        Clock.schedule_once(lambda x: self.add_dopzones(position_scroll=(Window.width * 0.85, Window.height * 0.43),  #  1-ое кладбище
                                                        position_butt=(Window.width * 0.84, Window.height * 0.89),
                                                        position_butt2=(Window.width * 0.84, Window.height * 0.43),
                                                        zone_name='grave_1', player=1, button_func='grave_1_func',
                                                        button_name='grave1_btn', gl_name='grave_1_gl', txt='Кладбище'))
        Clock.schedule_once(lambda x: self.add_dopzones(position_scroll=(Window.width * 0.03, Window.height * 0.43),  #  2-ое кладбище
                                                        position_butt=(Window.width * 0.01, Window.height * 0.89),
                                                        position_butt2=(Window.width * 0.01, Window.height * 0.43),
                                                        zone_name='grave_2', player=2, button_func='grave_2_func',
                                                        button_name='grave2_btn', gl_name='grave_2_gl', txt='Кладбище'))
        Clock.schedule_once(lambda x: self.add_dopzones(position_scroll=(Window.width * 0.85, Window.height * 0.43),  # 1-ая колода
                                        position_butt=(Window.width * 0.84, Window.height * 0.89),
                                        position_butt2=(Window.width * 0.84, Window.height * 0.39),
                                        zone_name='deck_1', player=1,  button_func='deck_1_func',
                                        button_name='deck1_btn', gl_name='deck_1_gl', txt='Колода'))

        # timeout otherwise some parts are not rendered
        Clock.schedule_once(lambda x: self.reveal_cards(self.backend.input_cards1))
        Clock.schedule_once(lambda x: self.reveal_cards(self.backend.input_cards2))

        return root



