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
import deck_selection
import berserk_gui
from game import Game

class MainField(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

class DraggableRL(KXDraggableBehavior, KXDroppableBehavior, RelativeLayout):
    def __init__(self, parent_, **kwargs):
        super(DraggableRL, self).__init__(**kwargs)
        self.drag_timeout = 1
        self.drag_distance = 10
        self.parent_ = parent_

    def get_right_spots(self):
        len_occupied = len([x for x in self.parent_.occupied.values() if x != -1])
        spots = []
        if (self.parent_.turn == 1 and len_occupied < 9) or (self.parent_.turn == 2 and len_occupied < 11):
            spots = self.parent_.spots_for_placement
        elif self.parent_.turn == 1 and 9 <= len_occupied < 13:
            spots = self.parent_.spots_for_placement1
        elif self.parent_.turn == 2 and len_occupied >= 11:
            spots = self.parent_.spots_for_placement1
        else:
            spots = self.parent_.spots_for_placement2
        return spots

    def extra_check(self, i, spots, obj_):
        prev = self.parent_.occupied[obj_]
        if self.parent_.turn == 2:
            new_places = set(self.parent_.spots_for_placement1)-set(self.parent_.spots_for_placement)
            if spots == self.parent_.spots_for_placement1 and i in new_places and prev in self.parent_.spots_for_placement:
                return False
        elif self.parent_.turn == 1:
            new_places1 = set(self.parent_.spots_for_placement1) - set(self.parent_.spots_for_placement)
            if spots == self.parent_.spots_for_placement1 and i in new_places1 and prev in self.parent_.spots_for_placement:
                return False
            new_places2 = set(self.parent_.spots_for_placement2) - set(self.parent_.spots_for_placement1)
            if spots == self.parent_.spots_for_placement2 and i in new_places2 and \
                (prev in self.parent_.spots_for_placement1 or prev in self.parent_.spots_for_placement):
                return False
        return True

    def extra_check1(self, spots, obj_):
        len_occupied = len([x for x in self.parent_.occupied.values() if x != -1])
        prev = self.parent_.occupied[obj_]
        if self.parent_.turn == 2:
            if prev in self.parent_.spots_for_placement and spots == self.parent_.spots_for_placement1 \
                    and len_occupied > len(self.parent_.spots_for_placement):
                return False
        elif self.parent_.turn == 1:
            if prev in self.parent_.spots_for_placement and spots == self.parent_.spots_for_placement1 \
                    and len_occupied > len(self.parent_.spots_for_placement):
                return False
            elif (prev in self.parent_.spots_for_placement or prev in self.parent_.spots_for_placement1) and spots == self.parent_.spots_for_placement2 \
                    and len_occupied > len(self.parent_.spots_for_placement1):
                return False
        return True


    def on_drag_end(self, touch):
        spots = self.get_right_spots()
        for i, el in enumerate(self.parent_.card_position_coords):
            if abs(touch.pos[0]-el[0]-CARD_X_SIZE / 2 ) < CARD_X_SIZE/2 and abs(touch.pos[1]-el[1]-CARD_X_SIZE / 2 ) < CARD_X_SIZE/2:
                if i in spots and i not in self.parent_.occupied.values():
                    if not self.extra_check(i, spots, self):
                        return
                    else:
                        self.pos = el
                        self.parent_.occupied[self] = i
                        self.parent_.layout.remove_widget(self.parent_.red_dots[i])
                        spots = self.get_right_spots()
                        self.parent_.display_marks([x for x in spots if x not in self.parent_.occupied.values()])
                        return
        if not self.extra_check1(spots, self):
            return
        self.pos = self.parent_.initial_loc_dict[self]
        self.parent_.occupied[self] = -1
        spots = self.get_right_spots()
        self.parent_.display_marks(
            [x for x in spots if x not in self.parent_.occupied.values()])

    def on_touch_down(self, touch):
        return super(DraggableRL, self).on_touch_down(touch)

class SelectionApp(App):

    def __init__(self, backend, window_size, hand, turn, mode, server_ip=None, server_port=None, **kwargs):
        super(SelectionApp, self).__init__(**kwargs)
        self.window_size = window_size
        Window.size = self.window_size
        # if window_size == (1920, 1080):
        #     Window.maximize()
        global CARD_X_SIZE, CARD_Y_SIZE, STACK_DURATION, TURN_DURATION, DZ_SIZE
        CARD_X_SIZE = (Window.width * 0.084375)
        CARD_Y_SIZE = CARD_X_SIZE  # (Window.height * 0.15)
        STACK_DURATION = 5
        TURN_DURATION = 6
        DZ_SIZE = (CARD_X_SIZE, Window.height * 0.45)

        self.backend = backend
        self.hand = hand
        self.turn = turn
        self.title = 'Berserk Renewal'
        self.mode = mode
        self.server_ip = server_ip
        self.server_port = server_port

    def open_settings(self, *largs):
        pass

    def display_marks(self, where_):
        for el in self.red_dots.values():
            self.layout.remove_widget(el)
        for ix in where_:
            rl = RelativeLayout(pos=(self.card_position_coords[ix]), size=(0,0))
            with rl.canvas:
                Color(1, 0, 0, 1)
                el = Ellipse(pos=(CARD_X_SIZE / 2 - 10, CARD_Y_SIZE / 2 - 10), size=(20, 20))
            self.layout.add_widget(rl)
            self.red_dots[ix] = rl

    def draw_card_overlay(self, card):
        size_ = (CARD_X_SIZE-2, CARD_Y_SIZE * 0.2)
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
                         font_size=Window.height * 0.02, )
            self.card_nameplates.append(lbl_)
            lyy.add_widget(ly)


    def display_draggable_cards(self):
        for card in self.hand:
            loc = self.empty_spots.pop()
            x, y = self.card_position_coords[loc]
            rl1 = DraggableRL(pos=(x, y), parent_=self, size=(CARD_X_SIZE, CARD_X_SIZE), size_hint=(None, None))
            btn1 = Button(disabled=False, pos=(0, CARD_Y_SIZE * 0.2),  border=(0,0,0,0),  background_down=card.pic,
                          background_normal=card.pic, size=(CARD_X_SIZE, CARD_Y_SIZE * 0.8), size_hint=(None, None))
            rl1.add_widget(btn1)
            self.base_overlays[card] = RelativeLayout()
            rl1.add_widget(self.base_overlays[card])
            self.draw_card_overlay(card)
            self.layout.add_widget(rl1)
            self.card_dict[card] = rl1
            self.occupied[rl1] = -1
            self.card_dict_reversed[rl1] = card
            self.initial_loc_dict[rl1] = (x, y)

    def convert_coord(self, coord):
        return 29 - coord

    def lock_and_loaded(self, *args):
        if -1 not in self.occupied.values():
            out = []
            for k, v in self.occupied.items():
                card = self.card_dict_reversed[k]
                card.player = self.turn
                if self.turn == 1:
                    card.loc = v
                else:
                    # if self.convert_coord(v) in [5, 11, 17, 23, 29]:
                    #     card.hidden = True
                    card.loc = self.convert_coord(v)
                out.append(card)
            if self.turn == 1:
                self.backend.cards_on_board1 = out
            elif self.turn == 2:
                self.backend.cards_on_board2 = out
            self.stop()
            if self.mode == 'single1':
                self.stop()
                d = deck_selection.DeckSelectionApp(self.window_size, mode='single2', backend=self.backend)
                d.run()
            elif self.mode == 'single2':
                self.stop()
                self.backend.set_cards(self.backend.cards_on_board1, self.backend.cards_on_board2, self.backend.gui)
                self.backend.gui.run()

    def build(self):
        root = MainField()
        self.layout = FloatLayout(size=(Window.width * 0.8, Window.height))
        self.card_position_coords = []
        self.spots_for_placement = []
        self.card_nameplates = []
        self.base_overlays = {}
        self.card_dict = {}
        self.card_dict_reversed = {}
        self.initial_loc_dict = {}
        self.occupied = {}
        self.red_dots = {}
        self.empty_spots = list(reversed([5 + 6*i for i in range(5)]+[4 + 6*i for i in range(5)]+[3 + 6*i for i in range(5)]))
        with root.canvas:
            root.bg_rect = Rectangle(source='data/bg/dark_bg_7.jpg', pos=root.pos, size=Window.size)
            points_x = [(Window.width * 0.25 + i * CARD_X_SIZE, Window.height*0.03+6*CARD_X_SIZE,
                       Window.width * 0.25 + i * CARD_X_SIZE, Window.height * 0.03) for i in range(6)]
            points_y = [(Window.width*0.25,  Window.height*0.03 + i*CARD_X_SIZE,
                         Window.width*0.672,  Window.height*0.03 + i*CARD_X_SIZE) for i in range(7)]
            for i in range(6):
                c = Color(1, 1, 1, 0.7)
                Line(color=c, points=points_x[i])
                Line(color=c, points=points_y[i])
            Line(color=c, points=points_y[6])
        for i in range(5):
            for j in range(6):
                btn1 = Button(text=str(i * 6 + j), disabled=False, opacity=0.8,
                              pos=(Window.width * 0.25 + i * CARD_X_SIZE,
                                   Window.height * 0.03 + j * CARD_Y_SIZE),
                              size=(CARD_X_SIZE, CARD_Y_SIZE), size_hint=(None, None))
                self.card_position_coords.append((btn1.x, btn1.y))
                #self.layout.add_widget(btn1)

        self.ready_btn = Button(text="Готов",
                                pos=(Window.width * 0.83, Window.height * 0.18), background_color=(1, 0, 0, 1),
                                size=(Window.width * 0.08, Window.height * 0.05), size_hint=(None, None))
        self.ready_btn.bind(on_press=self.lock_and_loaded)
        self.layout.add_widget(self.ready_btn)

        if self.turn == 1:
            self.spots_for_placement = [6, 7, 8, 12, 13, 14, 18, 19, 20]
            self.spots_for_placement1 = [6, 7, 8, 12, 13, 14, 18, 19, 20, 0, 1, 24, 25]
            self.spots_for_placement2 = [6, 7, 8, 12, 13, 14, 18, 19, 20, 0, 1, 24, 25, 2, 26]
        elif self.turn == 2:
            self.spots_for_placement = [6, 7, 8, 12, 13, 14, 18, 19, 20, 2, 26]
            self.spots_for_placement1 = [6, 7, 8, 12, 13, 14, 18, 19, 20, 0, 1, 24, 25, 2, 26]
        self.display_marks(self.spots_for_placement)
        root.add_widget(self.layout)
        self.display_draggable_cards()
        return root

# import os
# filedir = 'cards/set_1'
# modules = [f[:-3] for f in os.listdir(filedir) if
#            os.path.isfile(os.path.join(filedir, f)) and f.endswith('.py') and f != '__init__.py']
# imports = [f"from cards.set_1 import {module}\nfrom cards.set_1.{module} import *" for module in sorted(modules)]
# for imp in imports:
#     exec(imp)
#
# WINDOW_SIZE = (960, 540)  # (1920, 1080) #
# STACK_DURATION = 5
# TURN_DURATION = 5
# game = Game()
# gui = berserk_gui.BerserkApp(game, WINDOW_SIZE, STACK_DURATION, TURN_DURATION)
# game.gui = gui
# cards1 = [
#           Lovets_dush_1(), Cobold_1(), Draks_1(), Lovets_dush_1(), Voin_hrama_1(), Draks_1(),
#           Lovets_dush_1(), PovelitelMolniy_1(), Draks_1(),Lovets_dush_1(), PovelitelMolniy_1(), Draks_1(),
#           Lovets_dush_1(), PovelitelMolniy_1(),
#           #Draks_1()
#           ]
# game = Game()
# gui = berserk_gui.BerserkApp(game, (960, 540), 123, 123)
# game.gui = gui
# s = SelectionApp(game, (960, 540), cards1, 2, 'single1')
# s.run()