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
import network
from main_menu import MainMenuApp
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

class TouchInput(Widget):

  def on_touch_down(self, touch):
    global mouse
    mouse = touch.button


class BerserkApp(App):

    def __init__(self, window_size, stack_duration=10, turn_duration=10, pow=1, mode='offline', backend=None):
        super(BerserkApp, self).__init__()
        self.backend = backend
        self.mode = mode
        self.pow = pow
        self.window_size = window_size
        Window.size = window_size
        if window_size == (1920, 1080):
            Window.maximize()
        global CARD_X_SIZE, CARD_Y_SIZE, STACK_DURATION, TURN_DURATION, DZ_SIZE
        CARD_X_SIZE = (Window.width * 0.084375)
        CARD_Y_SIZE = CARD_X_SIZE  # (Window.height * 0.15)

        STACK_DURATION = stack_duration
        TURN_DURATION = turn_duration

        self.turn_duration = turn_duration
        self.stack_duration = stack_duration

        DZ_SIZE = (CARD_X_SIZE, Window.height * 0.45)
        self.title = 'Berserk Renewal'
        self.curr_state = None

    def load_complete(self):
        if self.mode == 'online':
            pass
        else:
            self.backend.on_load(1)

    def draw_card_overlay(self, *args):
        card = args[0]
        turned = args[1]  # 0 - initial, 1 - tapped, 2 - untapped
        name = (card['name'][:11] + '..') if len(card['name']) > 11 else card['name']
        if turned == 3:
            size_ = (CARD_X_SIZE-2, CARD_Y_SIZE * 0.16)
            lyy = self.base_overlays[card['id']]
            ly = RelativeLayout()
            with ly.canvas:
                if card['player'] == self.pow:
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
                self.card_nameplates_dict[card['id']] = ly
        if turned == 1:
            size_ = (CARD_Y_SIZE * 0.16, CARD_X_SIZE)
            lx = self.base_overlays[card['id']]
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
                lyy = self.base_overlays[card['id']]
                ly = RelativeLayout()
                self.cards_dict[card['id']].remove_widget(self.card_nameplates_dict[card['id']])
                if turned == 2:
                    with lyy.canvas.before:
                        PushMatrix()
                        self.rotation = Rotate()
                        self.rotation.origin = (ly.x + CARD_X_SIZE / 2, ly.y + CARD_Y_SIZE / 2)
                        self.rotation.angle = 90
                    with lyy.canvas.after:
                        PopMatrix()
                with ly.canvas:
                    if card['player'] == self.pow:
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
                                 font_size=Window.height * 0.02,)
                    self.card_nameplates.append(lbl_)
                    lyy.add_widget(ly)
                    self.card_nameplates_dict[card['id']] = ly

    def bright_card_overlay(self, card):
        lyy = self.base_overlays[card['id']]
        self.cards_dict[card['id']].remove_widget(self.card_nameplates_dict[card['id']])
        ly = RelativeLayout()
        with ly.canvas:
            if card['player'] == self.pow:
                c = Color(1, 1, 0, 1)
                c1 = (0, 0, 0, 1)
            else:
                c = Color(0.1, 0.1, 1, 1)
                c1 = (1, 1, 1, 1)
            rect = Rectangle(pos=(2, 0), background_color=c,
                             size=(CARD_X_SIZE-2, CARD_Y_SIZE * 0.16),
                             font_size=Window.height * 0.02)
            name = (card['name'][:12] + '..') if len(card['name']) > 14 else card['name']
            lbl_ = Label(pos=(0, 0), text=f'{name}', color=c1,
                         size=(CARD_X_SIZE, CARD_Y_SIZE * 0.16),
                         font_size=Window.height * 0.02, )
            self.card_nameplates.append(lbl_)
            self.card_nameplates_dict[card['id']] = ly
        lyy.add_widget(ly)

    def destroy_x(self, list_, long=False):
        if long==True:
            for bt, a in list_:
                self.root.remove_widget(bt)
        else:
            for bt in list_:
                self.root.remove_widget(bt)

    def delete_move_marks_on_unfocus(self, window, pos):
        delete_ = True
        for nav_b in self.nav_buttons:
            if abs(pos.x - CARD_X_SIZE / 2 - nav_b.x) < CARD_X_SIZE and abs(
                    pos.y - CARD_Y_SIZE / 2 - nav_b.y) < CARD_Y_SIZE:
                delete_ = False
        if delete_:
            self.destroy_x(self.nav_buttons)
            self.nav_buttons = []

    def card_popup_destr(self, window, pos):
        if hasattr(self, 'card_popup_obj'):
            self.card_popup_obj.dismiss()
            del self.card_popup_obj

    def get_pos(self, card_id):
        card = self.id_card_dict[card_id]
        if card['zone'] == 'board': #card.hidden:
            return self.cards_dict[card['id']].pos
        elif card['zone'] == 'gr':
            if (card['player'] == 1 and self.pow == 1) or (card['player'] == 2 and self.pow == 2):
                return self.grave_1_gl.to_window(*self.cards_dict[card_id].pos)
            else:
                return self.grave_2_gl.to_window(*self.cards_dict[card_id].pos)
        elif card['zone'] == 'dz':
            if (card['player'] == 1 and self.pow == 1) or (card['player'] == 2 and self.pow == 2):
                return self.dop_zone_1.to_parent(*self.cards_dict[card_id].pos)
            else:
                return self.dop_zone_2.to_parent(*self.cards_dict[card_id].pos)


    def card_popup(self, card, window):
        # print(card)
        try:
            if mouse == 'right':
                if not hasattr(self, 'card_popup_obj'):
                    self.card_popup_obj = Popup(title='Berserk renewal',
                                  content=Image(source=card['pic'][:-4]+'_full.jpg'),
                                  size_hint=(None, None), size=(281, 400))
                    self.card_popup_obj.open()
        except:
            pass

    def add_fishki_gui(self, card):
        if card['curr_fishka'] <= 0:
            return
        base_overlay = self.base_overlays[card['id']]
        rl = RelativeLayout()
        with rl.canvas:
            Color(0, 0, 0.8)
            Rectangle(size=(CARD_X_SIZE * 0.15, CARD_Y_SIZE * 0.15), color=(1, 1, 1, 0.3),
                      pos=(0, CARD_Y_SIZE * 0.70))  # pos_hint={'x':0, 'y':0.8}
            Color(1, 1, 1)
            Line(width=0.5, color=(1, 1, 1, 0),
                 rectangle=(0, CARD_Y_SIZE * 0.70, CARD_X_SIZE * 0.15, CARD_Y_SIZE * 0.15))
            lbl = Label(pos=(0, CARD_Y_SIZE * 0.70), text=f"{card['curr_fishka']}", color=(1, 1, 1, 1),
                        size=(CARD_X_SIZE * 0.15, CARD_Y_SIZE * 0.15),
                        font_size=Window.height * 0.02, valign='top')
            self.fishka_label_dict[card['id']] = lbl
        base_overlay.add_widget(rl)
        self.fishka_dict[card['id']] = rl

    def remove_fishki_gui(self, card):
        if card['id'] in self.fishka_label_dict:
            del self.fishka_label_dict[card['id']]
        try:
            base_overlay = self.base_overlays[card['id']]
            base_overlay.remove_widget(self.fishka_dict[card['id']])
        except:
            pass

    def draw_selection_border(self, instance, card):
        if hasattr(self, "card_border"):
            self.card_border[1].canvas.remove(self.card_border[0])
        with instance.canvas:
            if card['player'] == 1:
                c = Color(1, 1, 0, 1)
            else:
                c = Color(0.2, 0.2, 0.8, 1)
            self.card_border = (Line(width=1, color=c, rectangle=(0, 0, CARD_X_SIZE, CARD_Y_SIZE)), instance)

    def add_defence_signs(self, card):
        base_overlay = self.base_overlays[card['id']]
        try:
            base_overlay.remove_widget(self.card_signs_imgs[card['id']])
        except:
            pass
        self.card_signs[card['id']] = []
        if ActionTypes.RAZRYAD in card['defences'] and ActionTypes.ZAKLINANIE in card['defences'] and ActionTypes.MAG_UDAR in card['defences']:
            self.card_signs[card['id']].append('data/icons/zom.png')
        if ActionTypes.VYSTREL in card['defences']:
            self.card_signs[card['id']].append('data/icons/zov.png')
        if ActionTypes.OTRAVLENIE in card['defences']:
            self.card_signs[card['id']].append('data/icons/zoya.png')
        if CardEffect.NAPRAVLENNY_UDAR in card['active_status']:
            self.card_signs[card['id']].append('data/icons/naprav.png')
        if CardEffect.UDAR_CHEREZ_RYAD in card['active_status']:
            self.card_signs[card['id']].append('data/icons/uchr.png')
        if CardEffect.REGEN in card['active_status']:
            self.card_signs[card['id']].append('data/icons/regen.png')
        if CardEffect.NETTED in card['active_status']:
            self.card_signs[card['id']].append('data/icons/spider-web.png')
        rl = RelativeLayout()
        with rl.canvas:
            for i, p in enumerate(self.card_signs[card['id']]):
                im = Image(source=p, pos=(CARD_X_SIZE * 0.01 + i*CARD_X_SIZE * 0.18, CARD_Y_SIZE * 0.16),
                                          size=(CARD_X_SIZE * 0.18, CARD_X_SIZE * 0.18), opacity=0.88)
        self.card_signs_imgs[card['id']] = rl
        base_overlay.add_widget(rl)

    def update_zone_counters(self):
        zones = [(self.dz1_btn, 'extra1', 'Доп. зона'), (self.dz2_btn, 'extra2', 'Доп. зона'),
                 (self.grave1_btn, 'grave1', 'Кладбище'), (self.grave2_btn, 'grave2', 'Кладбище')]
        dz1, dz2, gr1, gr2 = 0, 0, 0, 0
        for card in self.curr_state['cards'].values():
            if (card['player'] == 1 and self.pow == 1) or (card['player'] == 2 and self.pow == 2):
                if card['zone'] == 'gr':
                    gr1 += 1
                elif card['zone'] == 'dz':
                    dz1 += 1
            elif (card['player'] == 2 and self.pow == 1) or (card['player'] == 1 and self.pow == 2):
                if card['zone'] == 'gr':
                    gr2 += 1
                elif card['zone'] == 'dz':
                    dz2 += 1
        for i, (btn, fld, base_txt) in enumerate(zones):
            btn.text = base_txt + ' ('+str([dz1, dz2, gr1, gr2][i])+')'

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
                    border1.rectangle = (0, 0, 0, 0)
                    butt1.pos = p1

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

    def start_timer(self, duration, player, *args):
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

    def display_card_actions(self, data):
        self.selected_card_buttons = []
        for i, (txt, ix, flag) in enumerate(data):
            btn = Button(text=txt,
                         pos=(Window.width * 0.84, Window.height * 0.24 - i * 0.04 * Window.height),
                         disabled=bool(flag), background_color=(1, 0, 0, 1), border=[1, 1, 1, 1],
                         size=(Window.width * 0.14, Window.height * 0.04))
            btn.bind(on_press=partial(self.ability_clicked, ix))
            self.root.add_widget(btn)
            self.selected_card_buttons.append(btn)

    def display_moves(self, moves):
        for move in moves:
            x, y = self.card_position_coords[move][0], self.card_position_coords[move][1]
            rl = RelativeLayout(pos=(x, y), size=(CARD_X_SIZE, CARD_Y_SIZE), size_hint=(None, None))
            btn = Button(size=(CARD_X_SIZE, CARD_Y_SIZE), size_hint=(None, None), background_color=(0, 0, 0, 0))
            rl.add_widget(btn)
            btn.bind(on_press=partial(self.mark_clicked, move))
            with rl.canvas:
                Color(1, 0, 0, 1)
                Ellipse(pos=(CARD_X_SIZE / 2 - 10, CARD_Y_SIZE / 2 - 10), size=(20, 20))
            self.root.add_widget(rl)
            self.nav_buttons.append(rl)

    def card_clicked(self, card, *args):
        if self.mode == 'online':
            pass
        else:
            ability_names, moves = self.backend.card_clicked(card['id'], self.pow)
        return ability_names, moves

    def ability_clicked(self, ix, *args):
        if self.mode == 'online':
            pass
        else:
            self.backend.ability_clicked(ix)

    def mark_clicked(self, mark, *args):
        if self.mode == 'online':
            pass
        else:
            self.backend.mark_clicked(mark)

    def update_card_buttons(self, ability_names):
        self.destroy_x(self.selected_card_buttons)
        self.selected_card_buttons = []
        self.display_card_actions(ability_names)

    def on_click_on_card(self, card, instance):
        if mouse == 'left':
            if self.selected_card:
                Clock.schedule_once(partial(self.draw_card_overlay, self.selected_card, 0))
            if self.nav_buttons:
                self.destroy_x(self.nav_buttons)
                self.nav_buttons = []
            self.bright_card_overlay(card)
            self.selected_card = card
            self.draw_selection_border(instance.parent, card)
            ability_names, moves = self.card_clicked(card)
            self.update_card_buttons(ability_names)
            self.display_moves(moves)


    def add_dopzones(self, position_scroll, position_butt, position_butt2, zone_name, button_name, gl_name, txt, player, button_func):
        if zone_name == 'dop_zone_1' or zone_name == 'dop_zone_2':
            size_ = (CARD_X_SIZE, Window.height * 0.45)
        else:
            size_ = (0, 0)
        scroll = ScrollView(bar_pos_x='top', always_overscroll=False, do_scroll_x=False,
                                     size=size_, size_hint=(None, None),
                                     pos=position_scroll)
        scroll.scroll_timeout = 0
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

    def draw_from_state_init(self):
        cards = self.curr_state['cards'].values()
        for card in cards:
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
            btn1 = Button(disabled=False, pos=(0, CARD_Y_SIZE * 0.16), background_down=card['pic'],
                          background_normal=card['pic'], size=(CARD_X_SIZE, CARD_Y_SIZE * 0.84), border=(0, 0, 0, 0),
                          size_hint=(None, None))
            if card['zone'] == 'dz':
                rl1 = RelativeLayout(size=(CARD_X_SIZE, CARD_Y_SIZE))
                if (card['player'] == 1 and self.pow == 1) or (card['player'] == 2 and self.pow == 2):
                    self.dop_zone_1_gl.add_widget(rl1)
                    self.dop_zone_1_buttons.append(rl1)
                elif (card['player'] == 2 and self.pow == 1) or (card['player'] == 1 and self.pow == 2):
                    self.dop_zone_2_gl.add_widget(rl1)
                    self.dop_zone_2_buttons.append(rl1)
            elif card['zone'] == 'gr':
                rl1 = RelativeLayout(size=(CARD_X_SIZE, CARD_Y_SIZE))
                if (card['player'] == 1 and self.pow == 1) or (card['player'] == 2 and self.pow == 2):
                    self.grave_1_gl.add_widget(rl1)
                    self.grave_buttons_1.append(rl1)
                elif (card['player'] == 2 and self.pow == 1) or (card['player'] == 1 and self.pow == 2):
                    self.grave_2_gl.add_widget(rl1)
                    self.grave_buttons_2.append(rl1)
            else:
                x, y = self.card_position_coords[card['loc']]
                rl1 = RelativeLayout(pos=(x, y))

            btn1.bind(on_press=partial(self.on_click_on_card, card))
            btn1.bind(on_press=partial(self.card_popup, card))
            btn1.bind(on_touch_up=self.card_popup_destr)
            rl1.add_widget(btn1)

            base_overlay_layout = RelativeLayout()
            with base_overlay_layout.canvas:
                # Life
                Color(0, 0.3, 0.1)
                Rectangle(size=(CARD_X_SIZE*0.33, CARD_Y_SIZE*0.15), color=(1,1,1,0.3),
                          pos=(1, CARD_Y_SIZE*0.85)) #pos_hint={'x':0, 'y':0.8}
                Color(1, 1, 1)
                Line(width=0.5, color=(1,1,1,0), rectangle=(1, CARD_Y_SIZE*0.85, CARD_X_SIZE*0.33, CARD_Y_SIZE*0.15))
                lbl = Label(pos=(3, CARD_Y_SIZE*0.85), text=f"{card['curr_life']}/{card['life']}", color=(1, 1, 1, 1), size=(CARD_X_SIZE * 0.3, CARD_Y_SIZE * 0.15),
                   font_size=Window.height*0.02, valign='top')
                self.hp_label_dict[card['id']] = lbl
                # Movement
                Color(0.6, 0, 0)
                Rectangle(pos=(CARD_X_SIZE * 0.73, CARD_Y_SIZE * 0.85), size=(CARD_X_SIZE * 0.27, CARD_Y_SIZE * 0.15),
                          color=(1, 1, 1, 0.3), pos_hint=(None, None))
                Color(1, 1, 1)
                Line(width=0.5, color=(1, 1, 1, 0),
                     rectangle=(CARD_X_SIZE * 0.74, CARD_Y_SIZE*0.85, CARD_X_SIZE * 0.25, CARD_Y_SIZE*0.15))
                lbl = Label(pos=(CARD_X_SIZE * 0.73, CARD_Y_SIZE * 0.85), text=f"{card['curr_move']}/{card['move']}", color=(1, 1, 1, 1),
                            size=(CARD_X_SIZE * 0.3, CARD_Y_SIZE * 0.15),
                            pos_hint=(None, None), font_size=Window.height*0.02)
                self.move_label_dict[card['id']] = lbl

            self.base_overlays[card['id']] = base_overlay_layout
            Clock.schedule_once(partial(self.draw_card_overlay, card, 0))
            rl1.add_widget(base_overlay_layout)
            self.cards_dict[card['id']] = rl1
            self.id_card_dict[card['id']] = card
            if card['curr_fishka'] > 0:
                self.add_fishki_gui(card)
            if card['zone'] == 'board':
                self.layout.add_widget(rl1)
            self.update_zone_counters()
            self.add_defence_signs(card)

        # # Строй
        # for card in cards:
        #     stroy_neighbors = self.backend.board.get_adjacent_with_stroy(card.loc)
        #     if len(stroy_neighbors) != 0 and not card.in_stroy and card.stroy_in:
        #         card.stroy_in()

    def move_card(self, card, move):
        x, y = self.card_position_coords[move]
        anim = Animation(x=x, y=y, duration=0.5)
        anim.start(self.cards_dict[card])
        self.destroy_x(self.nav_buttons)
        self.nav_buttons = []

    def display_damage(self, target_card, dmg):
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

    def update_labels(self, old, new):
        self.move_label_dict[new['id']].text = f'{new["curr_move"]}/{new["move"]}'
        if new['curr_life'] != old['curr_life'] or new['life'] != old['life']:
            self.hp_label_dict[new['id']].text = f'{new["curr_life"]}/{new["life"]}'
            self.display_damage(new["id"], int(new['curr_life'])-int(old['curr_life']))
        if new['curr_fishka'] > 0:
            self.add_fishki_gui(new)
        else:
            self.remove_fishki_gui(new)

    def tap_card(self, card, tap=True):
        scatter_obj = self.cards_dict[card['id']]
        for obj_ in scatter_obj.children:
            if isinstance(obj_, Button):
                ch = obj_
        if tap:
            ch.background_normal = card['pic'][:-4]+'_rot90.jpg'
            ch.background_down = card['pic'][:-4] + '_rot90.jpg'
            ch.pos = (CARD_X_SIZE*0.16, 0)
            ch.size = (CARD_X_SIZE*0.84, CARD_Y_SIZE)
            self.draw_card_overlay(card, 1)
        else:
            ch.background_normal = card['pic']
            ch.background_down = card['pic']
            self.draw_card_overlay(card, 2)
            ch.pos = (0, CARD_Y_SIZE * 0.16)
            ch.size = (CARD_X_SIZE, CARD_Y_SIZE*0.84)

    def display_available_targets(self):
        pass

    def draw_from_state_diff(self, state):
        new_state = state
        old_state = self.curr_state
        for card_id in new_state['cards'].keys():
            if old_state['cards'][card_id]['loc'] != new_state['cards'][card_id]['loc']:
                self.move_card(card_id, new_state['cards'][card_id]['loc'])
            self.update_labels(old_state['cards'][card_id], new_state['cards'][card_id])
            if old_state['cards'][card_id]['tapped'] and not new_state['cards'][card_id]['tapped']:  # tap check
                self.tap_card(new_state['cards'][card_id], tap=False)
            elif not old_state['cards'][card_id]['tapped'] and new_state['cards'][card_id]['tapped']:
                self.tap_card(new_state['cards'][card_id], tap=True)
            if card_id == self.selected_card['id']:
                self.update_card_buttons(new_state['cards'][card_id]['abilities'])
            self.add_defence_signs(new_state['cards'][card_id])
        self.curr_state = new_state
        if new_state['markers']:
            self.display_available_targets()

    def on_state_recieved(self, state):
        if not self.curr_state:
            self.curr_state = state
            self.draw_from_state_init()
        else:
            self.draw_from_state_diff(state)
        self.timer_state = state['timer']
        if self.timer_state['restart']:
            self.start_timer(self.timer_state['duration'], '1')
        self.butt_state = state['butt_state']
        self.ph_button.disabled = not(bool(self.butt_state[0]))
        self.eot_button.disabled = not(bool(self.butt_state[1]))

    def build(self):
        if self.mode == 'online':
            network.on_entering_next_screen(self.backend.server_ip, self.backend.server_port, self.backend.turn, self)
        root = MainField()
        with root.canvas:
            root.bg_rect = Rectangle(source='data/bg/dark_bg_7.jpg', pos=root.pos, size=Window.size)
        root.add_widget(Vertical())
        root.add_widget(Horizontal())

        # generate board coords
        self.layout = FloatLayout(size=(0, 0))
        self.card_position_coords = [None for _ in range(30)]
        # card overlay dictds
        self.base_overlays = {}
        self.hp_label_dict = {}
        self.move_label_dict = {}
        self.fishka_dict = {}
        self.fishka_label_dict = {}
        self.card_signs_imgs = {}
        self.card_signs = defaultdict(list)
        self.damage_marks = []

        self.selected_card = None
        self.card_nameplates = []
        self.cards_dict = {}
        self.card_nameplates_dict = defaultdict(RelativeLayout)
        self.selected_card_buttons = []
        self.nav_buttons = []
        self.grave_buttons_1 = []
        self.grave_buttons_2 = []
        self.id_card_dict = {}

        # self.defender_set = False
        # self.eot_button_disabled = False
        # self.pending_attack = None
        # self.disabled_actions = False
        # self.exit_stack = False
        # self.proxi_ability = None
        # self.target_marks_buttons = []
        # self.pereraspredelenie_label_dict = defaultdict(int)
        # self.pereraspredelenie_dict = {}
        # self.die_pics = []
        # self.red_arrows = []
        # self.target_rectangles = []
        # self.target_marks_cards = []
        # self.curr_id_on_bord = 0
        # self.selection_flicker_dict = {}
        # self.stack_cards = []
        # self.multiple_targets_list = []
        # self.garbage = []
        # self.garbage_dict = {}

        for i in range(5):
            for j in range(6):
                btn1 = Button(text=str(i * 6 + j), disabled=False, opacity=0.8,
                              pos=(Window.width * 0.25 + i * CARD_X_SIZE,
                                   Window.height * 0.03 + j * CARD_Y_SIZE),
                              size=(CARD_X_SIZE, CARD_Y_SIZE), size_hint=(None, None))
                if self.pow == 1:
                    self.card_position_coords[i * 6 + j] = (btn1.x, btn1.y)
                else:
                    self.card_position_coords[29-(i * 6 + j)] = (btn1.x, btn1.y)
                #self.layout.add_widget(btn1)

        # when user clicked on square outside red move marks
        Window.bind(on_touch_down=self.delete_move_marks_on_unfocus)
        # # when user clicked on square outside target card
        # Window.bind(on_touch_down=self.delete_target_marks_on_unfocus)
        # popup on right click
        root.add_widget(self.layout)

        # Button for phase skip
        self.ph_button = Button(text="Пропустить", disabled=True,
                              pos=(Window.width * 0.83, Window.height * 0.28), background_color=(1,0,0,1),
                                   size=(Window.width * 0.08, Window.height * 0.05), size_hint=(None, None))
        # self.ph_button.bind(on_press=self.backend.player_passed)
        # self.ph_button.bind(on_press=Clock.schedule_once(self.check_all_passed))
        # self.ph_button.bind(on_press=partial(self.start_timer, STACK_DURATION))
        # self.ph_button.bind(on_press=self.destroy_flickering)
        # if self.backend.mode == 'online':
        #     self.ph_button.bind(on_press=partial(network.ph_pressed, self.backend.server_ip, self.backend.server_port,
        #                                           self.backend.turn))
        self.layout.add_widget(self.ph_button)
        #
        # Button for end of turn
        self.eot_button = Button(text="Сл. Фаза", disabled=False,
                           pos=(Window.width * 0.91, Window.height * 0.28), background_color=(1,0,0,1),
                           size=(Window.width * 0.08, Window.height * 0.05), size_hint=(None, None))
        # self.eot_button.bind(on_press=self.backend.next_game_state)
        # self.eot_button.bind(on_press=Clock.schedule_once(self.update_timer_text, ))
        # self.eot_button.bind(on_press=partial(self.start_timer, TURN_DURATION))
        # if self.backend.mode == 'online':
        #     self.eot_button.bind(on_press=partial(network.eot_pressed, self.backend.server_ip, self.backend.server_port, self.backend.turn))
        #     if self.pow != self.backend.current_active_player:
        #         self.eot_button.disabled = True
        self.layout.add_widget(self.eot_button)

        self.timer_label = Label()
#        self.backend.start()
        #Clock.schedule_once(lambda x: self.start_timer(TURN_DURATION))  # BUGGY?

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

        root_input = TouchInput()
        Clock.schedule_once(lambda x: root.add_widget(root_input))
        Clock.schedule_once(lambda x: self.load_complete())
        return root



