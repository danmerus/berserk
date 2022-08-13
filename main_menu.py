import kivy
kivy.require('2.0.1')
from kivy import Config
Config.set('input', 'mouse', 'mouse,multitouch_on_demand')
Config.set('graphics', 'resizable', '0')
Config.set('graphics', 'maxfps', '144')
# Config.set('kivy', 'exit_on_escape', '0')
from kivy.core.window import Window
from kivy.uix.floatlayout import FloatLayout
from kivy.app import App
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.button import Button
from kivy.uix.widget import Widget
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.graphics import Line, Color, Rectangle, Ellipse
from kivy.utils import get_color_from_hex
from kivy.clock import Clock
from kivy.uix.dropdown import DropDown
from game import Game
import berserk_gui
from kivy.lang import Builder
from game_properties import GameStates
from cards.card import *
import placement
import os
import copy
from functools import partial

SUPPORTED_RESOLUTIONS = [(1920, 1080), (1536, 864), (1440, 900), (1366, 768), (960, 540)]

class MainField(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

class MainMenuApp(App):

    def __init__(self, backend, window_size):
        super(MainMenuApp, self).__init__()
        Window.size = window_size
        if window_size == (1920, 1080):
            Window.maximize()
        global CARD_X_SIZE, CARD_Y_SIZE, STACK_DURATION, TURN_DURATION, DZ_SIZE
        CARD_X_SIZE = (Window.width * 0.07)
        CARD_Y_SIZE = CARD_X_SIZE  # (Window.height * 0.15)
        self.backend = backend
        self.title = 'Berserk Renewal'
        self.window_size = window_size

    def darker_col_on_touch_down(self, instance, *args):
        instance.color = get_color_from_hex('#FF9933')
        Clock.schedule_once(partial(self.default_col_on_release, instance), 1)

    def default_col_on_release(self, instance, *args):
        instance.color = self.c1

    def new_single_game_bind(self, *args):
        print('pressed!')

    def new_net_game_bind(self, *args):
        print('net')

    def settings_bind(self, *args):
        popup = Popup(title='Berserk renewal',
                       width=Window.width/2, height=Window.height/2, background_color=(1, 0, 0, 1),
                       overlay_color=(0, 0, 0, 0), size_hint=(None, None),
                       auto_dismiss=False)
        dropdown = DropDown(pos=(Window.width/2,Window.width/4))
        for index in range(len(SUPPORTED_RESOLUTIONS)):
            btn = Button(text=f'{SUPPORTED_RESOLUTIONS[index]}', background_color=(1, 0, 0, 1),
                         size_hint_y=None, height=Window.height/20, font_name='Roboto-Regular.ttf')
            btn.bind(on_release=partial(self.set_future_res, (SUPPORTED_RESOLUTIONS[index])))
            btn.bind(on_release=lambda btn: dropdown.select(btn.text))
            dropdown.add_widget(btn)

        mainbutton = Button(text='Выберите разрешение', background_color=(1, 0, 0, 1),
                            pos_hint={'top': 0.7, 'right': 0.35}, size_hint=(1/3, 1/10), font_name='Roboto-Regular.ttf')
        mainbutton.bind(on_release=dropdown.open)
        rl = RelativeLayout(size=popup.size, size_hint=(None, None))
        rl.add_widget(mainbutton)
        okbutton = Button(text='Сохранить', pos_hint={'top': 0.2, 'right': 0.8}, size_hint=(1 / 3, 1 / 5),
                        background_color = (1, 0, 0, 1), font_name='Roboto-Regular.ttf')
        okbutton.bind(on_press=self.resize_)
        rl.add_widget(okbutton)
        popup.content = rl
        popup.open()

    def set_future_res(self, res, *args):
        self.future_res = res

    def resize_(self, *args):
        x, y = self.future_res[0], self.future_res[1]
        self.stop()
        Window.size = (x, y)
        #Window.maximize()
        Window.left = 0
        Window.top = 0
        # Window.borderless = True
        # Window.restore()
        self.run()

    def deck_bind(self, *args):
        print('deck')


    def build(self):
        root = MainField()
        self.all_buttons = []
        self.layout = FloatLayout(size=(Window.width, Window.height))
        self.future_res = self.window_size

        with root.canvas:
            root.bg_rect = Rectangle(source='data/bg/dark_bg_7.jpg', pos=root.pos, size=Window.size)
        self.c1 = get_color_from_hex('#FCD618')
        kv = '''
<Label>
    font_name: 'data/fonts/RuslanDisplay-Regular.ttf'
'''
        Builder.load_string(kv)

        # Buttons:
        self.new_net_game_btn = Button(pos=(Window.width * 0.37, Window.height * 0.78), text='Игра по сети',
                                          color=self.c1,
                                          size=(Window.width * 0.24, Window.height * 0.11), size_hint=(None, None),
                                          background_color=(0, 0, 0, 0),
                                          font_size=Window.height * 0.05, )
        self.layout.add_widget(self.new_net_game_btn)
        self.new_net_game_btn.bind(on_press=self.new_net_game_bind)
        self.all_buttons.append(self.new_net_game_btn)

        self.new_single_game_btn = Button(pos=(Window.width * 0.37, Window.height * 0.7), text='Одиночный режим', color=self.c1,
                                          size=(Window.width * 0.24, Window.height * 0.11), size_hint=(None, None),
                                          background_color=(0, 0, 0, 0),
                                          font_size=Window.height * 0.05, )
        self.layout.add_widget(self.new_single_game_btn)
        self.new_single_game_btn.bind(on_release=self.new_single_game_bind)
        self.all_buttons.append(self.new_single_game_btn)

        self.deck_btn = Button(pos=(Window.width * 0.37, Window.height * 0.62), text='Сбор колоды',
                                          color=self.c1,
                                          size=(Window.width * 0.24, Window.height * 0.11), size_hint=(None, None),
                                          background_color=(0, 0, 0, 0),
                                          font_size=Window.height * 0.05, )
        self.layout.add_widget(self.deck_btn)
        self.deck_btn.bind(on_release=self.deck_bind)
        self.all_buttons.append(self.deck_btn)

        self.settings_btn = Button(pos=(Window.width * 0.37, Window.height * 0.54), text='Настройки',
                                   color=self.c1,
                                   size=(Window.width * 0.24, Window.height * 0.11), size_hint=(None, None),
                                   background_color=(0, 0, 0, 0),
                                   font_size=Window.height * 0.05, )
        self.layout.add_widget(self.settings_btn)
        self.settings_btn.bind(on_release=self.settings_bind)
        self.all_buttons.append(self.settings_btn)

        self.exit_btn = Button(pos=(Window.width * 0.37, Window.height * 0.46), text='Выход',
                                   color=self.c1,
                                   size=(Window.width * 0.24, Window.height * 0.11), size_hint=(None, None),
                                   background_color=(0, 0, 0, 0),
                                   font_size=Window.height * 0.05, )
        self.layout.add_widget(self.exit_btn)
        self.exit_btn.bind(on_release=self.stop)
        self.all_buttons.append(self.exit_btn)

        for b in self.all_buttons:
            b.bind(on_press=self.darker_col_on_touch_down)
            b.bind(on_release=self.default_col_on_release)

        root.add_widget(self.layout)
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
m = MainMenuApp(game, WINDOW_SIZE)
m.run()
