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

class SelectionApp(App):

    def __init__(self, backend, window_size, hand, turn):
        super(SelectionApp, self).__init__()
        Window.size = window_size
        if window_size == (1920, 1080):
            Window.maximize()
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
            btn1 = Button(disabled=False, pos=(0, CARD_Y_SIZE * 0.2),  border=(0,0,0,0),
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
                    card.loc = self.convert_coord(v)
                out.append(card)
            if self.turn == 1:
                self.backend.cards_on_board1 = out
            elif self.turn == 2:
                self.backend.cards_on_board2 = out
            self.stop()

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
                # self.layout.add_widget(btn1)

        self.ready_btn = Button(text="Готов",
                                pos=(Window.width * 0.83, Window.height * 0.18), background_color=(1, 0, 0, 1),
                                size=(Window.width * 0.08, Window.height * 0.05), size_hint=(None, None))
        self.ready_btn.bind(on_press=self.lock_and_loaded)
        self.layout.add_widget(self.ready_btn)

        if self.turn == 1 and len(self.hand) <= 9:
            self.spots_for_placement = [6, 7, 8, 12, 13, 14, 18, 19, 20]
        elif self.turn == 1 and 9 < len(self.hand) <= 13:
            self.spots_for_placement = [6, 7, 8, 12, 13, 14, 18, 19, 20, 0, 1, 24, 25]
        elif self.turn == 2 and len(self.hand) <= 11:
            self.spots_for_placement = [6, 7, 8, 12, 13, 14, 18, 19, 20, 2, 26]
        else:
            self.spots_for_placement = [6, 7, 8, 12, 13, 14, 18, 19, 20, 0, 1, 24, 25, 2, 26]
        self.display_marks(self.spots_for_placement)
        root.add_widget(self.layout)
        self.display_draggable_cards()
        return root
