import kivy
kivy.require('2.0.1')
from kivy import Config
Config.set('input', 'mouse', 'mouse,multitouch_on_demand')
from kivy.core.window import Window
from kivy.uix.floatlayout import FloatLayout
from kivy.app import App
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.button import Button
from kivy.uix.widget import Widget
from kivy.uix.label import Label
from kivy.graphics import Line, Color, Rectangle, Ellipse
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.image import Image
from game import Game
import berserk_gui
from game_properties import GameStates
from cards.card import *
import placement
import os
import copy
from functools import partial
from deck import *

class MainField(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

class DeckApp(App):

    def __init__(self, window_size, **kwargs):
        super(DeckApp, self).__init__(**kwargs)
        Window.size = window_size
        self.window_size = window_size
        global CARD_X_SIZE, CARD_Y_SIZE, STACK_DURATION, TURN_DURATION, DZ_SIZE
        CARD_X_SIZE = (Window.width * 0.07)
        CARD_Y_SIZE = CARD_X_SIZE  # (Window.height * 0.15)
        self.title = 'Berserk Renewal'
        l = Library()
        l.load()
        self.all_cards = []
        for x in range(4):
            self.all_cards.extend(l.get_cards())

    def draw_card_overlay(self, card):
        size_ = (CARD_X_SIZE - 2, CARD_Y_SIZE * 0.18)
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
            name = (card.name[:10] + '..') if len(card.name) > 10 else card.name
            lbl_ = Label(pos=(0, 0), text=f'{name}', color=c1,
                         size=size_,
                         font_size=Window.height * 0.02, )
            self.card_nameplates.append(lbl_)
            if card.cost[0] == 0:
                Color(0.9, 0.9, 0.9)
                cost = card.cost[1]
            else:
                Color(1, 1, 0)
                cost = card.cost[0]
            Rectangle(pos=(1, 0.18 * CARD_Y_SIZE + 1), size=(CARD_X_SIZE * 0.27, CARD_Y_SIZE * 0.15),
                      color=(1, 1, 1, 0.3), pos_hint=(None, None))
            Color(0, 0, 0)
            Line(width=0.5, color=(1, 1, 1, 0),
                 rectangle=(1, CARD_Y_SIZE * 0.18 + 1, CARD_X_SIZE * 0.27, CARD_Y_SIZE * 0.15))
            lbl = Label(pos=(1, 0.18 * CARD_Y_SIZE + 1), text=f'{cost}',
                        color=(0, 0, 0, 1),
                        size=(CARD_X_SIZE * 0.3, CARD_Y_SIZE * 0.15),
                        pos_hint=(None, None), font_size=Window.height * 0.02)
            self.cost_labels.append(lbl)
            self.card_nameplates.append(lbl_)
            lyy.add_widget(ly)

    def display_cards(self):
        for i, card in enumerate(self.hand):
            x, y = self.card_position_coords_initial[i]
            rl1 = RelativeLayout(pos=(x, y), size=(CARD_X_SIZE, CARD_X_SIZE), size_hint=(None, None))
            btn1 = Button(disabled=False, pos=(0, CARD_Y_SIZE * 0.18), background_down=card.pic,
                          background_normal=card.pic, size=(CARD_X_SIZE, CARD_Y_SIZE * 0.85), size_hint=(None, None), border=(0,0,0,0))
            btn1.bind(on_press=partial(self.move_card, card))
            rl1.add_widget(btn1)
            self.base_overlays[card] = RelativeLayout()
            rl1.add_widget(self.base_overlays[card])
            self.draw_card_overlay(card)
            self.layout.add_widget(rl1)
            self.card_dict[card] = rl1
            self.cards_up.append(card)
            self.max_top += 1

    def build(self):
        root = MainField()
        self.card_position_coords_initial = [None for x in range(18)]
        self.card_position_coords_modified = [None for x in range(18)]
        self.layout = FloatLayout(size=(Window.width, Window.height))
        self.base_overlays = {}
        self.card_dict = {}
        self.card_nameplates = []
        self.cost_labels = []
        self.cards_up = []
        self.cards_down = []
        self.max_top = 0
        self.max_bottom = 0
        print(len(self.all_cards))

        with root.canvas:
            root.bg_rect = Rectangle(source='data/bg/dark_bg_7.jpg', pos=root.pos, size=Window.size)
            points_x = [(Window.width * 0.2 + i * CARD_X_SIZE, Window.height * 0.675,
                         Window.width * 0.2 + i * CARD_X_SIZE, Window.height * 0.924) for i in range(9)]
            points_y = [(Window.width * 0.2, Window.height * 0.55 + i * CARD_X_SIZE,
                         Window.width * 0.76, Window.height * 0.55 + i * CARD_X_SIZE) for i in range(1, 4)]
            for i in range(3):
                c = Color(1, 1, 1, 0)
                Line(color=c, points=points_y[i])
            for j in range(9):
                Line(color=c, points=points_x[j])
            c1 = Color(0.5, 0, 0, 1)
            Line(color=c, points=(Window.width * 0.15, 0,
                                  Window.width * 0.15, Window.height), width=4)
            Line(color=c, points=(Window.width * 0.8, 0,
                                  Window.width * 0.8, Window.height), width=4)
            Line(color=c, points=(Window.width * 0.15, Window.height * 0.5,
                                  Window.width * 0.80, Window.height * 0.5), width=4)

        numrows = len(self.all_cards)//8+1
        for i in range(8):
            for j in range(numrows):
                btn1 = Button(text=str(i + (1 - j) * 8), disabled=False, opacity=0.8,
                              pos=(Window.width * 0.2 + i * CARD_X_SIZE,
                                   Window.height * 0.675 + j * CARD_X_SIZE),
                              size=(CARD_X_SIZE, CARD_Y_SIZE), size_hint=(None, None))
                btn2 = Button(text=str(i + (1 - j) * 8), disabled=False, opacity=0.8,
                              pos=(Window.width * 0.2 + i * CARD_X_SIZE,
                                   Window.height * 0.2 + j * CARD_X_SIZE),
                              size=(CARD_X_SIZE, CARD_Y_SIZE), size_hint=(None, None))
                print(i, j, i*8 + j)
                # self.card_position_coords_initial[i + (numrows - j) * 8] = (btn1.x, btn1.y - (numrows - j) * 5)
                # self.card_position_coords_modified[i + (numrows - j) * 8] = (btn2.x, btn2.y - (numrows - j) * 5)
                # self.layout.add_widget(btn1)
                # self.layout.add_widget(btn2)

        # layout = GridLayout(cols=1, spacing=10, size_hint_y=None)
        # layout.bind(minimum_height=layout.setter('height'))
        # for i in range(100):
        #     btn = Button(text=str(i), size_hint_y=None, height=40)
        #     layout.add_widget(btn)
        # root = ScrollView(size_hint=(1, None), size=(Window.width, Window.height))
        # # self.layout.add_widget(layout)

        root.add_widget(self.layout)
        return root


WINDOW_SIZE = (960, 540) #(1920, 1080) #
f = DeckApp(WINDOW_SIZE)
f.run()
