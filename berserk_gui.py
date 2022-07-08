import kivy

kivy.require('1.0.1')
from kivy import Config
from kivy.core.window import Window

Config.set('graphics', 'position', 'custom')
Config.set('graphics', 'left', 0)
Config.set('graphics', 'top', 0)
# Window.size = (1920, 1080)

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
import card as cd
from itertools import chain
import board

CARD_X_SIZE = (Window.width * 0.12)
CARD_Y_SIZE = (Window.height * 0.15)


class MainField(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    # Clock.schedule_interval(self.check, 1 / 5.0)

    def check(self, *args):
        print('txt')


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
            curr_widget.destroy_nav_buttons()

            for a, b in curr_widget.card_position_coords:
                if abs(x - a) < 0.001 and abs(y - b) < 0.001:
                    now = curr_widget.card_position_coords.index((a, b))  # Костыль
            curr_widget.backend.board.update_board(card=card_obj, prev=prev, now=now)
            card_obj.loc = now


class BerserkApp(App):

    def __init__(self, backend):
        super(BerserkApp, self).__init__()
        self.backend = backend

    def destroy_nav_buttons(self):
        for bt in self.nav_buttons:
            self.root.remove_widget(bt)
        self.nav_buttons = []

    def destroy_action_buttons(self):
        for bt in self.selected_card_buttons:
            self.root.remove_widget(bt)
        self.selected_card_buttons = []

    def destroy_target_buttons(self):
        for bt in self.target_marks_buttons:
            self.root.remove_widget(bt)
        self.target_marks_buttons = []

    def say_coords(self, instance):
        # DELETE LATER
        instance.background_color = (rng.random(), rng.random(), rng.random(), 1.0)

        # add dropdown
        btn = Button(text='Opa', size=(CARD_X_SIZE, CARD_Y_SIZE), size_hint=(None, None))
        self.dop_zone_1_buttons.append(btn)
        self.dop_zone_1.add_widget(btn)

    def on_mouse_pos(self, bttn, window, pos):
        """
        КРАСНЫЕ СТРЕЛОЧКИ!!!
        """
        for butt in chain(self.layout.my_buttons, self.dop_zone_1_buttons):  #
            if butt.collide_point(*pos):
                with self.root.canvas:
                    if self.red_arrows:
                        for arr in self.red_arrows:
                            self.root.canvas.remove(arr)
                            self.red_arrows.remove(arr)
                    Color(1., 0, 0)
                    red_arr = Line(points=[bttn.x + CARD_X_SIZE / 2, bttn.y + CARD_Y_SIZE / 2, butt.x + CARD_X_SIZE / 2,
                                           butt.y + CARD_Y_SIZE / 2],
                                   width=2)
                    self.red_arrows.append(red_arr)
            # root.add_widget(l)

    def delete_move_marks_on_unfocus(self, window, pos):
        delete_ = True
        for nav_b in self.nav_buttons:
            if abs(pos.x - nav_b.x) < CARD_X_SIZE / 2 and abs(pos.y - nav_b.y) < CARD_Y_SIZE / 2:
                delete_ = False
        if delete_:
            self.destroy_nav_buttons()
        #   self.destroy_target_buttons()

    def delete_action_buttons_on_unfocus(self, window, pos):
        # deletes buttons if you click on a middle part outside of a card
        if self.selected_card:
            delete_ = True
            for nav_b in self.selected_card_buttons:
                if (pos.x > Window.width * 0.75) or (pos.x < Window.width * 0.15):
                    delete_ = False
            if delete_:
                self.destroy_action_buttons()
                self.selected_card = None

    def on_click_on_card(self, card, instance):
        self.selected_card = instance
        # Display card action buttons
        self.display_card_actions(card)
        # Display navigation buttons
        moves = self.backend.board.get_available_moves(card)
        if self.nav_buttons:
            self.destroy_nav_buttons()
        for move in moves:
            mark = MoveMark()
            x, y = self.card_position_coords[move][0] + CARD_X_SIZE / 2, self.card_position_coords[move][
                1] + CARD_Y_SIZE / 2
            mark.x = x
            mark.y = y
            mark.bind(on_touch_down=partial(mark.move_card, instance, self, card))
            self.root.add_widget(mark)
            self.nav_buttons.append(mark)
        print(self.hp_label_dict[card].text)

    def display_available_targets(self, board, card, ability, instance):
        b_size = 10  # размер квадратика
        if ability == 'attack':
            range_of_action = 1
        else:
            range_of_action = ability.range
        targets = board.get_available_target_cards(board.game_board.index(card), range_=range_of_action)
        for t in targets:
            btn = Button(pos=(self.card_position_coords[t][0] + CARD_X_SIZE / 2 - b_size / 2,
                              self.card_position_coords[t][1] + CARD_Y_SIZE / 2 - b_size / 2),
                         background_color=(1, 0, 0),
                         size=(b_size, b_size), size_hint=(None, None), background_normal='')
            self.root.add_widget(btn)
            self.target_marks_buttons.append(btn)

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

    def create_board(self):
        state = self.backend.board.get_state()
        for i, cell in enumerate(state['game_board']):
            if cell != 0:
                print('LIfe: ', cell.life)
                x, y = self.card_position_coords[i]
                rl1 = RelativeLayout(pos=(x, y))
                btn1 = Button(text='', disabled=False, opacity=1.0, #pos=(x, y),
                              background_normal=cell.pic,
                              size=(CARD_X_SIZE, CARD_Y_SIZE), size_hint=(None, None))

                btn1.bind(on_press=partial(self.on_click_on_card, cell))
                rl1.add_widget(btn1)
                with rl1.canvas:
                    Color(0, 0.3, 0.1)
                    Rectangle(size=(CARD_X_SIZE*0.33, CARD_Y_SIZE*0.2), color=(0,0,0,0.3), pos_hint=(None, None))
                    Color(1, 1, 1)
                    Line(width=0.5, color=(1,1,1,0), rectangle=(0,0,CARD_X_SIZE*0.33,CARD_Y_SIZE*0.2))
                    lbl = Label(text='10/10', color=(1, 1, 1, 1), size=(CARD_X_SIZE * 0.3, CARD_Y_SIZE * 0.2),
                      pos_hint=(None, None), font_size='12')
                    self.hp_label_dict[cell] = lbl
                    self.layout.add_widget(rl1)

    def build(self):
        root = MainField()

        # generate board coords
        self.layout = FloatLayout(size=(Window.width * 0.8, Window.height))
        self.card_position_coords = []
        self.nav_buttons = []
        self.selected_card_buttons = []
        self.selected_card = None
        self.target_marks_buttons = []
        self.hp_label_dict = {}
        for i in range(5):
            for j in range(6):
                btn1 = Button(text=str(i * 6 + j), disabled=False, opacity=0.8,
                              pos=(Window.width * 0.15 + i * Window.width * 0.12,
                                   Window.height * 0.03 + j * Window.height * 0.15),
                              size=(Window.width * 0.12, Window.height * 0.15), size_hint=(None, None))
                self.card_position_coords.append((btn1.x, btn1.y))
                self.layout.add_widget(btn1)

        # when user clicked on square outside red move marks
        Window.bind(on_touch_down=self.delete_move_marks_on_unfocus)
        # when user clicked on square outside selected card
        Window.bind(on_touch_down=self.delete_action_buttons_on_unfocus)

        # self.layout.my_buttons[13].bind(on_press=self.say_coords)
        # Window.bind(mouse_pos=partial(self.on_mouse_pos, self.layout.my_buttons[13]))
        # for i, bttn in enumerate(self.layout.my_buttons):
        #     if i != 13:
        #         self.layout.remove_widget(bttn)
        root.add_widget(self.layout)
       # self.create_board()

        # Dropdowns
        self.dop_zone_1 = DropDown()
        self.dop_zone_1_buttons = []
        for k in range(1):
            btn = Button(text='k', size=(CARD_X_SIZE, CARD_Y_SIZE), size_hint=(None, None))
            # btn.bind(on_release=lambda btn: dropdown.select(btn.text))
            self.dop_zone_1.add_widget(btn)
            self.dop_zone_1_buttons.append(btn)
        # root.add_widget(dropdown)
        self.mainbutton = Button(text='Доп.Зона', size_hint=(None, None), size=(CARD_X_SIZE, Window.height * 0.05),
                                 pos=(Window.width * 0.82, Window.height * 0.9))

        self.red_arrows = []
        self.mainbutton.bind(on_release=self.dop_zone_1.open)
        # self.dop_zone_1.bind(on_select=lambda instance, x: setattr(mainbutton, 'text', x))
        root.add_widget(self.mainbutton)

        root.add_widget(Vertical())
        root.add_widget(Horizontal())

        # timeout otherwise some parts are not rendered
        Clock.schedule_once(lambda x: self.create_board(), 0.5)
        #   Window.bind(on_resize=self.check_resize)
        return root

