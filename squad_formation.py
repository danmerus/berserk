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
from game import Game
import berserk_gui
from game_properties import GameStates
from cards.card import *
import placement
import os
import copy
from functools import partial



class MainField(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

class FormationApp(App):

    def __init__(self, backend, window_size, hand, turn, gold_cap, silver_cap):
        super(FormationApp, self).__init__()
        Window.size = window_size
        if window_size == (1920, 1080):
            Window.maximize()
        global CARD_X_SIZE, CARD_Y_SIZE, STACK_DURATION, TURN_DURATION, DZ_SIZE
        CARD_X_SIZE = (Window.width * 0.07)
        CARD_Y_SIZE = CARD_X_SIZE  # (Window.height * 0.15)
        STACK_DURATION = 5
        TURN_DURATION = 6
        DZ_SIZE = (CARD_X_SIZE, Window.height * 0.45)

        self.backend = backend
        self.hand = hand
        self.turn = turn
        self.title = 'Berserk Renewal'
        if turn == 2:
            gold_cap += 1
            silver_cap += 1
        self.gold_cap = gold_cap
        self.silver_cap = silver_cap

    def draw_card_overlay(self, card):
        size_ = (CARD_X_SIZE-2, CARD_Y_SIZE * 0.18)
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
                         font_size=Window.height * 0.02,)
            self.card_nameplates.append(lbl_)
            if card.cost[0] == 0:
                Color(0.9, 0.9, 0.9)
                cost = card.cost[1]
            else:
                Color(1, 1, 0)
                cost = card.cost[0]
            Rectangle(pos=(1, 0.18*CARD_Y_SIZE+1), size=(CARD_X_SIZE * 0.27, CARD_Y_SIZE * 0.15),
                      color=(1, 1, 1, 0.3), pos_hint=(None, None))
            Color(0, 0, 0)
            Line(width=0.5, color=(1, 1, 1, 0),
                 rectangle=(1, CARD_Y_SIZE * 0.18+1, CARD_X_SIZE * 0.27, CARD_Y_SIZE * 0.15))
            lbl = Label(pos=(1, 0.18*CARD_Y_SIZE+1), text=f'{cost}',
                        color=(0, 0, 0, 1),
                        size=(CARD_X_SIZE * 0.3, CARD_Y_SIZE * 0.15),
                        pos_hint=(None, None), font_size=Window.height * 0.02)
            self.cost_labels.append(lbl)
            self.card_nameplates.append(lbl_)
            lyy.add_widget(ly)


    def redraw_up(self):
        if len(self.cards_up) < self.max_top:
            for i, c in enumerate(self.cards_up):
                self.card_dict[c].pos = self.card_position_coords_initial[i]
        self.max_top = len(self.cards_up)

    def redraw_down(self):
        if len(self.cards_down) < self.max_bottom:
            for i, c in enumerate(self.cards_down):
                self.card_dict[c].pos = self.card_position_coords_modified[i]
        self.max_bottom = len(self.cards_down)

    def update_costs(self, card, dir_):
        if dir_ == 'down':
            curr_cols = set([x.color for x in self.cards_down if x.color != CardColor.NEUTRAL])
            if card.color != CardColor.NEUTRAL and card.color not in curr_cols and len(curr_cols) > 0:
                self.penalty += 1
            self.gold_curr -= card.cost[0]
            self.silver_curr -= card.cost[1]
        elif dir_ == 'up':
            new_down = self.cards_down.copy()
            new_down.remove(card)
            curr_cols = set([x.color for x in new_down if x.color != CardColor.NEUTRAL])
            self.penalty = len(curr_cols)-1
            self.gold_curr += card.cost[0]
            self.silver_curr += card.cost[1]

    def cost_check(self, card):
        curr_cols = set([x.color for x in self.cards_down if x.color != CardColor.NEUTRAL])
        temp_penalty = self.penalty
        if card.color != CardColor.NEUTRAL and card.color not in curr_cols:
            temp_penalty += 1
        return all([(self.gold_curr-card.cost[0]-temp_penalty) >= 0, (self.silver_curr-card.cost[1]) >= 0])

    def update_labels(self):
        self.gold_lbl.text = str(self.gold_curr-self.penalty)
        self.penalty_lbl.text = '('+('' if self.penalty == 0 else '-')+str(self.penalty)+')'
        self.silver_lbl.text = str(self.silver_curr)

    def move_card(self, card, *args):
        if card in self.cards_up:
            if self.cost_check(card):
                l = len(self.cards_down)
                x, y = self.card_position_coords_modified[l]
                self.card_dict[card].pos = (x, y)
                self.update_costs(card, 'down')
                self.update_labels()
                self.cards_down.append(card)
                self.cards_up.remove(card)
                self.max_bottom += 1
                self.redraw_up()
        elif card in self.cards_down:
            l = len(self.cards_up)
            x, y = self.card_position_coords_initial[l]
            self.card_dict[card].pos = (x, y)
            self.update_costs(card, 'up')
            self.update_labels()
            self.cards_up.append(card)
            self.cards_down.remove(card)
            self.max_top += 1
            self.redraw_down()

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
        self.layout = FloatLayout(size=(Window.width * 0.8, Window.height))
        self.base_overlays = {}
        self.card_dict = {}
        self.card_nameplates = []
        self.cost_labels = []
        self.cards_up = []
        self.cards_down = []
        self.max_top = 0
        self.max_bottom = 0
        self.gold_curr = self.gold_cap
        self.silver_curr = self.silver_cap
        self.penalty = 0


        with root.canvas:
            root.bg_rect = Rectangle(source='data/bg/dark_bg_7.jpg', pos=root.pos, size=Window.size)
            points_x = [(Window.width * 0.2 + i * CARD_X_SIZE, Window.height*0.675,
                       Window.width * 0.2 + i * CARD_X_SIZE, Window.height*0.924) for i in range(9)]
            points_y = [(Window.width*0.2,  Window.height*0.55 + i*CARD_X_SIZE,
                         Window.width*0.76,  Window.height*0.55 + i*CARD_X_SIZE) for i in range(1, 4)]
            for i in range(3):
                c = Color(1, 1, 1, 0)
                Line(color=c, points=points_y[i])
            for j in range(9):
                Line(color=c, points=points_x[j])
            c1 = Color(0.5, 0, 0, 1)
            Line(color=c, points=(Window.width * 0.15, 0,
                       Window.width * 0.15, Window.height), width=4)
            Line(color=c, points=(Window.width * 0.85, 0,
                                  Window.width * 0.85, Window.height), width=4)
            Line(color=c, points=(Window.width*0.15, Window.height*0.5,
                                  Window.width*0.85, Window.height*0.5), width=4)

            self.gold_lbl = Label(pos=(0.88*Window.width, Window.height * 0.75), text=f'{self.gold_cap}', color=(1, 1, 1, 1),
                        size=(CARD_X_SIZE * 0.15, CARD_Y_SIZE * 0.15),
                        font_size=Window.height * 0.05, valign='top')
            self.penalty_lbl = Label(pos=(0.93*Window.width, Window.height * 0.75), text=f'({self.penalty})', color=(1, 1, 1, 1),
                        size=(CARD_X_SIZE * 0.15, CARD_Y_SIZE * 0.15),
                        font_size=Window.height * 0.05, valign='top')
            self.silver_lbl = Label(pos=(0.88*Window.width, Window.height * 0.7), text=f'{self.silver_cap}', color=(1, 1, 1, 1),
                        size=(CARD_X_SIZE * 0.15, CARD_Y_SIZE * 0.15),
                        font_size=Window.height * 0.05, valign='top')

        for i in range(8):
            for j in range(2):
                btn1 = Button(text=str(i + (1-j)*8), disabled=False, opacity=0.8,
                              pos=(Window.width * 0.2 + i * CARD_X_SIZE,
                                   Window.height*0.675 + j*CARD_X_SIZE),
                              size=(CARD_X_SIZE, CARD_Y_SIZE), size_hint=(None, None))
                btn2 = Button(text=str(i + (1-j)*8), disabled=False, opacity=0.8,
                              pos=(Window.width * 0.2 + i * CARD_X_SIZE,
                                   Window.height * 0.2 + j * CARD_X_SIZE),
                              size=(CARD_X_SIZE, CARD_Y_SIZE), size_hint=(None, None))
                self.card_position_coords_initial[i + (1-j)*8] = (btn1.x, btn1.y-(1-j)*5)
                self.card_position_coords_modified[i + (1-j)*8] = (btn2.x, btn2.y-(1-j)*5)
                # self.layout.add_widget(btn1)
                # self.layout.add_widget(btn2)
        root.add_widget(self.layout)

        self.ready_btn = Button(text="Готов",
                                pos=(Window.width * 0.88, Window.height * 0.18), background_color=(1, 0, 0, 1),
                                size=(Window.width * 0.1, Window.height * 0.04), size_hint=(None, None))
        # self.ready_btn.bind(on_press=)
        self.layout.add_widget(self.ready_btn)
        self.shuffle = Button(text="Сдать",
                                pos=(Window.width * 0.88, Window.height * 0.14), background_color=(1, 0, 0, 1),
                                size=(Window.width * 0.1, Window.height * 0.04), size_hint=(None, None))
        # self.shuffle.bind(on_press=)
        self.layout.add_widget(self.shuffle)

        self.display_cards()

        return root

filedir = 'cards/set_1'
modules = [f[:-3] for f in os.listdir(filedir) if
           os.path.isfile(os.path.join(filedir, f)) and f.endswith('.py') and f != '__init__.py']
imports = [f"from cards.set_1 import {module}\nfrom cards.set_1.{module} import *" for module in sorted(modules)]
for imp in imports:
    exec(imp)
WINDOW_SIZE = (960, 540) #(1920, 1080) #
STACK_DURATION = 5
TURN_DURATION = 5
game = Game()
cards1 = [Lovets_dush_1(), Cobold_1(), Draks_1(), Lovets_dush_1(), Voin_hrama_1(), Draks_1(),
          Lovets_dush_1(), PovelitelMolniy_1(), Draks_1(),Lovets_dush_1(), PovelitelMolniy_1(), Draks_1(),
          Lovets_dush_1(), PovelitelMolniy_1(), Draks_1()]
gui = berserk_gui.BerserkApp(game, WINDOW_SIZE, STACK_DURATION, TURN_DURATION)
game.gui = gui
f = FormationApp(game, WINDOW_SIZE, cards1, 1, 24, 22)
f.run()

