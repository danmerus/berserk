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
from kivy_garden.draggable import KXDraggableBehavior, KXDroppableBehavior
from game import Game
import berserk_gui
from game_properties import GameStates
from cards.card import *
import placement
import os



class MainField(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

class DraggableRL(KXDraggableBehavior, KXDroppableBehavior, RelativeLayout):
    def __init__(self, parent_, **kwargs):
        super(DraggableRL, self).__init__(**kwargs)
        self.drag_timeout = 1
        self.drag_distance = 10
        self.parent_ = parent_

    def on_drag_end(self, touch):
        for i, el in enumerate(self.parent_.card_position_coords):
            if abs(touch.pos[0]-el[0]-CARD_X_SIZE / 2 ) < CARD_X_SIZE/2 and abs(touch.pos[1]-el[1]-CARD_X_SIZE / 2 ) < CARD_X_SIZE/2:
                if i in self.parent_.spots_for_placement and i not in self.parent_.occupied.values():
                    self.pos = el
                    self.parent_.occupied[self] = i
                    self.parent_.layout.remove_widget(self.parent_.red_dots[i])
                    self.parent_.display_marks([x for x in self.parent_.spots_for_placement if x not in self.parent_.occupied.values()])
                    return
        self.pos = self.parent_.initial_loc_dict[self]
        self.parent_.occupied[self] = -1
        self.parent_.display_marks(
            [x for x in self.parent_.spots_for_placement if x not in self.parent_.occupied.values()])

    def on_touch_down(self, touch):
        return super(DraggableRL, self).on_touch_down(touch)

class FormationApp(App):

    def __init__(self, backend, window_size, hand, turn):
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
            name = (card.name[:12] + '..') if len(card.name) > 12 else card.name
            lbl_ = Label(pos=(0, 0), text=f'{name}', color=c1,
                         size=size_,
                         font_size=Window.height * 0.02,)
            self.card_nameplates.append(lbl_)
            if card.cost[0] == 0:
                Color(0.8, 0.8, 0.8)
                cost = card.cost[1]
            else:
                Color(1, 1, 0)
                cost = card.cost[0]
            Rectangle(pos=(0, 0.18*CARD_Y_SIZE), size=(CARD_X_SIZE * 0.27, CARD_Y_SIZE * 0.15),
                      color=(1, 1, 1, 0.3), pos_hint=(None, None))
            Color(1, 1, 1)
            Line(width=0.5, color=(1, 1, 1, 0),
                 rectangle=(CARD_X_SIZE * 0.74, CARD_Y_SIZE * 0.85, CARD_X_SIZE * 0.25, CARD_Y_SIZE * 0.15))
            lbl = Label(pos=(0, 0.18*CARD_Y_SIZE), text=f'{cost}',
                        color=(1, 1, 1, 1),
                        size=(CARD_X_SIZE * 0.3, CARD_Y_SIZE * 0.15),
                        pos_hint=(None, None), font_size=Window.height * 0.02)
            self.card_nameplates.append(lbl_)
            lyy.add_widget(ly)

    def display_cards(self):
        for card in self.hand:
            loc = self.card_position_coords_initial.pop()
            x, y =  loc #self.card_position_coords[loc]
            rl1 = RelativeLayout(pos=(x, y), size=(CARD_X_SIZE, CARD_X_SIZE), size_hint=(None, None))
            btn1 = Button(disabled=False, pos=(0, CARD_Y_SIZE * 0.18),
                          background_normal=card.pic, size=(CARD_X_SIZE, CARD_Y_SIZE * 0.85), size_hint=(None, None), border=(0,0,0,0))
            rl1.add_widget(btn1)
            self.base_overlays[card] = RelativeLayout()
            rl1.add_widget(self.base_overlays[card])
            self.draw_card_overlay(card)
            self.layout.add_widget(rl1)
            self.card_dict[card] = rl1



    def build(self):
        root = MainField()
        self.card_position_coords_initial = []
        self.card_position_coords_modified = []
        self.layout = FloatLayout(size=(Window.width * 0.8, Window.height))
        self.base_overlays = {}
        self.card_dict = {}
        self.card_nameplates = []


        with root.canvas:
            root.bg_rect = Rectangle(source='data/bg/dark_bg_7.jpg', pos=root.pos, size=Window.size)
            points_x = [(Window.width * 0.2 + i * CARD_X_SIZE, Window.height*0.675,
                       Window.width * 0.2 + i * CARD_X_SIZE, Window.height*0.924) for i in range(9)]
            points_y = [(Window.width*0.2,  Window.height*0.55 + i*CARD_X_SIZE,
                         Window.width*0.76,  Window.height*0.55 + i*CARD_X_SIZE) for i in range(1, 4)]
            for i in range(3):
                c = Color(1, 1, 1, 0.7)
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
                self.card_position_coords_initial.append((btn1.x, btn1.y))
                self.layout.add_widget(btn1)
                self.layout.add_widget(btn2)
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
f = FormationApp(game, WINDOW_SIZE, cards1, 1)
f.run()

