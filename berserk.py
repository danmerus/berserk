import kivy
kivy.require('2.0.1')

from kivy.uix.floatlayout import FloatLayout
from kivy.app import App
from kivy.properties import ObjectProperty, StringProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.button import Button
from kivy.uix.widget import Widget
from kivy.core.window import Window
import numpy.random as rng

class MainField(Widget):

    pass

class BerserkApp(App):


   # def check_resize(self, instance, x, y):
     #   Window.size = (Window.size[0],  Window.size[1])

    def say_coords(self, instance):
        instance.background_color = (rng.random(), rng.random(), rng.random(), 1.0)
        print('hi!\ncoords:', instance.x, instance.y)

    def build(self):
        root = MainField()

        layout = GridLayout(cols=5, rows=6, size=(Window.width*0.8, Window.height*0.8), size_hint_y=None)
        #layout.size_hint = (0.8, 0.8)
        layout.my_buttons = []
        for i in range(30):
            btn1 = Button(text=str(i))
            layout.my_buttons.append(btn1)
            layout.add_widget(btn1)
        layout.my_buttons[13].background_normal='data/123.png'
        layout.my_buttons[13].bind(on_press=self.say_coords)
        root.add_widget(layout)

        l1 = BoxLayout(orientation='vertical', pos=(Window.width*0.9, 0), size=(Window.width*0.1, Window.height))
        for i in range(8):
            btn2 = Button(text=str(i))
            l1.add_widget(btn2)
        root.add_widget(l1)

       # Window.bind(on_resize=self.check_resize)
        return root


if __name__ == '__main__':
    BerserkApp().run()