from collections import defaultdict
import kivy
kivy.require('2.0.1')
from kivy import Config#
Config.set('input', 'mouse', 'mouse,multitouch_on_demand')
from kivy.core.window import Window
from kivy.uix.floatlayout import FloatLayout
from kivy.app import App
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.button import Button
from kivy.uix.widget import Widget
from kivy.uix.label import Label
from kivy.graphics import Line, Color, Rectangle, Ellipse
from kivy.uix.gridlayout import GridLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.image import Image
from kivy.uix.filechooser import FileChooserListView
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.uix.treeview import TreeView
from game import Game
import berserk_gui
from game_properties import GameStates
from cards.card import *
import placement
import os
import copy
import re
from functools import partial
from deck import *

class MainField(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

class DeckSelectionApp(App):

    def __init__(self, window_size, **kwargs):
        super(DeckSelectionApp, self).__init__(**kwargs)
        Window.size = window_size
        self.window_size = window_size
        if window_size == (1920, 1080):
            Window.maximize()
        global CARD_X_SIZE, CARD_Y_SIZE, STACK_DURATION, TURN_DURATION, DZ_SIZE
        CARD_X_SIZE = (Window.width * 0.07)
        CARD_Y_SIZE = CARD_X_SIZE  # (Window.height * 0.15)
        self.title = 'Berserk Renewal'
        l = Library()
        l.load()
        self.all_cards = []
        self.card_count_down_dict = defaultdict(int)
        self.card_count_up_dict = {}
        vals = l.get_cards()
        self.all_cards = vals
        self.reset_dicts()
        self.deck_obj = Deck()

    def reset_dicts(self):
        for card, count in self.all_cards :
            self.card_count_up_dict[card.__class__] = count
            self.card_count_down_dict[card.__class__] = 0

    def check(self, card):
        return self.card_count_down_dict[card] > 0

    def move_card(self, rl, card_inst, card,  *args):
        with self.layout.canvas:
            self.card_preview = Image(source=card_inst.pic[:-4] + '_full.jpg', pos=(-0.025 * Window.width, 0),
                                      size=(0.2 * Window.width, 0.2 * Window.width), opacity=1)
        if rl in self.cards_up:
            # self.update_labels()
            if self.card_count_down_dict[card] == 0:
                rl1 = self.create_card_widget(card_inst)
                self.base_overlays[rl1] = RelativeLayout()
                rl1.add_widget(self.base_overlays[rl1])
                self.draw_card_overlay(rl1, card_inst)
                self.cards_down.append(rl1)
                self.gl2.add_widget(rl1)
                self.cards_down_dict[card] = rl1
            else:
                rl1 = self.cards_down_dict[card]
            self.card_count_down_dict[card] += 1
            self.card_count_up_dict[card] -= 1
            self.draw_card_count(rl1, card_inst, up=False)
            self.draw_card_count(rl, card_inst)
        elif rl in self.cards_down:
            # self.update_labels()
            if self.card_count_down_dict[card] == 1:
                self.gl2.remove_widget(self.cards_down_dict[card])
                self.cards_down.remove(self.cards_down_dict[card])
                rl1 = None
            else:
                rl1 = self.cards_down_dict[card]
            self.card_count_up_dict[card] += 1
            self.card_count_down_dict[card] -= 1
            self.draw_card_count(self.cards_up_dict[card], card_inst)
            if rl1:
                self.draw_card_count(rl1, card_inst, up=False)
        self.deck_lbl.text = f'Ваша дека, {sum(self.card_count_down_dict.values())} карт'

    def draw_card_count(self, rl, card, up=True):
        if up:
            count = self.card_count_up_dict[card.__class__]
            # print(rl)
        else:
            count = self.card_count_down_dict[card.__class__]
        lyy = self.base_overlays[rl]
        try:
            lyy.remove_widget(self.count_labels_dict[rl])
        except:
            pass
        ly = RelativeLayout()
        with ly.canvas:
            if count == 0:
                Color(0, 0, 0)
            elif count > 0:
                Color(0, 0, 1)
            else:
                Color(1, 0, 0)
            Rectangle(pos=(CARD_Y_SIZE * 0.73, CARD_Y_SIZE * 0.85), size=(CARD_X_SIZE * 0.27, CARD_Y_SIZE * 0.15),
                      color=(1, 1, 1, 0.3), pos_hint=(None, None))
            Color(1, 1, 1)
            Line(width=0.5, color=(1, 1, 1, 0),
                 rectangle=(CARD_Y_SIZE * 0.73, CARD_Y_SIZE * 0.85, CARD_X_SIZE * 0.27, CARD_Y_SIZE * 0.15))
            lbl = Label(pos=(CARD_Y_SIZE * 0.73, CARD_Y_SIZE * 0.85), text=f'{count}',
                        color=(1, 1, 1, 1),
                        size=(CARD_X_SIZE * 0.3, CARD_Y_SIZE * 0.15),
                        pos_hint=(None, None), font_size=Window.height * 0.02)
            self.count_labels.append(lbl)
        self.count_labels_dict[rl] = ly
        lyy.add_widget(ly)

    def draw_card_overlay(self, rl, card):
        size_ = (CARD_X_SIZE - 2, CARD_Y_SIZE * 0.18)
        lyy = self.base_overlays[rl]
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
                         font_size=Window.height * 0.02, )
            self.card_nameplates.append(lbl_)
            # cost
            if card.cost[0] == 0:
                Color(0.9, 0.9, 0.9)
                cost = card.cost[1]
            else:
                Color(1, 1, 0)
                cost = card.cost[0]
            Rectangle(pos=(1, 0.18 * CARD_Y_SIZE + 1), size=(CARD_X_SIZE * 0.27, CARD_Y_SIZE * 0.15),
                      color=(1, 1, 1, 0.3), pos_hint=(None, None))
            Color(0, 0, 0)
            Line(width=0.5, color=(1, 1, 1, 0),
                 rectangle=(1, CARD_Y_SIZE * 0.18 + 1, CARD_X_SIZE * 0.27, CARD_Y_SIZE * 0.15))
            lbl = Label(pos=(1, 0.18 * CARD_Y_SIZE + 1), text=f'{cost}',
                        color=(0, 0, 0, 1),
                        size=(CARD_X_SIZE * 0.3, CARD_Y_SIZE * 0.15),
                        pos_hint=(None, None), font_size=Window.height * 0.02)
            self.cost_labels.append(lbl)
        lyy.add_widget(ly)

    def display_cards(self):
        for i, (card, count) in enumerate(self.all_cards):
            rl1 = self.create_card_widget(card)
            self.cards_up.append(rl1)
            self.base_overlays[rl1] = RelativeLayout()
            rl1.add_widget(self.base_overlays[rl1])
            self.draw_card_overlay(rl1, card)
            self.draw_card_count(rl1, card)
            self.gl1.add_widget(rl1)
            self.cards_up_dict[card.__class__] = rl1

    def create_card_widget(self, card):
        rl1 = RelativeLayout(size=(CARD_X_SIZE, CARD_X_SIZE), size_hint=(None, None))
        btn1 = Button(disabled=False, pos=(0, CARD_Y_SIZE * 0.18), background_down=card.pic,
                      background_normal=card.pic, size=(CARD_X_SIZE, CARD_Y_SIZE * 0.85), size_hint=(None, None),
                      border=(0, 0, 0, 0))
        btn1.bind(on_press=partial(self.move_card, rl1, card, card.__class__))
        rl1.add_widget(btn1)
        return rl1

    def open_deck(self, path, filename, *args):
        if self.filechoser.selection:
            deck_ = self.deck_obj.load_deck(self.filechoser.selection[0])
            self.reset_dicts()
            self.gl2.clear_widgets()
            for c in deck_:
                self.card_count_down_dict[c] += 1
                self.card_count_up_dict[c] -= 1
            for k, v in self.cards_up_dict.items():
                self.draw_card_count(v, k())
            for cardcls, count in self.card_count_down_dict.items():
                if count > 0:
                    inst = cardcls()
                    rl1 = self.create_card_widget(inst)
                    self.base_overlays[rl1] = RelativeLayout()
                    rl1.add_widget(self.base_overlays[rl1])
                    self.draw_card_overlay(rl1, inst)
                    self.cards_down.append(rl1)
                    self.gl2.add_widget(rl1)
                    self.cards_down_dict[cardcls] = rl1
                    self.draw_card_count(rl1, inst, up=False)
            self.deck_lbl.text = f'Ваша дека, {len(deck_)} карт'

    def activate_save(self, save=True, *args):
        self.tinput.opacity = 1
        self.tinput.disabled = False
        self.tinput.focus = True
        self.tinput.select_all()
        self.okbtn.opacity = 1
        self.okbtn.disabled = False
        if save:
            self.tinput.text = 'Название деки'
            self.okbtn.bind(on_release=self.bindok)
        else:
            self.okbtn.bind(on_release=self.deactivate_save)
        Window.bind(on_key_down=self.save_deck_enter)

    def deactivate_save(self, *args):
        self.tinput.opacity = 0
        self.tinput.disabled = True
        self.tinput.focus = False
        self.okbtn.opacity = 0
        self.okbtn.disabled = True
        try:
            self.okbtn.unbind(on_release=self.bindok)
        except:
            print('rttt')
        Window.unbind(on_key_down=self.save_deck_enter)

    def deck_check(self, cards):
        text = ''
        res = True
        if len(cards) > 50:
            text = f'Более 50 карт в деке'
            res = False
            return res, text
        if len(cards) < 30:
            text = f'Менее 30 карт в деке'
            res = False
            return res, text
        for card in cards:
            if self.card_count_up_dict[card] < 0:
                text = f'Недостаточно копий: {card().name}'
                res = False
                return res, text
            if self.card_count_down_dict[card] > 3 and CardEffect.ORDA not in card().active_status:
                text = f'Cлишком много копий: {card().name}'
                res = False
                return res, text
            elif self.card_count_down_dict[card] > 5 and CardEffect.ORDA in card().active_status:
                text = f'Cлишком много копий: {card().name}'
                res = False
                return res, text
        return res, text

    def save_deck(self, *args):
        cards = []
        for key, vals in self.card_count_down_dict.items():
            cards.extend([key for x in range(vals)])
        chk, text = self.deck_check(cards)
        # pat = re.compile(r'\s')
        deck_name = self.tinput.text #re.sub(pat, '', self.tinput.text)
        if chk and deck_name:
            self.deck_obj.save_deck(cards=cards, name=deck_name)
            self.tinput.text = ''
            self.deactivate_save()
            self.filechoser._update_files()
        elif text:
            self.tinput.text = ''
            self.deactivate_save()
            p = Popup(title='Berserk renewal',
                    content=Label(text=text), background_color=(1, 0, 0, 1),
                    size_hint=(None, None), size=(Window.width/3, Window.height/3))
            p.open()
        else:
            self.tinput.text = ''

    def try_delete(self, path, *args):
        try:
            os.remove(path)
            self.filechoser._update_files()
        except:
            pass

    def del_deck(self, *args):
        if self.filechoser.selection:
            rl = RelativeLayout()
            lbl = Label(text='Вы уверенны?', y=Window.height * 0.06)
            rl.add_widget(lbl)
            btn1 = Button(text='Удалить', pos=(Window.width * 0.01, Window.height * 0.01), background_color=(1, 0, 0, 1),
                          size=(Window.width * 0.08, Window.height * 0.04), size_hint=(None, None))
            btn2 = Button(text='Отмена', pos=(Window.width * 0.22, Window.height * 0.01), background_color=(1, 0, 0, 1),
                          size=(Window.width * 0.08, Window.height * 0.04), size_hint=(None, None))
            rl.add_widget(btn1)
            rl.add_widget(btn2)
            p = Popup(title='', separator_height=0,
                      content=rl, background_color=(1, 0, 0, 1),
                      size_hint=(None, None), size=(Window.width / 3, Window.height / 3))
            btn2.bind(on_press=p.dismiss)
            btn1.bind(on_press=partial(self.try_delete, self.filechoser.selection[0]))
            btn1.bind(on_press=p.dismiss)
            p.open()

    def save_deck_enter(self, instance, keyboard, keycode, text, modifiers):
        if keycode == 40:
            self.save_deck()

    def show_export(self, *args):
        if self.filechoser.selection:
            try:
                with open(self.filechoser.selection[0], 'r') as f:
                    text = f.read()
                    self.activate_save(False)
                    self.tinput.text = text
                    self.tinput.select_all()
            except Exception as e:
                print(e)

    def on_entry_added_(self, *args):
        if (args[1].path)==os.getcwd():
            return True

    def build(self):
        root = MainField()
        self.layout = FloatLayout(size=(Window.width, Window.height))
        self.base_overlays = {}
        # self.card_dict = {}
        self.card_nameplates = []
        self.cost_labels = []
        self.count_labels = []
        self.count_labels_dict = {}
        self.cards_down_dict = {}
        self.cards_up_dict = {}
        self.cards_up = []
        self.cards_down = []
        self.card_preview = None

        with root.canvas:
            root.bg_rect = Rectangle(source='data/bg/dark_bg_7.jpg', pos=root.pos, size=Window.size)
            points_x = [(Window.width * 0.2 + i * CARD_X_SIZE, Window.height * 0.675,
                         Window.width * 0.2 + i * CARD_X_SIZE, Window.height * 0.924) for i in range(9)]
            points_y = [(Window.width * 0.2, Window.height * 0.55 + i * CARD_X_SIZE,
                         Window.width * 0.76, Window.height * 0.55 + i * CARD_X_SIZE) for i in range(1, 4)]
            for i in range(3):
                c = Color(1, 1, 1, 0)
                Line(color=c, points=points_y[i])
            for j in range(9):
                Line(color=c, points=points_x[j])
            c1 = Color(0.5, 0, 0, 1)
            Line(color=c, points=(Window.width * 0.15, 0,
                                  Window.width * 0.15, Window.height), width=4)
            Line(color=c, points=(Window.width * 0.8, 0,
                                  Window.width * 0.8, Window.height), width=4)
            Line(color=c, points=(Window.width * 0.15, Window.height * 0.5,
                                  Window.width * 0.80, Window.height * 0.5), width=4)

        numrows = len(self.all_cards) // 8 + 1
        self.sv2 = ScrollView(size_hint=(1, None), size=(Window.width / 2, Window.height *0.45),
                              always_overscroll=False, pos=(Window.width*0.2, Window.height * (0.0)),)
        self.sv1 = ScrollView(pos=(Window.width*0.2, Window.height * 0.53), size_hint=(1, None), always_overscroll=False,
                              size=(Window.width / 2, Window.height *0.46))
        self.gl2 = GridLayout(cols=8, spacing=(1, 5), size_hint_y=None)
        self.gl1 = GridLayout(cols=8, spacing=(1, 5), size_hint_y=None)
        self.gl2.bind(minimum_height=self.gl2.setter('height'))
        self.gl1.bind(minimum_height=self.gl1.setter('height'))
        for j in range(numrows):
            for i in range(8):
                btn1 = Button(text=str(i + j*8), disabled=False, opacity=0.8,
                              pos=(Window.width * 0.2 + i * CARD_X_SIZE,
                                   Window.height * 0.775 - j * CARD_X_SIZE),
                              size=(CARD_X_SIZE, CARD_Y_SIZE), size_hint=(None, None))
                btn2 = Button(text=str(i + j*8), disabled=False, opacity=0.8,
                              pos=(Window.width * 0.2 + i * CARD_X_SIZE,
                                   Window.height * 0.35 - j * CARD_X_SIZE),
                              size=(CARD_X_SIZE, CARD_Y_SIZE), size_hint=(None, None))
        #         if i + j*8 < 50:
        #             self.gl1.add_widget(btn1)
        #         print(i + j*8)
        #         self.gl2.add_widget(btn2)
        self.sv1.add_widget(self.gl1)
        self.layout.add_widget(self.sv1)
        self.sv2.add_widget(self.gl2)
        self.layout.add_widget(self.sv2)

        self.deck_lbl = Label(pos=(0, 0), text=f'Ваша дека, 0 карт',
                        color=(1, 1, 1, 1), font_size=Window.height * 0.02)
        self.layout.add_widget(self.deck_lbl)

        self.filechoser = FileChooserListView(size_hint=(0.2, 0.44),
                                pos=(Window.width*0.81, Window.height*0.56))
        self.filechoser.bind(on_submit=partial(self.open_deck, self.filechoser.path, self.filechoser.selection))
        with root.canvas:
            Color(0, 0, 0, 0.4)
            self.background_rect = Rectangle(size=(Window.width*0.2, Window.height*0.6),  pos=(Window.width*0.8025, Window.height*0.45))

        self.filechoser.bind(on_entry_added=self.on_entry_added_)
        self.filechoser.filters = ['*.bdck']
        self.filechoser.path = './user_decks'

        btn2 = Button(text='Загрузить', pos=(Window.width * 0.81, Window.height * 0.51), background_color=(1, 0, 0, 1),
                                size=(Window.width * 0.08, Window.height * 0.04), size_hint=(None, None))
        btn2.bind(on_release=partial(self.open_deck, self.filechoser.path, self.filechoser.selection))
        btn3 = Button(text='Сохранить', pos=(Window.width * 0.9, Window.height * 0.51), background_color=(1, 0, 0, 1),
                      size=(Window.width * 0.08, Window.height * 0.04), size_hint=(None, None))
        btn3.bind(on_release=partial(self.activate_save, True))
        btn5 = Button(text='Удалить', pos=(Window.width * 0.81, Window.height * 0.46), background_color=(1, 0, 0, 1),
                      size=(Window.width * 0.08, Window.height * 0.04), size_hint=(None, None))
        btn5.bind(on_release=partial(self.del_deck))
        btn6 = Button(text='Экспорт', pos=(Window.width * 0.9, Window.height * 0.46), background_color=(1, 0, 0, 1),
                      size=(Window.width * 0.08, Window.height * 0.04), size_hint=(None, None))
        btn6.bind(on_release=partial(self.show_export))
        self.layout.add_widget(self.filechoser)
        self.layout.add_widget(btn2)
        self.layout.add_widget(btn3)
        self.layout.add_widget(btn5)
        self.layout.add_widget(btn6)

        self.tinput = TextInput(text='Название деки', size=(Window.width * 0.18, Window.height * 0.05), font_size=Window.height*0.024,
                                multiline=False,
                                pos=(Window.width * 0.81, Window.height * 0.39), size_hint=(None, None), opacity=0, disabled=True)
        self.layout.add_widget(self.tinput)
        self.okbtn = Button(text='Ок', pos=(Window.width * 0.81, Window.height * 0.34), background_color=(1, 0, 0, 1),
                      size=(Window.width * 0.08, Window.height * 0.04), size_hint=(None, None), opacity=0, disabled=True)
        self.bindok = partial(self.save_deck, self.filechoser.path, self.filechoser.selection)
        self.layout.add_widget(self.okbtn)

        root.add_widget(self.layout)
        self.display_cards()
        return root


WINDOW_SIZE = (960, 540) #(1920, 1080)
f = DeckSelectionApp(WINDOW_SIZE)
f.run()
