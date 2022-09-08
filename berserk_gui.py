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

    def __init__(self, window_size, stack_duration=10, turn_duration=10, pow=1, mode='offline', backend=None,
                 server_ip=None, server_port=None):
        super(BerserkApp, self).__init__()
        self.backend = backend
        self.mode = mode
        self.pow = pow
        self.window_size = window_size
        self.server_ip = server_ip
        self.server_port = server_port
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
            network.client_loaded(self.server_ip, self.server_port, self.pow)
        else:
            self.backend.on_load()

    def destroy_red_arrows(self, *args):
        if self.red_arrows:
            for el in self.root.canvas.children:
                if el in self.red_arrows:
                    self.root.canvas.remove(el)
                    self.red_arrows.remove(el)

    def draw_red_arrows(self, arrow_list):
        with self.root.canvas:
            c = Color(1, 0, 0, 0.8)
            # print('arrow_list', arrow_list)
            for fr, to, type_ in arrow_list:
                if to is None:
                    continue
                if self.id_card_dict[fr]['zone'] == 'dz':
                    if (self.id_card_dict[fr]['player'] == 1 and self.pow == 1) or (self.id_card_dict[fr]['player'] == 2 and self.pow == 2):
                        x, y = self.dop_zone_1.to_parent(*self.cards_dict[fr].pos)
                    else:
                        x, y = self.dop_zone_2.to_parent(*self.cards_dict[fr].pos)
                elif self.id_card_dict[fr]['zone'] == 'board':
                    x, y = self.cards_dict[fr].pos
                if type_ == 'card':
                    if self.id_card_dict[to]['zone'] == 'dz':
                        if (self.id_card_dict[to]['player'] == 1 and self.pow == 1) or (
                                self.id_card_dict[to]['player'] == 2 and self.pow == 2):
                            n, m = self.dop_zone_1.to_parent(*self.cards_dict[to].pos)
                        else:
                            n, m = self.dop_zone_2.to_parent(*self.cards_dict[to].pos)
                    elif self.id_card_dict[to]['zone'] == 'board':
                        n, m = self.cards_dict[to].pos
                elif type_ == 'cell':
                    n, m = self.card_position_coords[to]
                l = Line(width=3, color=c, points=(x + CARD_X_SIZE / 2, y + CARD_Y_SIZE / 2,
                                                   n + CARD_X_SIZE / 2, m + CARD_Y_SIZE / 2))
                self.red_arrows.append(l)
        Clock.schedule_once(self.destroy_red_arrows, 2)
            # TODO
            # tri = Triangle(color=c, points=[x*0.7+(x-n)*0.15*0.57, (x-n)*0.85+n*0.1,
            #                                  n+CARD_X_SIZE/2, m+CARD_Y_SIZE/2,
            #                                 x*0.7+(x-n)*0.15*0.57, (y-m)*0.85+m])
            #self.red_arrows.append(tri)

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

    def check_children(self, list_):
        for bt in list_:
            if bt in self.root.children:
                return True
        return False


    def destroy_target_marks(self, *args):
        for btn, card in self.target_marks_cards:
            card.remove_widget(btn)
        for r, canvas in self.target_rectangles:
            canvas.remove(r)
        self.target_rectangles = []
        self.target_marks_buttons = []
        self.target_marks_cards = []

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
            print('play_attack_sound ', e)

    def start_flickering(self, card_id, player=1):
        rl = RelativeLayout()
        self.base_overlays[card_id].add_widget(rl)
        with rl.canvas:
            col = Color(1, 1, 1, 0.2)
            rect = Rectangle(size=(CARD_X_SIZE, CARD_Y_SIZE),
                             background_color=col,
                             pos=(0, 0), size_hint=(1, 1))
            anim = Animation(opacity=0, duration=0.5) + Animation(opacity=1, duration=0.5)
            anim.repeat = True
            anim.start(rl)
            self.selection_flicker_dict[card_id] = rl

    def destroy_flickering(self, *args):
        for c in self.selection_flicker_dict.keys():
            self.base_overlays[c].remove_widget(self.selection_flicker_dict[c])

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
        if card['id'] not in self.fishka_dict.keys():
            base_overlay.add_widget(rl)
        else:
            base_overlay.remove_widget(self.fishka_dict[card['id']])
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
            if card['player'] == self.pow:
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
        self.timer_label.text = self.timer_state['state_name'] + ' ' + str(int(total_min-minutes))+':'+str(int(duration-rem_m*60-seconds)).zfill(2)
        # self.timer_label.text = 'TODO' + ' ' + str(int(total_min-minutes))+':'+str(int(duration-rem_m*60-seconds)).zfill(2)

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
            self.lbl = Label(text=self.timer_state['state_name'],
                        pos=(Window.width * 0.88, Window.height * 0.35), color=(0, 0, 0, 1),
                        size=(CARD_X_SIZE * 0.3, CARD_Y_SIZE * 0.2),
                        pos_hint=(None, None), font_size=str(Window.height * 0.016))
            self.timer_label = self.lbl
        self.root.add_widget(self.timer_ly)
        self.timer = Animation(s=1 / 30, duration=duration)
        self.timer.bind(on_progress=partial(self.timer_update, duration))
        self.timer.bind(on_complete=self.timer_completed)
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
            network.card_clicked(self.server_ip, self.server_port, self.pow, card['id'])
        else:
            self.backend.card_clicked(card['id'], self.pow)

    def ability_clicked(self, ix, *args):
        if self.mode == 'online':
            network.ability_clicked(self.server_ip, self.server_port, self.pow, ix)
        else:
            self.backend.ability_clicked(ix, self.pow)

    def mark_clicked(self, mark, *args):
        self.mark_clicked_list.append(mark)
        if len(self.mark_clicked_list) == len(self.curr_state['markers']):
            if self.mode == 'online':
                network.mark_clicked(self.server_ip, self.server_port, self.pow, self.mark_clicked_list)
            else:
                self.backend.mark_clicked(self.mark_clicked_list, self.pow)
            self.mark_clicked_list = []

    def eot_clicked(self, *args):
        if self.mode == 'online':
            network.eot_pressed(self.server_ip, self.server_port, self.pow)
        else:
            self.backend.eot_clicked()

    def ph_clicked(self, *args):
        if self.mode == 'online':
            network.ph_pressed(self.server_ip, self.server_port, self.pow)
        else:
            self.backend.ph_clicked()

    def timer_completed(self, *args):
        try:
            self.popup_.dismiss()
            if self.default_popup_option:
                if self.mode == 'online':
                    network.pop_up_clicked(self.server_ip, self.server_port, self.pow, self.default_popup_option[0], self.default_popup_option[1])
                else:
                    self.backend.pop_up_clicked(self.default_popup_option[0], self.default_popup_option[1])
                self.default_popup_option = []
        except:
            pass
        if self.mode == 'online' and self.pow == 1:
            network.timer_completed(self.server_ip, self.server_port, self.pow)
        elif self.mode == 'online' and self.pow == 2:
            pass
        else:
            self.backend.timer_completed()

    def pop_up_clicked(self, i, type_, *args):
        self.default_popup_option = []
        if self.mode == 'online':
            network.pop_up_clicked(self.server_ip, self.server_port, self.pow, i, type_)
        else:
            self.backend.pop_up_clicked(i, type_)

    def update_card_buttons(self, ability_names):
        self.destroy_x(self.selected_card_buttons)
        self.selected_card_buttons = []
        self.display_card_actions(ability_names)

    def on_click_on_card(self, card, instance):
        self.destroy_target_marks()
        if mouse == 'left':
            if self.selected_card:
                Clock.schedule_once(partial(self.draw_card_overlay, self.selected_card, 0))
            if self.nav_buttons:
                self.destroy_x(self.nav_buttons)
                self.nav_buttons = []
            self.bright_card_overlay(card)
            self.selected_card = card
            self.draw_selection_border(instance.parent, card)
            self.card_clicked(card)
            # self.update_card_buttons(ability_names)
            # self.display_moves(moves)

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

    def draw_from_state_init(self, cards):
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
            self.play_attack_sound(int(new['curr_life'])-int(old['curr_life']))
        if old['curr_fishka'] < new['curr_fishka'] or (old['curr_fishka'] > new['curr_fishka'] and new['curr_fishka'] > 0):
            self.add_fishki_gui(new)
        elif old['curr_fishka'] > 0 and new['curr_fishka'] <= 0:
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
        self.mark_clicked_list = []
        targets = self.curr_state['markers']
        self.display_available_targets_helper(targets, 1, len(targets))

    def display_available_targets_helper(self, targets, i, total, *args):
        self.destroy_target_marks()
        b_size = 30  # размер квадратика
        target_dict = targets[i-1]
        target_list_cards = []
        target_list_cells = []
        if 'card_ids' in target_dict.keys():
            target_list_cards = target_dict['card_ids']
        elif 'cells' in target_dict.keys():
            target_list_cells = target_dict['cells']
        for t in target_list_cards:
            with self.cards_dict[t].canvas:
                btn = Button(pos=(0, 0),
                             background_color=(1, 1, 1, 0.0),
                             size=(CARD_X_SIZE, CARD_Y_SIZE), size_hint=(None, None))
                if self.id_card_dict[t]['player'] == self.pow:
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
                btn.bind(on_press=partial(self.mark_clicked, t))
            if i < total:
                btn.bind(on_press=partial(self.display_available_targets_helper, targets, i+1, total))

            self.target_rectangles.append((rect1, self.cards_dict[t].canvas))
            self.target_rectangles.append((rect2, self.cards_dict[t].canvas))
            self.cards_dict[t].add_widget(btn)
            self.target_marks_cards.append([btn, self.cards_dict[t]])
            self.target_marks_buttons.append(t)

        for t in target_list_cells:
            pos = self.card_position_coords[t]
            rl = RelativeLayout(pos=pos, size=(CARD_X_SIZE, CARD_Y_SIZE), size_hint=(None, None))
            btn = Button(size=(CARD_X_SIZE, CARD_Y_SIZE), size_hint=(None, None), background_color=(0, 0, 0, 0))
            with rl.canvas:
                Color(1, 0, 0, 1)
                Ellipse(pos=(CARD_X_SIZE / 2 - 10, CARD_Y_SIZE / 2 - 10), size=(20, 20))
                rl.add_widget(btn)
                self.nav_buttons.append(rl)
            btn.bind(on_press=partial(self.mark_clicked, t))
            if i < total:
                btn.bind(on_press=partial(self.display_available_targets_helper, targets, i+1, total))
            self.root.add_widget(rl)
            self.target_marks_buttons.append(t)

    def card_remover(self, card, prev_zone, *args):
        if prev_zone == 'dz':
            if (card['player'] == 1 and self.pow == 1) or (card['player'] == 2 and self.pow == 2):
                self.dop_zone_1.children[0].remove_widget(self.cards_dict[card['id']])
            else:
                self.dop_zone_2.children[0].remove_widget(self.cards_dict[card['id']])
        else:
            self.layout.remove_widget(self.cards_dict[card['id']])
        rl1 = RelativeLayout(size=(CARD_X_SIZE, CARD_Y_SIZE))
        btn1 = Button(disabled=False, pos=(0, CARD_Y_SIZE * 0.16), background_down=card['pic'],
                      background_normal=card['pic'], size=(CARD_X_SIZE, CARD_Y_SIZE * 0.84), border=(0, 0, 0, 0),
                      size_hint=(None, None))
        btn1.bind(on_press=partial(self.card_popup, card))
        btn1.bind(on_touch_up=self.card_popup_destr)
        rl1.add_widget(btn1)
        self.cards_dict[card['id']] = rl1
        self.base_overlays[card['id']] = RelativeLayout()
        Clock.schedule_once(partial(self.draw_card_overlay, card, 3))
        rl1.add_widget(self.base_overlays[card['id']])
        if (card['player'] == 1 and self.pow == 1) or (card['player'] == 2 and self.pow == 2):
            self.grave_1_gl.add_widget(rl1)
            self.grave_buttons_1.append(rl1)
        elif (card['player'] == 2 and self.pow == 1) or (card['player'] == 1 and self.pow == 2):
            self.grave_2_gl.add_widget(rl1)
            self.grave_buttons_2.append(rl1)
        self.update_zone_counters()

    def move_to_grave(self, card, prev_zone):
        for el in self.cards_dict[card['id']].children:
            if isinstance(el, Button):
                anim = Animation(pos=(CARD_Y_SIZE/2, CARD_Y_SIZE/2), size=(0, 0), d=0.5, s=1/60, t='in_back')
                anim.bind(on_complete=partial(self.card_remover, card, prev_zone))
                anim.start(el)
            else:
                el.opacity = 0

    def move_from_grave(self, card):
        print('ressurrect: ', card, card['zone'])
        self.draw_from_state_init([card])


    def on_game_end(self, text_):
        rl = RelativeLayout()
        rl.add_widget(Label(text=text_, font_size=Window.height * 0.05, pos=(0, Window.height * 0.05)))
        btn = Button(text='В меню', background_color=(1, 0, 0, 1), size_hint=(0.5, 0.2), pos=(Window.width * 0.1, 0))
        btn.bind(on_press=lambda x: self.stop())
        btn.bind(on_press=lambda x: MainMenuApp(self.window_size).run())
        rl.add_widget(btn)
        popup = OmegaPopup(title='', separator_height=0, overlay_color=(0, 0, 0, 0),
                           content=rl, background_color=(1, 0, 0, 1),
                           size_hint=(None, None), size=(Window.width * 0.4, Window.height / 4))
        popup.open()

    def draw_die(self, dices):
        clean = False
        for el in dices:
            if el:
                clean = True
        if clean:
            self.destroy_x(self.die_pics)
        if self.pow == 1:
            player_one_part = dices[0]
            player_two_part = dices[1]
        else:
            player_one_part = dices[1]
            player_two_part = dices[0]
        to_draw_1 = []
        to_draw_2 = []
        for set_of_rolls in player_one_part:
            if set_of_rolls:
                bonus = set_of_rolls[1]
                for i, roll in enumerate(set_of_rolls[0]):
                    if roll > 6:
                        roll = 6
                    elif roll < 1:
                        roll = 1
                    to_draw_1.append((roll, bonus))
        for i, (roll, bonus) in enumerate(to_draw_1):
            r1_i = Image(source=f'data/dice/Alea_{roll}.png', pos=(Window.width * 0.78 - 0.07 * Window.width * i, Window.height * 0.8),
                         size=(0.07 * Window.width, Window.height * 0.07))
            with r1_i.canvas:
                if bonus is not None:
                    l = Label(text='+'+str(bonus), pos=(Window.width * 0.78 - 0.07 * Window.width * i, Window.height * 0.7))
                    self.die_pics.append(l)
            self.root.add_widget(r1_i)
            self.die_pics.append(r1_i)
        for set_of_rolls in player_two_part:
            if set_of_rolls:
                bonus = set_of_rolls[1]
                for i, roll in enumerate(set_of_rolls[0]):
                    if roll > 6:
                        roll = 6
                    elif roll < 1:
                        roll = 1
                    to_draw_2.append((roll, bonus))
        for i, (roll, bonus) in enumerate(to_draw_2):
            r2_i = Image(source=f'data/dice/Alea_{roll}.png', pos=(Window.width * 0.12 + 0.07 * Window.width * i, Window.height * 0.8),
                         size=(0.07 * Window.width, Window.height * 0.07))
            with r2_i.canvas:
                if bonus is not None:
                    l = Label(text='+'+str(bonus), pos=(Window.width * 0.12 + 0.07 * Window.width * i, Window.height * 0.7))
                    self.die_pics.append(l)
            self.root.add_widget(r2_i)
            self.die_pics.append(r2_i)

    def create_selection_popup(self, data):
        question = data['q']
        button_texts = data['texts']
        self.default_popup_option = (0, data['type'])
        self.popup_ = OmegaPopup(width=310, height=110, background_color=(1, 0, 0, 1),
                                           overlay_color=(0, 0, 0, 0), size_hint=(None, None),
                                           auto_dismiss=False)
        rl = RelativeLayout(size=self.popup_.size, size_hint=(None, None))
        self.popup_.content = rl
        with rl.canvas:
            l = Label(pos=(70, 20), size_hint=(None, None), text=question, valign='top')
            self.garbage.append(l)

        for i, b_text in enumerate(button_texts):
            btn1 = Button(pos=(0+i*rl.width/len(button_texts), 0), size=(130, 30), background_color=(1, 0, 0, 1),
                          size_hint=(None, None),
                          text=b_text)
            btn1.bind(on_press=partial(self.pop_up_clicked, i, data['type']))
            btn1.bind(on_press=lambda x: self.popup_.dismiss())
            rl.add_widget(btn1)
        self.popup_.open()
        return self.popup_

    def draw_from_state_diff(self, state):
        self.destroy_target_marks()
        self.destroy_flickering()
        new_state = state
        old_state = self.curr_state
        self.curr_state = new_state
        for card_id in new_state['cards'].keys():
            if old_state['cards'][card_id]['zone'] != 'gr' and new_state['cards'][card_id]['zone'] == 'gr':
                self.move_to_grave(new_state['cards'][card_id], prev_zone=old_state['cards'][card_id]['zone'])
            if old_state['cards'][card_id]['zone'] == 'gr' and new_state['cards'][card_id]['zone'] != 'gr':
                self.move_from_grave(new_state['cards'][card_id])
            if old_state['cards'][card_id]['loc'] != new_state['cards'][card_id]['loc']:
                self.move_card(card_id, new_state['cards'][card_id]['loc'])
            self.update_labels(old_state['cards'][card_id], new_state['cards'][card_id])
            if old_state['cards'][card_id]['tapped'] and not new_state['cards'][card_id]['tapped']:  # tap check
                self.tap_card(new_state['cards'][card_id], tap=False)
            elif not old_state['cards'][card_id]['tapped'] and new_state['cards'][card_id]['tapped']:
                self.tap_card(new_state['cards'][card_id], tap=True)
            if self.selected_card:
                if card_id == self.selected_card['id']:
                    self.update_card_buttons(new_state['cards'][card_id]['abilities'])
            self.add_defence_signs(new_state['cards'][card_id])
        if new_state['markers']:
            self.display_available_targets()
        if new_state['flickers']:
            for c in new_state['flickers']:
                self.start_flickering(c)
        if new_state['arrows']:
            self.draw_red_arrows(new_state['arrows'])
        if new_state['dices']:
            self.draw_die(new_state['dices'])
        if new_state['popups']:
            if new_state['popups']['show_to'] == self.pow:
                self.create_selection_popup(new_state['popups'])

    def on_state_received(self, state):
        self.garbage_dict = {}
        if not self.curr_state:
            self.curr_state = state
            cards = self.curr_state['cards'].values()
            self.draw_from_state_init(cards)
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
            network.on_entering_next_screen(self.server_ip, self.server_port, self.pow, self)
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
        self.target_rectangles = []
        self.target_marks_cards = []
        self.target_marks_buttons = []
        self.selection_flicker_dict = {}
        self.mark_clicked_list = []
        self.red_arrows = []
        self.die_pics = []
        self.garbage = []
        self.garbage_dict = {}
        self.default_popup_option = []


        # self.defender_set = False
        # self.eot_button_disabled = False
        # self.pending_attack = None
        # self.disabled_actions = False
        # self.exit_stack = False
        # self.proxi_ability = None
        # self.pereraspredelenie_label_dict = defaultdict(int)
        # self.pereraspredelenie_dict = {}
        # self.curr_id_on_bord = 0
        # self.stack_cards = []
        # self.multiple_targets_list = []

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
        self.ph_button.bind(on_press=self.ph_clicked)
        self.layout.add_widget(self.ph_button)
        #
        # Button for end of turn
        self.eot_button = Button(text="Сл. Фаза", disabled=False,
                           pos=(Window.width * 0.91, Window.height * 0.28), background_color=(1,0,0,1),
                           size=(Window.width * 0.08, Window.height * 0.05), size_hint=(None, None))
        self.eot_button.bind(on_press=self.eot_clicked)
        self.layout.add_widget(self.eot_button)

        self.timer_label = Label()

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



