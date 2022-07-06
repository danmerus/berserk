import kivy
kivy.require('1.0.1')
from kivy import Config
from kivy.core.window import Window
Config.set('graphics', 'position', 'custom')
Config.set('graphics', 'left', 0)
Config.set('graphics', 'top',  0)
#Window.size = (1920, 1080)

from kivy.uix.floatlayout import FloatLayout
from kivy.app import App
from kivy.properties import ObjectProperty, StringProperty, NumericProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.button import Button
from kivy.uix.widget import Widget
from kivy.uix.label import Label
from kivy.graphics import Line, Color, InstructionGroup, Rectangle
import numpy.random as rng
from kivy.clock import Clock
from kivy.animation import Animation
from functools import partial
import card as cd
import board


CARD_X_SIZE = (Window.width * 0.12)
CARD_Y_SIZE = (Window.height * 0.15)
class MainField(Widget):
    def draw_board(self):
        Color(1., 0, 0)
        l1 = Line(points=[100, 100, 200, 100, 100, 200], width=10)

class Vertical(Widget):
    pass
class Horizontal(Widget):
    pass
class MoveMark(ButtonBehavior, Label, Widget):

    x = NumericProperty(100)
    y = NumericProperty(100)
    z = NumericProperty(20)

    def move_card(self, card, curr_widget, instance, touch):
      #  print('Instance ',instance.x, instance.y, 'Card X ', card.x, card.y)
        if instance.x + 50 > touch.x > instance.x - 50 and instance.y + 50 > touch.y > instance.y - 50:
            anim = Animation(x=instance.x - CARD_X_SIZE/2, y=instance.y - CARD_Y_SIZE/2, duration=0.5)
            anim.start(card)
            curr_widget.destroy_nav_buttons()
class BerserkApp(App):

    def __int__(self, **kwargs):
        super(BerserkApp, self).__init__(**kwargs)
        self.title = 'Test'
        #self.card_x_size = Window.width*0.13
        Clock.schedule_once(lambda dt: print('hi!'))

    def update_board(self):
        for i, cell in enumerate(b.game_board):
            if cell != 0:
                self.layout.my_buttons

    def destroy_nav_buttons(self):
        for bt in self.nav_buttons:
            self.root.remove_widget(bt)

    def say_coords(self, instance):
        instance.background_color = (rng.random(), rng.random(), rng.random(), 1.0)
        print('hi!\ncoords:', instance.x, instance.y)

        # marks
        offset_x =(self.layout.my_buttons[0].x-self.layout.my_buttons[6].x)/2
        offset_y = (self.layout.my_buttons[1].y - self.layout.my_buttons[0].y) / 2
        moves = self.show_possible_moves()
        self.nav_buttons = []
        for move in moves:
            mark = MoveMark()
            x, y = self.layout.my_buttons[move].x-offset_x, self.layout.my_buttons[move].y-offset_y
            mark.x = x
            mark.y = y
            mark.bind(on_touch_down=partial(mark.move_card, instance, self))
            self.root.add_widget(mark)
            self.nav_buttons.append(mark)


        # animated move to mark


    def show_possible_moves(self):
        pos = b.get_available_moves('card')
        return pos


    def build(self):
        root = MainField() #size=(1800,800))

        self.layout = FloatLayout(size=(Window.width*0.8, Window.height))
        self.layout.my_buttons = []
        for i in range(5):
            for j in range(6):
                btn1 = Button(text=str(i*6+j), disabled=False, opacity=0.8, pos=(Window.width*0.15 + i*Window.width*0.12,
                        Window.height*0.03 + j*Window.height*0.15), size=(Window.width*0.12, Window.height*0.15), size_hint=(None, None))
                self.layout.my_buttons.append(btn1)
                self.layout.add_widget(btn1)
        self.layout.my_buttons[13].disabled = False
        self.layout.my_buttons[13].background_normal = 'data/123.png'
        self.layout.my_buttons[13].bind(on_press=self.say_coords)

        for i, bttn in enumerate(self.layout.my_buttons):
            if i != 13:
                self.layout.remove_widget(bttn)

        root.add_widget(self.layout)


        l1 = BoxLayout(orientation='vertical', pos=(Window.width*0.9, 0), size=(Window.width*0.1, Window.height))
        for i in range(8):
            btn2 = Button(text=str(i))
            l1.add_widget(btn2)
        root.add_widget(l1)

        root.add_widget(Vertical())
        root.add_widget(Horizontal())

        #print(b.game_board)
    #   Window.bind(on_resize=self.check_resize)
        return root



if __name__ == '__main__':
    b = board.Board()
    BerserkApp().run()
