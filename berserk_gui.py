import kivy

kivy.require('1.0.1')
from kivy import Config
from kivy.core.window import Window

Config.set('graphics', 'position', 'custom')
Config.set('graphics', 'left', 0)
Config.set('graphics', 'top', 0)
#Window.size = (1920, 1080)

from kivy.uix.floatlayout import FloatLayout
from kivy.app import App
from kivy.properties import ObjectProperty, StringProperty, NumericProperty, BooleanProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.scrollview import ScrollView
from kivy.uix.dropdown import DropDown
from kivy.uix.button import Button
from kivy.uix.widget import Widget
from kivy.uix.label import Label
from kivy.graphics import Line, Color, InstructionGroup, Rectangle
import numpy.random as rng
from kivy.clock import Clock
from kivy.animation import Animation
from functools import partial
from itertools import chain
from kivy.uix.image import Image
from kivy.clock import mainthread
from kivy.graphics.vertex_instructions import Triangle
from cards.card_properties import ActionTypes, SimpleCardAction, CreatureType

CARD_X_SIZE = (Window.width * 0.12)
CARD_Y_SIZE = (Window.height * 0.15)


class MainField(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    # Clock.schedule_interval(self.check, 1 / 5.0)

class Vertical(Widget):
    pass


class Horizontal(Widget):
    pass


class MoveMark(ButtonBehavior, Label, Widget):
    x = NumericProperty(100)
    y = NumericProperty(100)
    z = NumericProperty(20)

    def move_card(self, card, curr_widget, card_obj, instance, touch):
        #  print('Instance ',instance.x, instance.y, 'Card X ', card.x, card.y)
        prev = card_obj.loc
        if instance.x + CARD_X_SIZE / 2 > touch.x > instance.x - CARD_X_SIZE / 2 and instance.y + CARD_Y_SIZE / 2 > touch.y > instance.y - CARD_Y_SIZE / 2:
            x = instance.x - CARD_X_SIZE / 2
            y = instance.y - CARD_Y_SIZE / 2
            anim = Animation(x=x, y=y, duration=0.5)
            anim.start(card.parent)
            curr_widget.destroy_x(curr_widget.nav_buttons)
            curr_widget.nav_buttons = []

            for a, b in curr_widget.card_position_coords:
                if abs(x - a) < 0.001 and abs(y - b) < 0.001:
                    now = curr_widget.card_position_coords.index((a, b))  # Костыль
            curr_widget.backend.board.update_board(card=card_obj, prev=prev, now=now)
            card_obj.loc = now


class BerserkApp(App):

    def __init__(self, backend):
        super(BerserkApp, self).__init__()
        self.backend = backend

    def destroy_x(self, list_, whatever=False):
        for bt in list_:
            self.root.remove_widget(bt)


    def delete_move_marks_on_unfocus(self, window, pos):
        delete_ = True
        for nav_b in self.nav_buttons:
            if abs(pos.x - nav_b.x) < CARD_X_SIZE / 2 and abs(pos.y - nav_b.y) < CARD_Y_SIZE / 2:
                delete_ = False
        if delete_:
            self.destroy_x(self.nav_buttons)
            self.nav_buttons = []

    def delete_target_marks_on_unfocus(self, window, pos):
        delete_ = True
        for nav_b in self.target_marks_buttons:
            if abs(pos.x - nav_b.children[0].x) < CARD_X_SIZE  and abs(pos.y - nav_b.children[0].y) < CARD_Y_SIZE:
                delete_ = False
        if delete_:
            self.destroy_x(self.target_marks_buttons)
            self.target_marks_buttons = []
            Clock.schedule_once(partial(self.destroy_x, self.die_pics), 1)
            self.die_pics = []

    def draw_selection_border(self, instance, card):
        if hasattr(self, "card_border"):
            self.card_border[1].canvas.remove(self.card_border[0])
        with instance.canvas:
            if card.player == 1:
                c = Color(1, 1, 0, 1)
            else:
                c = Color(0.2, 0.2, 0.8, 1)
            self.card_border = (Line(width=1, color=c, rectangle=(0, 0, CARD_X_SIZE * 1, CARD_Y_SIZE * 1)), instance)


    def on_click_on_card(self, card, instance):
        #print(instance.parent.pos)
        self.selected_card = instance
        self.destroy_x(self.selected_card_buttons)
        # Draw border
        self.draw_selection_border(instance.parent, card)
        # Display card action buttons
        self.display_card_actions(card)
        # Display navigation buttons
        moves = self.backend.board.get_available_moves(card)
        if self.nav_buttons:
            self.destroy_x(self.nav_buttons)
            self.nav_buttons = []
        for move in moves:
            mark = MoveMark()
            x, y = self.card_position_coords[move][0] + CARD_X_SIZE / 2, self.card_position_coords[move][1] + CARD_Y_SIZE / 2
            mark.x = x
            mark.y = y
            mark.bind(on_touch_down=partial(mark.move_card, instance, self, card))
            self.root.add_widget(mark)
            self.nav_buttons.append(mark)

    def destroy_card(self, card):
        self.layout.remove_widget(self.cards_dict[card])
        self.backend.board.remove_card(card)

    def draw_red_arrow(self, from_card, to_card, card, victim):

        with self.root.canvas:
            c = Color(1, 0, 0, 0.8)
            if card.type == CreatureType.FLYER or card.type == CreatureType.LAND:
                if card.player == 1:
                    x, y = self.dop_zone_1.to_parent(from_card.x, from_card.y)
                else:
                    x, y = self.dop_zone_2.to_parent(from_card.x, from_card.y)
            else:
                x, y = from_card.x, from_card.y
            if victim.type == CreatureType.FLYER or victim.type == CreatureType.LAND:
                if card.player == 1:
                    n, m = self.dop_zone_1.to_parent(to_card.x, to_card.y)
                else:
                    n, m = self.dop_zone_2.to_parent(to_card.x, to_card.y)
            else:
                n, m = to_card.x, to_card.y

            l = Line(width=3, color=c, points=(x+CARD_X_SIZE/2, y+CARD_Y_SIZE/2,
                                           n+CARD_X_SIZE/2, m+CARD_Y_SIZE/2))
            tri = Triangle(color=c, points=[(n-x)*0.3, (y-m)*0.3,
                                             n+CARD_X_SIZE/2, m+CARD_Y_SIZE/2,
                                             n+CARD_X_SIZE/2+30, m+CARD_Y_SIZE/2+30])
            self.red_arrows.append(l)
            self.red_arrows.append(tri)

    def draw_die(self, r1, r2):
        r1_i = Image(source=f'data/dice/Alea_{r1}.png', pos=(Window.width*0.78, Window.height*0.8), size=(0.07*Window.width, Window.height*0.07))
        r2_i = Image(source=f'data/dice/Alea_{r2}.png', pos=(Window.width*0.12, Window.height*0.8), size=(0.07*Window.width, Window.height*0.07))
        self.root.add_widget(r1_i)
        self.root.add_widget(r2_i)
        self.die_pics.append(r1_i)
        self.die_pics.append(r2_i)


    def perform_card_action(self, card, ability, victim, instance):
        if ability == 'attack':
            outcome_list, roll1, roll2 = self.backend.get_fight_result()
            if len(outcome_list) == 1:
                a, b = outcome_list[0]
                if a:
                    victim.curr_life -= card.attack[a-1]
                if b:
                    card.curr_life -= victim.attack[b-1]
            else: # TODO: add extra button
                a, b = outcome_list[0]
                if a:
                    victim.curr_life -= card.attack[a - 1]
                if b:
                    card.curr_life -= victim.attack[b - 1]

            print('roll1: ', roll1, 'roll2: ', roll2)
            self.draw_red_arrow(self.cards_dict[card], self.cards_dict[victim], card, victim)

            self.draw_die(roll1, roll2)
            self.hp_label_dict[victim].text = f'{victim.curr_life}/{victim.life}'
            self.hp_label_dict[card].text = f'{card.curr_life}/{card.life}'
            if card.curr_life <= 0:
                self.destroy_card(card)
            if victim.curr_life <= 0:
                self.destroy_card(victim)

        self.destroy_x(self.target_marks_buttons)
        self.target_marks_buttons = []


    def display_available_targets(self, board, card, ability, instance):
        b_size = 20  # размер квадратика
        if ability == 'attack':
            range_of_action = 1
        else:
            range_of_action = ability.range
        if card.type == CreatureType.CREATURE:
            targets = board.get_available_targets_ground(board.game_board.index(card), range_=range_of_action)  # targets are card objects
        elif card.type == CreatureType.FLYER:
            targets = board.get_available_targets_flyer(card)
        for t in targets:
            ly = RelativeLayout(pos=(0, 0))
            ix = t.loc
            btn = Button(pos=(self.card_position_coords[ix][0],
                              self.card_position_coords[ix][1]),
                         background_color=(1, 1, 1, 0.2),
                         size=(CARD_X_SIZE, CARD_Y_SIZE), size_hint=(None, None), background_normal='')
            with ly.canvas:
                Color(1, 0, 0, 1)
                rect1 = Rectangle(pos=(self.card_position_coords[ix][0] + CARD_X_SIZE / 2 - b_size / 2,
                              self.card_position_coords[ix][1] + CARD_Y_SIZE / 2 - b_size / 2),
                         background_color=(1, 0, 0),
                         size=(b_size, b_size), size_hint=(1, 1))
            btn.bind(on_press=partial(self.perform_card_action, card, ability, t))
            ly.add_widget(btn)
            self.root.add_widget(ly)
            self.target_marks_buttons.append(ly)

    def display_card_actions(self, card):
        # adding attack button
        btn1 = Button(text=f'Атака {card.attack[0]}-{card.attack[1]}-{card.attack[2]}',
                      pos=(Window.width * 0.79, Window.height * 0.20),
                      size=(Window.width * 0.17, Window.height * 0.05), size_hint=(None, None))
        btn1.bind(on_press=partial(self.display_available_targets, self.backend.board, card, 'attack'))
        self.root.add_widget(btn1)
        self.selected_card_buttons.append(btn1)
        # adding abilities buttons
        for i, ability in enumerate(card.abilities):
            btn = Button(text=ability.txt,
                          pos=(Window.width * 0.79, Window.height * 0.20 - (i + 1) * 0.05 * Window.height),
                          size=(Window.width * 0.17, Window.height * 0.05), size_hint=(None, None))
            btn.bind(on_press=partial(self.display_available_targets, self.backend.board, card, ability))
            self.root.add_widget(btn)
            self.selected_card_buttons.append(btn)


    def update_pos(self, instance, value):
        pass

    def reveal_cards(self, cards):
        for card in cards:
            loc = card.loc
            if card.type == CreatureType.FLYER:
                print('flyer!')
                x, y = self.dz1_btn.pos
                rl1 = RelativeLayout(size_hint=(None, None))#, size=(CARD_X_SIZE, CARD_Y_SIZE))
                btn1 = Button(text='', disabled=False,
                              background_normal=card.pic,
                              size=(CARD_X_SIZE, CARD_Y_SIZE), size_hint=(None, None))
                self.backend.board.game_board[card.loc] = 0
                card.loc = -1
                if card.player == 1:
                    self.dop_zone_1_gl.add_widget(rl1)
                    self.dop_zone_1_buttons.append(rl1)
                else:
                    self.dop_zone_2_gl.add_widget(rl1)
                    self.dop_zone_2_buttons.append(rl1)
            else:
                x, y = self.card_position_coords[loc]
                rl1 = RelativeLayout(pos=(x, y))
                btn1 = Button(text='', disabled=False, opacity=1.0, #pos=(x, y),
                          background_normal=card.pic,
                          size=(CARD_X_SIZE, CARD_Y_SIZE), size_hint=(None, None))
                btn1.bind(pos= lambda x1: x1.pos)

            btn1.bind(on_press=partial(self.on_click_on_card, card))
            rl1.add_widget(btn1)
            with rl1.canvas:
                Color(0, 0.3, 0.1)
                Rectangle(pos=(0, CARD_Y_SIZE*0.8), size=(CARD_X_SIZE*0.33, CARD_Y_SIZE*0.2), color=(1,1,1,0.3), pos_hint=(None, None))
                Color(1, 1, 1)
                Line(width=0.5, color=(1,1,1,0), rectangle=(0,CARD_Y_SIZE*0.8,CARD_X_SIZE*0.33, CARD_Y_SIZE*0.2))
                lbl = Label(pos=(0, CARD_Y_SIZE*0.8), text=f'{card.life}/{card.life}', color=(1, 1, 1, 1), size=(CARD_X_SIZE * 0.3, CARD_Y_SIZE * 0.2),
                  pos_hint=(None, None), font_size='12')
                self.hp_label_dict[card] = lbl
                self.cards_dict[card] = rl1
                if card.type == CreatureType.CREATURE:
                    self.layout.add_widget(rl1)

    def hide_scroll(self, sv, instance):
        if not sv.disabled:
            sv.disabled = True
            sv.opacity = 0
        else:
            sv.disabled = False
            sv.opacity = 1

    def check_children(self):
        for el in self.layout.children:
            print(el)
            if len(el.children) > 0:
                print(el.children[0].pos)

    def build(self):
        root = MainField()
        root.add_widget(Vertical())
        root.add_widget(Horizontal())
        # generate board coords
        self.layout = FloatLayout(size=(Window.width * 0.8, Window.height))
        self.card_position_coords = []
        self.nav_buttons = []
        self.selected_card_buttons = []
        self.selected_card = None
        self.target_marks_buttons = []
        self.hp_label_dict = {}
        self.cards_dict = {}
        self.die_pics = []
        self.red_arrows = []
        for i in range(5):
            for j in range(6):
                btn1 = Button(text=str(i * 6 + j), disabled=False, opacity=0.8,
                              pos=(Window.width * 0.18 + i * CARD_X_SIZE,
                                   Window.height * 0.03 + j * CARD_Y_SIZE),
                              size=(CARD_X_SIZE, CARD_Y_SIZE), size_hint=(None, None))
                self.card_position_coords.append((btn1.x, btn1.y))
                self.layout.add_widget(btn1)

        # when user clicked on square outside red move marks
        Window.bind(on_touch_down=self.delete_move_marks_on_unfocus)
        # when user clicked on square outside selected card
      #  Window.bind(on_touch_down=self.delete_action_buttons_on_unfocus)
        # when user clicked on square outside target card
        Window.bind(on_touch_down=self.delete_target_marks_on_unfocus)

        root.add_widget(self.layout)

        # Dropdowns
        self.dop_zone_1 = ScrollView(bar_pos_x='top', always_overscroll=False, do_scroll_x=False,
                                     size=(CARD_X_SIZE, Window.height/2), size_hint=(None, None), pos=(Window.width * 0.84, Window.height * 0.39))
        self.dop_zone_1_gl = GridLayout(cols=1, size_hint=(None, None))
        self.dop_zone_1_gl.bind(minimum_height=self.dop_zone_1_gl.setter('height'))
        self.dop_zone_2 = ScrollView(bar_pos_x='top', always_overscroll=False, do_scroll_x=False,
                                     size=(CARD_X_SIZE, Window.height/2), size_hint=(None, None), pos=(Window.width * 0.01, Window.height * 0.39))
        self.dop_zone_2_gl = GridLayout(cols=1, size_hint=(None, None))
        self.dop_zone_2_gl.bind(minimum_height=self.dop_zone_2_gl.setter('height'))
        self.dop_zone_1.add_widget(self.dop_zone_1_gl)
        self.dop_zone_2.add_widget(self.dop_zone_2_gl)
        self.dop_zone_1_buttons = []
        self.dop_zone_2_buttons = []
        self.dz1_btn = Button(text='Доп.Зона', size_hint=(None, None), size=(Window.width*0.15, Window.height * 0.05),
                                 pos=(Window.width * 0.84, Window.height * 0.88))
        self.dz2_btn = Button(text='Доп.Зона', size_hint=(None, None), size=(Window.width * 0.15, Window.height * 0.05),
                              pos=(Window.width * 0.01, Window.height * 0.88))
        self.dz1_btn.bind(on_press=partial(self.hide_scroll, self.dop_zone_1))
        self.dz2_btn.bind(on_press=partial(self.hide_scroll, self.dop_zone_2))

        root.add_widget(self.dop_zone_1)
        root.add_widget(self.dop_zone_2)
        root.add_widget(self.dz1_btn)
        root.add_widget(self.dz2_btn)

        # timeout otherwise some parts are not rendered
        Clock.schedule_once(lambda x: self.reveal_cards(self.backend.input_cards1), 0.5)
        Clock.schedule_once(lambda x: self.reveal_cards(self.backend.input_cards2), 0.5)
        #   Window.bind(on_resize=self.check_resize)
        #Clock.schedule_once(lambda x: self.check_children(), 1)
        return root

