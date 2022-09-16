import socket
import sys

"""
returns Monitor size x and y in pixels for desktop platforms, or None for
mobile platforms
Found at:
https://groups.google.com/forum/#!topic/kivy-users/uZYrghb87g0
"""
if sys.platform == 'linux2' or sys.platform == 'linux':
    import subprocess
    output = subprocess.Popen(
        'xrandr | grep "\*" | cut -d" " -f4',
        shell=True,
        stdout=subprocess.PIPE).communicate()[0]
    screenx = int(output.decode("utf-8") .replace('\n', '').split('x')[0])
    screeny = int(output.decode("utf-8") .replace('\n', '').split('x')[1])
elif sys.platform == 'win32':
    from win32api import GetSystemMetrics
    screenx = GetSystemMetrics(0)
    screeny = GetSystemMetrics(1)
elif sys.platform == 'darwin':
    from AppKit import NSScreen
    frame_size = NSScreen.mainScreen().frame().size
    screenx = frame_size.width
    screeny = frame_size.height
else:
    # For mobile devices, use full screen
    screenx,screeny = 800, 600  # return something
# print(screenx, screeny, sys.platform)
import os
os.environ['KIVY_AUDIO'] = 'sdl2'
import kivy
kivy.require('2.0.1')
from kivy import Config
Config.set('input', 'mouse', 'mouse,multitouch_on_demand')
Config.set('graphics', 'resizable', '0')
Config.set('graphics', 'maxfps', '144')
Config.set('kivy', 'exit_on_escape', '0')
Config.remove_option('input', 'wm_pen')
Config.remove_option('input', 'wm_touch')
from kivy.core.window import Window
from kivy.uix.floatlayout import FloatLayout
from kivy.app import App
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.button import Button
from kivy.uix.widget import Widget
from kivy.uix.label import Label
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.graphics import Rectangle, Color
from kivy.utils import get_color_from_hex
from kivy.clock import Clock, mainthread
from kivy.uix.dropdown import DropDown
import threading
from functools import partial
from screens import deck_selection
#from game import Game
import network
import server

SUPPORTED_RESOLUTIONS = [(1920, 1080), (1536, 864), (1440, 900), (1366, 768), (960, 540)]

class MainField(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

class MainMenuApp(App):

    def __init__(self, window_size):
        super(MainMenuApp, self).__init__()
        self.window_size = window_size
        Window.size = self.window_size
        # if window_size == (1920, 1080):
        #     Window.maximize()
        global CARD_X_SIZE, CARD_Y_SIZE, STACK_DURATION, TURN_DURATION, DZ_SIZE
        CARD_X_SIZE = (Window.width * 0.07)
        CARD_Y_SIZE = CARD_X_SIZE  # (Window.height * 0.15)
        self.title = 'Berserk Renewal'
        self.icon = 'data/icons/Berserk_icon.ico'
        self.server_up = False
        self.garbage = []

    def open_settings(self, *largs):
        pass

    def set_connect_btn(self, *args):
        self.start_game_btn.disabled = True
        self.create_table.disabled = True
        # for b in self.gl.children:
        #     b.disabled = True


    def darker_col_on_touch_down(self, instance, *args):
        instance.color = get_color_from_hex('#FF9933')
        Clock.schedule_once(partial(self.default_col_on_release, instance), 1)

    def default_col_on_release(self, instance, *args):
        instance.color = self.c1

    def new_single_game_bind(self, *args):
        rl = RelativeLayout()
        lbl = Label(text='Сначала наберите отряд за первого игрока,\nзатем за второго, и начнём игру!',
                    y=Window.height * 0.06, font_size=Window.height*0.03)
        rl.add_widget(lbl)
        btn1 = Button(text='Ок', pos=(Window.width * 0.22, Window.height * 0.01), background_color=(1, 0, 0, 1),
                      font_size=Window.height * 0.03,
                      size=(Window.width * 0.08, Window.height * 0.04), size_hint=(None, None))
        rl.add_widget(btn1)
        p = Popup(title='', separator_height=0,
                  content=rl, background_color=(1, 0, 0, 1), overlay_color=(0, 0, 0, 0),
                  size_hint=(None, None), size=(Window.width*0.4, Window.height / 3))
        btn1.bind(on_press=p.dismiss)
        btn1.bind(on_press=self.start_for_single)
        p.open()

    def start_for_single(self, *args):
        self.stop()
        d = deck_selection.DeckSelectionApp(self.window_size, mode='single1')
        d.run()

    def new_net_game_bind(self, *args):
        rl = RelativeLayout()
        self.server_input = TextInput(text='127.0.1.1:12345', size=(Window.width * 0.15, Window.height * 0.05), # 127.0.1.1:12345  172.30.112.1:12345
                                font_size=Window.height * 0.024,
                                multiline=False,
                                pos=(Window.width * 0.035, Window.height * 0.34), size_hint=(None, None))
        rl.add_widget(self.server_input)
        self.nickname_input = TextInput(text='Унгар', size=(Window.width * 0.15, Window.height * 0.05),
                                      font_size=Window.height * 0.024,
                                      multiline=False,
                                      pos=(Window.width * 0.2, Window.height * 0.34), size_hint=(None, None))
        rl.add_widget(self.nickname_input)
        btn1 = Button(text='Подключиться к серверу', pos=(Window.width * 0.09, Window.height * 0.25), background_color=(1, 0, 0, 1),
                      font_size=Window.height * 0.03,
                      size=(Window.width * 0.2, Window.height * 0.05), size_hint=(None, None))
        rl.add_widget(btn1)
        btn2 = Button(text='Создать свой сервер', pos=(Window.width * 0.09, Window.height * 0.15),
                      background_color=(1, 0, 0, 1), font_size=Window.height * 0.03,
                      size=(Window.width * 0.2, Window.height * 0.05), size_hint=(None, None))
        rl.add_widget(btn2)
        self.server_output_label = Label(text='Сервер запущен на:', size=(Window.width * 0.35, Window.height * 0.05),
                                      opacity=0,
                                      font_size=Window.height * 0.024,
                                      pos=(Window.width * (-0.1), Window.height * 0.05), size_hint=(None, None))
        # self.garbage.append(self.server_output_label)
        rl.add_widget(self.server_output_label)
        self.server_output = TextInput(text='Сервер запущен на:', size=(Window.width * 0.15, Window.height * 0.05),
                                      opacity=0,
                                      font_size=Window.height * 0.024,
                                      multiline=False,
                                      pos=(Window.width * 0.15, Window.height * 0.05), size_hint=(None, None))
        rl.add_widget(self.server_output)
        self.conn_popup = Popup(title='', separator_height=0,
                  content=rl, background_color=(1, 0, 0, 1), overlay_color=(0, 0, 0, 0),
                  size_hint=(None, None), size=(Window.width * 0.4, Window.height*0.48))
        btn1.bind(on_press=self.server_popup)
        btn2.bind(on_press=self.on_start_server_pressed)
        self.conn_popup.open()

    def on_start_server_pressed(self, *args):
        if not self.server_up:
            self.server_up = True
            self.server_output.opacity = 1
            self.server_output_label.opacity = 1
            s = server.MainServer()
            host, port = s.HOST, s.PORT
            t = threading.Thread(target=s.start, daemon=True)
            t.start()
            self.server_output.text = str(host) + ':' + str(port)
            self.server_output.select_all()
        else:
            self.server_output_label.opacity = 1
            self.server_output_label.text = 'Сервер уже создан!'

    def server_popup_thread(self, *args):
        self.host, self.port = self.server_input.text.split(':')
        code = network.join_server(self.host, self.port, self.nickname_input.text)
        self.server_popup_mainthread(code)

    @mainthread
    def server_popup_mainthread(self, code):
        if hasattr(self, 'wait_conn_popup'):
            self.wait_conn_popup.dismiss()
        if code == -1:
            p = Popup(title='', separator_height=0, background='',
                      content=Label(text='Не удалось подключиться'), background_color=(0.8, 0.3, 0, 1),
                      overlay_color=(0, 0, 0, 0),
                      size_hint=(None, None), size=(Window.width * 0.4, Window.height * 0.38))
            p.open()
            Clock.schedule_once(lambda x: p.dismiss(), 2)
        else:
            self.conn_popup.dismiss()
            self.server_popup_display()


    def server_popup_display(self, *args):
        self.gl = GridLayout(cols=1, spacing=(0, 5), size_hint_y=None)
        rl = RelativeLayout()
        sv = ScrollView(size_hint=(None, None), size=(Window.width * 0.21, Window.height * 0.45),
                        always_overscroll=False, pos=(Window.width * 0.08, Window.height * 0.1))
        self.gl.bind(minimum_height=self.gl.setter('height'))
        # with self.gl.canvas:
        #     Color(1, 0, 0, 1, mode='rgba')
        #     Rectangle(pos=(Window.width * 0.08, Window.height * 0.1), size=(Window.width * 0.21, Window.height * 0.95))
        sv.add_widget(self.gl)
        rl.add_widget(sv)
        self.create_table = Button(text='Создать стол', disabled=False, opacity=1,
                                   pos=(Window.width * 0.02, Window.height * 0.02),
                                   size=(Window.width * 0.15, Window.height * 0.05), size_hint=(None, None))
        self.create_table.bind(on_press=partial(network.start_waiting, self.host, self.port, self))
        self.create_table.bind(on_press=Clock.schedule_once(self.update_serverlist, 1))
        self.create_table.bind(on_press=self.set_connect_btn)
        rl.add_widget(self.create_table)
        self.start_game_btn = Button(text='Подключиться', disabled=False, opacity=1,
                                     pos=(Window.width * 0.18, Window.height * 0.02),
                                     size=(Window.width * 0.15, Window.height * 0.05), size_hint=(None, None))
        self.start_game_btn.bind(on_press=self.accept_game)
        self.start_game_btn.bind(on_press=self.set_connect_btn)
        rl.add_widget(self.start_game_btn)
        p = Popup(title='', separator_height=0,
                  content=rl, background_color=(1, 0, 0, 1), overlay_color=(0, 0, 0, 0),
                  size_hint=(None, None), size=(Window.width * 0.4, Window.height * 0.7))
        p.bind(on_dismiss=self.remove_client)
        p.open()

    def server_popup(self, *args):
        t = threading.Thread(target=self.server_popup_thread, daemon=True)
        t.start()
        self.wait_conn_popup = Popup(title='', separator_height=0, background='',
                  content=Label(text='Подключаемся к серверу..'), background_color=(0.3, 0.7, 0, 1),
                  overlay_color=(0, 0, 0, 0),
                  size_hint=(None, None), size=(Window.width * 0.4, Window.height * 0.38))
        self.wait_conn_popup.open()
        #Clock.schedule_interval(self.update_serverlist, 3)

    def update_serverlist(self, *args):
        t = threading.Thread(target=network.get_waiting_players, args=(self.host, self.port, self), daemon=True)
        t.start()

    def update_serverlist_gui(self, players):
        try:
            self.gl.clear_widgets()
            for player in players:
                btn1 = Button(text=player[1].decode('utf-8'), disabled=False, opacity=1,
                              pos=(0, 0), size=(Window.width * 0.2, Window.height * 0.05), size_hint=(None, None))
                self.gl.add_widget(btn1)
                btn1.bind(on_press=lambda x: self.set_game_ip(player[0], btn1))
                btn1.bind(on_touch_down=self.join_double_click)
        except Exception as e:
            print(e)

    def join_double_click(self, btn, touch, *args):
        if touch.is_double_tap:
            self.accept_game()
            self.set_connect_btn()

    def accept_game(self, *args):
        ip = socket.gethostbyname(socket.gethostname())
        # if ip != self.game_ip:
        res = network.accept_game(self.host, self.port, self, self.game_ip)  # if res == -1 >?

    def handle_start_game_response(self, game_id, *args):
        rl = RelativeLayout()
        lbl = Label(text=f'Начнём игру?\nid:{game_id}',
                    y=Window.height * 0.06, font_size=Window.height * 0.03)
        rl.add_widget(lbl)
        btn2 = Button(text='Го!', pos=(Window.width * 0.09, Window.height * 0.07),
                      background_color=(0.6, 0.6, 0, 1), font_size=Window.height * 0.03,
                      size=(Window.width * 0.1, Window.height * 0.05), size_hint=(None, None))
        rl.add_widget(btn2)
        p = Popup(title='', separator_height=0, background='',
                  content=rl, background_color=(0.4, 0, 0.1, 1), overlay_color=(0, 0, 0, 0),
                  size_hint=(None, None), size=(Window.width * 0.3, Window.height * 0.3))
        p.open()
        btn2.bind(on_press=partial(self.start_for_constra_net, game_id))
        btn2.bind(on_press=partial(Popup.dismiss, p))

    def start_for_constra_net(self, game_id, *args):
        #self.stop()
        network.start_constr_game(self.host, self.port, self, game_id)

    def start_for_constra(self, turn, ip, port):
        for b in [self.deck_btn, self.settings_btn, self.exit_btn]:
            b.disabled = True
        self.stop()
        d = deck_selection.DeckSelectionApp(self.window_size, mode='constr', server_ip=ip, server_port=port, turn=int(turn))
        d.run()

    def set_game_ip(self, ip, instance):
        instance.disabled = False
        self.game_ip = ip

    def remove_client(self, *args):
        try:
            t = threading.Thread(target=network.client_left, args=(self.host, self.port), daemon=True)
            t.start()
        except Exception as e:
            print(e)

    def on_request_close(self, source=None, *args):
        self.remove_client()

    def settings_bind(self, *args):
        popup = Popup(title='', separator_height=0,
                       width=Window.width/2, height=Window.height/2, background_color=(1, 0, 0, 1),
                       overlay_color=(0, 0, 0, 0), size_hint=(None, None),
                       auto_dismiss=False)
        dropdown = DropDown(pos=(Window.width/2,Window.width/4))
        for index in range(len(SUPPORTED_RESOLUTIONS)):
            btn = Button(text=f'{SUPPORTED_RESOLUTIONS[index]}', background_color=(1, 0, 0, 1),
                         font_size=Window.height * 0.03,
                         size_hint_y=None, height=Window.height/20, font_name='Roboto-Regular.ttf')
            btn.bind(on_release=partial(self.set_future_res, (SUPPORTED_RESOLUTIONS[index])))
            btn.bind(on_release=lambda btn: dropdown.select(btn.text))
            dropdown.add_widget(btn)

        mainbutton = Button(text='Выберите разрешение', background_color=(1, 0, 0, 1), font_size=Window.height*0.03,
                            pos_hint={'top': 0.8, 'right': 0.4}, size_hint=(0.4, 1/10), font_name='Roboto-Regular.ttf')
        mainbutton.bind(on_release=dropdown.open)
        rl = RelativeLayout(size=popup.size, size_hint=(None, None))
        rl.add_widget(mainbutton)
        okbutton = Button(text='Сохранить', pos_hint={'top': 0.2, 'right': 0.8}, size_hint=(1 / 3, 1 / 9),
                        background_color = (1, 0, 0, 1),font_size=Window.height*0.03, font_name='Roboto-Regular.ttf')
        okbutton.bind(on_press=self.resize_)
        rl.add_widget(okbutton)
        popup.content = rl
        popup.open()

    def set_future_res(self, res, *args):
        self.future_res = res

    def resize_(self, *args):
        x, y = self.future_res[0], self.future_res[1]
        self.window_size = self.future_res
        self.stop()
        Window.size = (x, y)
        #Window.maximize()
        Window.left = (screenx - self.window_size[0]) / 2
        Window.top = (screeny - self.window_size[1]) / 2
        # Window.borderless = True
        # Window.restore()
        self.run()

    def deck_bind(self, *args):
        d = deck_selection.DeckSelectionApp(self.window_size, mode='building')
        self.stop()
        d.run()


    def build(self):
        root = MainField()
        Window.bind(on_request_close=self.on_request_close)
        self.all_buttons = []
        self.game_ip = ''
        self.layout = FloatLayout(size=(Window.width, Window.height))
        self.future_res = self.window_size

        with root.canvas:
            root.bg_rect = Rectangle(source='data/bg/dark_bg_7.jpg', pos=root.pos, size=Window.size)
        self.c1 = get_color_from_hex('#FCD618')

        # Buttons:
        self.new_net_game_btn = Button(pos=(Window.width * 0.37, Window.height * 0.78), text='Игра по сети',
                                          color=self.c1, #disabled=True,
                                          size=(Window.width * 0.24, Window.height * 0.11), size_hint=(None, None),
                                          background_color=(0, 0, 0, 0),
                                          font_size=Window.height * 0.05, font_name='data/fonts/RuslanDisplay-Regular.ttf')
        self.layout.add_widget(self.new_net_game_btn)
        self.new_net_game_btn.bind(on_press=self.new_net_game_bind)
        self.all_buttons.append(self.new_net_game_btn)

        self.new_single_game_btn = Button(pos=(Window.width * 0.37, Window.height * 0.7), text='Одиночный режим', color=self.c1,
                                          disabled=True,
                                          size=(Window.width * 0.24, Window.height * 0.11), size_hint=(None, None),
                                          background_color=(0, 0, 0, 0),
                                          font_size=Window.height * 0.05, font_name='data/fonts/RuslanDisplay-Regular.ttf')
        self.layout.add_widget(self.new_single_game_btn)
        self.new_single_game_btn.bind(on_release=self.new_single_game_bind)
        self.all_buttons.append(self.new_single_game_btn)

        self.deck_btn = Button(pos=(Window.width * 0.37, Window.height * 0.62), text='Сбор колоды',
                                          color=self.c1,
                                          size=(Window.width * 0.24, Window.height * 0.11), size_hint=(None, None),
                                          background_color=(0, 0, 0, 0),
                                          font_size=Window.height * 0.05, font_name='data/fonts/RuslanDisplay-Regular.ttf' )
        self.layout.add_widget(self.deck_btn)
        self.deck_btn.bind(on_release=self.deck_bind)
        self.all_buttons.append(self.deck_btn)

        self.settings_btn = Button(pos=(Window.width * 0.37, Window.height * 0.54), text='Настройки',
                                   color=self.c1,
                                   size=(Window.width * 0.24, Window.height * 0.11), size_hint=(None, None),
                                   background_color=(0, 0, 0, 0),
                                   font_size=Window.height * 0.05, font_name='data/fonts/RuslanDisplay-Regular.ttf')
        self.layout.add_widget(self.settings_btn)
        self.settings_btn.bind(on_release=self.settings_bind)
        self.all_buttons.append(self.settings_btn)

        self.exit_btn = Button(pos=(Window.width * 0.37, Window.height * 0.46), text='Выход',
                                   color=self.c1,
                                   size=(Window.width * 0.24, Window.height * 0.11), size_hint=(None, None),
                                   background_color=(0, 0, 0, 0),
                                   font_size=Window.height * 0.05, font_name='data/fonts/RuslanDisplay-Regular.ttf' )
        self.layout.add_widget(self.exit_btn)
        self.exit_btn.bind(on_release=self.stop)
        self.all_buttons.append(self.exit_btn)

        for b in self.all_buttons:
            b.bind(on_press=self.darker_col_on_touch_down)
            b.bind(on_release=self.default_col_on_release)

        root.add_widget(self.layout)
        return root


# filedir = 'cards/set_1'
# modules = [f[:-3] for f in os.listdir(filedir) if
#            os.path.isfile(os.path.join(filedir, f)) and f.endswith('.py') and f != '__init__.py']
# imports = [f"from cards.set_1 import {module}\nfrom cards.set_1.{module} import *" for module in sorted(modules)]
# for imp in imports:
#     exec(imp)
# STACK_DURATION = 5
# TURN_DURATION = 5
# game = Game()
# cards1 = [Lovets_dush_1(), Cobold_1(), Draks_1(), Lovets_dush_1(), Voin_hrama_1(), Draks_1(),
#           Lovets_dush_1(), PovelitelMolniy_1(), Draks_1(),Lovets_dush_1(), PovelitelMolniy_1(), Draks_1(),
#           Lovets_dush_1(), PovelitelMolniy_1(), Draks_1()]
# gui = berserk_gui.BerserkApp(game, WINDOW_SIZE, STACK_DURATION, TURN_DURATION)
# game.gui = gui
if __name__ == '__main__':
    WINDOW_SIZE = (960, 540)  # (1920, 1080) #
    m = MainMenuApp(WINDOW_SIZE)
    m.run()
