import kivy
kivy.require('1.0.1')
from kivy import Config
from kivy.core.window import Window

from kivy.uix.floatlayout import FloatLayout
from kivy.app import App
from kivy.properties import ObjectProperty, StringProperty, NumericProperty, BooleanProperty
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.relativelayout import RelativeLayout
from kivy.uix.scatterlayout import ScatterLayout
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.scrollview import ScrollView
from kivy.uix.dropdown import DropDown
from kivy.uix.button import Button
from kivy.uix.widget import Widget
from kivy.uix.label import Label
from kivy.graphics import Line, Color, InstructionGroup, Rectangle, Rotate, PushMatrix, Rotate, PopMatrix
from kivy.uix.progressbar import ProgressBar
import numpy.random as rng
from kivy.clock import Clock
from kivy.animation import Animation
from functools import partial
from itertools import chain
from kivy.uix.image import Image
from kivy.clock import mainthread
from kivy.graphics.vertex_instructions import Triangle, BorderImage
from cards.card_properties import ActionTypes, SimpleCardAction, CreatureType
import game_properties
import card_prep
import operator
import collections


#Window.size = (1920, 1080)
Window.size = (960, 540)
#Window.maximize()
CARD_X_SIZE = (Window.width * 0.084375)
CARD_Y_SIZE = (Window.height * 0.15)


class MainField(Widget):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # self.background_normal = bg_sorce
        # self.width = width
        # self.hight = hight

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
        self.title = 'Berserk Renewal'

    def destroy_x(self, list_, long=False):
        for bt in list_:
            self.root.remove_widget(bt)

    def destroy_target_marcs(self):
        for btn, card in self.target_marks_cards:
            card.remove_widget(btn)


        self.target_marks_buttons = []
        self.target_marks_cards = []

    def destroy_target_rectangles(self):
        for r, canvas in self.target_rectangles:
            canvas.remove(r)
        self.target_rectangles = []

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
        if pos.is_mouse_scrolling:
            delete_ = False
        for nav_b in self.target_marks_buttons:
            if abs(pos.x - nav_b.x) < CARD_X_SIZE and abs(pos.y - nav_b.y) < CARD_Y_SIZE:
                delete_ = False
        if delete_:
            self.destroy_target_rectangles()
            Clock.schedule_once(partial(self.destroy_x, self.die_pics), 1)
            self.die_pics = []
            #Clock.schedule_once(partial(self.destroy_x, self.red_arrows), 0.5)
            for el in self.root.canvas.children:
                if el in self.red_arrows:
                    self.root.canvas.remove(el)
            self.red_arrows = []

    def draw_selection_border(self, instance, card):
        if hasattr(self, "card_border"):
            self.card_border[1].canvas.remove(self.card_border[0])
        with instance.canvas:
            if card.player == 1:
                c = Color(1, 1, 0, 1)
            else:
                c = Color(0.2, 0.2, 0.8, 1)
            self.card_border = (Line(width=1, color=c, rectangle=(0, 0, CARD_X_SIZE, CARD_Y_SIZE)), instance)

    def on_click_on_card(self, card, instance):
        self.destroy_target_marcs()
        if self.selected_card:
            Clock.schedule_once(partial(self.draw_card_overlay, card, False))
        self.selected_card = card
        self.destroy_x(self.selected_card_buttons)
        # Draw border
        self.draw_selection_border(instance.parent, card)
        # Higlight name
        self.bright_card_overlay(card)
        # Display card action buttons
        self.display_card_actions(card, instance)
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
        if card.type == CreatureType.FLYER:
            if card.player == 1:
                self.dop_zone_1.children[0].remove_widget(self.cards_dict[card])
            else:
                self.dop_zone_2.children[0].remove_widget(self.cards_dict[card])
        else:
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
                x, y = self.cards_dict[card].pos
            if victim.type == CreatureType.FLYER or victim.type == CreatureType.LAND:
                if victim.player == 1:
                    n, m = self.dop_zone_1.to_parent(to_card.x, to_card.y)
                else:
                    n, m = self.dop_zone_2.to_parent(to_card.x, to_card.y)
            else:
                n, m = to_card.x, to_card.y

            l = Line(width=3, color=c, points=(x+CARD_X_SIZE/2, y+CARD_Y_SIZE/2,
                                           n+CARD_X_SIZE/2, m+CARD_Y_SIZE/2))
            # TODO
            # tri = Triangle(color=c, points=[x*0.7+(x-n)*0.15*0.57, (x-n)*0.85+n*0.1,
            #                                  n+CARD_X_SIZE/2, m+CARD_Y_SIZE/2,
            #                                 x*0.7+(x-n)*0.15*0.57, (y-m)*0.85+m])
            self.red_arrows.append(l)
            #self.red_arrows.append(tri)

    def draw_die(self, r1, r2):
        r1_i = Image(source=f'data/dice/Alea_{r1}.png', pos=(Window.width*0.78, Window.height*0.8), size=(0.07*Window.width, Window.height*0.07))
        r2_i = Image(source=f'data/dice/Alea_{r2}.png', pos=(Window.width*0.12, Window.height*0.8), size=(0.07*Window.width, Window.height*0.07))
        self.root.add_widget(r1_i)
        self.root.add_widget(r2_i)
        self.die_pics.append(r1_i)
        self.die_pics.append(r2_i)


    def perform_card_action(self, card, ability, victim, btn, instance):
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

        self.destroy_target_rectangles()

        if card.curr_life <= 0:
            self.destroy_card(card)
        if victim.curr_life <= 0:
            self.destroy_card(victim)

        card.actions_left -= 1
        if card.actions_left <= 0:
            self.tap_card(card)
            for b in self.selected_card_buttons:
                b.disabled = True

        self.destroy_target_marcs()
        #self.destroy_x(self.target_marks_buttons)
        #self.target_marks_buttons = []

    def tap_card(self, card):
        scatter_obj = self.cards_dict[card]
        for obj_ in scatter_obj.children:
            if isinstance(obj_, Button):
                ch = obj_
        if not card.tapped:
            ch.background_normal = card.pic[:-4]+'_rot90.jpg'
            ch.pos = (CARD_X_SIZE*0.2, 0)
            ch.size = (CARD_X_SIZE*0.8, CARD_Y_SIZE)
            self.draw_card_overlay(card, True)
            card.tapped = True
        else:
            ch.background_normal = card.pic
            card.tapped = False


    def display_available_targets(self, board, card, ability, instance):
        self.destroy_target_marcs()
        b_size = 30  # размер квадратика
        if ability == 'attack':
            range_of_action = 1
        else:
            range_of_action = ability.range
        if card.type == CreatureType.CREATURE:
            targets = board.get_available_targets_ground(board.game_board.index(card), range_=range_of_action)  # targets are card objects
        elif card.type == CreatureType.FLYER:
            targets = board.get_available_targets_flyer(card)
        for t in targets:
            if card.type == CreatureType.ARTIFACT or card.type == CreatureType.CREATURE:
                x, y = self.cards_dict[t].pos
            else:
                if t.player == 1 and (t.type != CreatureType.ARTIFACT and t.type != CreatureType.CREATURE ):
                    x, y = self.dop_zone_1.to_parent(*self.cards_dict[t].pos)
                elif t.player == 2 and (t.type != CreatureType.ARTIFACT and t.type != CreatureType.CREATURE):
                    x, y = self.dop_zone_2.to_parent(*self.cards_dict[t].pos)
                else:
                    x, y = self.cards_dict[t].pos
            with self.cards_dict[t].canvas:
                btn = Button(pos=(0,0),
                             background_color=(1, 1, 1, 0.0),
                             size=(CARD_X_SIZE, CARD_Y_SIZE), size_hint=(None, None))
                if t.player == self.backend.current_active_player:
                    c = Color(1, 1, 1, 0.8)
                else:
                    c = Color(1, 0, 0, 1)
                rect1 = Rectangle(pos=(CARD_X_SIZE / 2 - b_size / 2,
                              CARD_Y_SIZE / 2 - b_size / 2),
                         background_color=c,
                         size=(b_size, b_size), size_hint=(1, 1))
                c = Color(1, 1, 1, 0.15)
                rect2 = Rectangle(size=(CARD_X_SIZE, CARD_Y_SIZE ),
                                  background_color=c,
                                  pos=(0,0), size_hint=(1, 1))
                self.target_rectangles.append((rect1, self.cards_dict[t].canvas))
                self.target_rectangles.append((rect2, self.cards_dict[t].canvas))

                btn.bind(on_press=partial(self.perform_card_action, card, ability, t, btn))
                self.cards_dict[t].add_widget(btn)

                self.target_marks_buttons.append(btn)
                self.target_marks_cards.append([btn, self.cards_dict[t]])

    def display_card_actions(self, card, instance):
        if self.backend.current_active_player == card.player:
            disabled_ = operator.not_(bool(card.actions_left))
        else:
            disabled_ = True
        # adding attack button
        btn1 = Button(text=f'Атака {card.attack[0]}-{card.attack[1]}-{card.attack[2]}',
                      pos=(Window.width * 0.84, Window.height * 0.20),
                      disabled=disabled_,
                      size=(Window.width * 0.14, Window.height * 0.05), size_hint=(None, None))
        Clock.schedule_once(lambda x: btn1.bind(on_press=partial(self.display_available_targets, self.backend.board, card, 'attack')), 0.5)
        #btn1.bind(disabled=lambda x: operator.not_(bool(card.actions_left)))
        self.root.add_widget(btn1)
        self.selected_card_buttons.append(btn1)
        # adding abilities buttons
        for i, ability in enumerate(card.abilities):
            btn = Button(text=ability.txt,
                          pos=(Window.width * 0.84, Window.height * 0.20 - (i + 1) * 0.05 * Window.height),
                          disabled=disabled_,
                          size=(Window.width * 0.14, Window.height * 0.05), size_hint=(None, None))
            btn.bind(on_press=partial(self.display_available_targets, self.backend.board, card, ability))
            self.root.add_widget(btn)
            self.selected_card_buttons.append(btn)

    def draw_card_overlay(self, *args):
        card = args[0]
        turned = args[1]
        if turned:
            size_ = (CARD_Y_SIZE * 0.2, CARD_X_SIZE)
            lx = self.base_overlays[card]
            with lx.canvas.before:
                PushMatrix()
                self.rotation = Rotate()
                self.rotation.origin = (lx.x+CARD_X_SIZE/2, lx.y+CARD_Y_SIZE/2)
                self.rotation.angle = -90
            with lx.canvas.after:
                PopMatrix()
        else:
            size_ = (CARD_X_SIZE, CARD_Y_SIZE * 0.2)
            if not self.selected_card == card or turned:
                lyy = self.base_overlays[card]
                ly = RelativeLayout()
                self.cards_dict[card].remove_widget(self.card_nameplates_dict[card])
                with ly.canvas:
                    if card.player == 1:
                        c = Color(1, 1, 0.6, 1)
                        c1 = (0, 0, 0, 1)
                    else:
                        c = Color(0.4, 0.5, 1, 1)
                        c1 = (1, 1, 1, 1)
                    rect = Rectangle(pos=(0, 0), background_color=c,
                                 size=size_,
                                 font_size=Window.height * 0.02)
                    name = (card.name[:12] + '..') if len(card.name) > 14 else card.name
                    lbl_ = Label(pos=(0, 0), text=f'{name}', color=c1,
                                 size=size_,
                                 font_size=Window.height * 0.02,)

                    #self.card_nameplate_rect_dict[card] = rect
                    self.card_nameplates.append(lbl_)
                    lyy.add_widget(ly)
                    self.card_nameplates_dict[card] = ly

    def bright_card_overlay(self, card):
        lyy = self.base_overlays[card]
        self.cards_dict[card].remove_widget(self.card_nameplates_dict[card])
        ly = RelativeLayout()
        with ly.canvas:
            if card.player == 1:
                c = Color(1, 1, 0, 1)
                c1 = (0, 0, 0, 1)
            else:
                c = Color(0.1, 0.1, 1, 1)
                c1 = (1, 1, 1, 1)
            rect = Rectangle(pos=(0, 0), background_color=c,
                             size=(CARD_X_SIZE, CARD_Y_SIZE * 0.2),
                             font_size=Window.height * 0.02)
            name = (card.name[:12] + '..') if len(card.name) > 14 else card.name
            lbl_ = Label(pos=(0, 0), text=f'{name}', color=c1,
                         size=(CARD_X_SIZE, CARD_Y_SIZE * 0.2),
                         font_size=Window.height * 0.02, )
            self.card_nameplates.append(lbl_)
            self.card_nameplates_dict[card] = ly
        lyy.add_widget(ly)
        #self.cards_dict[card].add_widget(lyy)

    def reveal_cards(self, cards):
        for card in cards:
            loc = card.loc
            if card.type == CreatureType.FLYER:
                x, y = self.dz1_btn.pos
                rl1 = RelativeLayout(size=(CARD_X_SIZE, CARD_Y_SIZE))
                btn1 = Button(disabled=False,
                              background_normal=card.pic, pos=(0, CARD_Y_SIZE*0.2),
                              size=(CARD_X_SIZE, CARD_Y_SIZE*0.8), size_hint=(None, None))
                # update backend
                self.backend.board.game_board[card.loc] = 0
                card.loc = -1
                if card.player == 1:
                    self.dop_zone_1_gl.add_widget(rl1)
                    self.dop_zone_1_buttons.append(rl1)
                    self.backend.board.extra1.append(card)
                else:
                    self.dop_zone_2_gl.add_widget(rl1)
                    self.dop_zone_2_buttons.append(rl1)
                    self.backend.board.extra2.append(card)
            else:
                x, y = self.card_position_coords[loc]
                rl1 = RelativeLayout(pos=(x, y))
                btn1 = Button(disabled=False,  pos=(0, CARD_Y_SIZE*0.2),
                          background_normal=card.pic,# pos_hint = {'center_x': .5, 'center_y': .5},
                          size=(CARD_X_SIZE, CARD_Y_SIZE*0.8), size_hint=(None, None))


            btn1.bind(on_press=partial(self.on_click_on_card, card))
            rl1.add_widget(btn1)
            #rl1.bind(pos=rl1.setter('pos'))
            #with rl1.canvas:
            # LIFE
            base_overlay_layout = RelativeLayout()
            with base_overlay_layout.canvas:
                Color(0, 0.3, 0.1)
                Rectangle(pos=(0, CARD_Y_SIZE*0.8), size=(CARD_X_SIZE*0.33, CARD_Y_SIZE*0.2), color=(1,1,1,0.3), pos_hint=(None, None))
                Color(1, 1, 1)
                Line(width=0.5, color=(1,1,1,0), rectangle=(0,CARD_Y_SIZE*0.8,CARD_X_SIZE*0.33, CARD_Y_SIZE*0.2))
                lbl = Label(pos=(0, CARD_Y_SIZE*0.8), text=f'{card.life}/{card.life}', color=(1, 1, 1, 1), size=(CARD_X_SIZE * 0.3, CARD_Y_SIZE * 0.2),
                  pos_hint=(None, None), font_size='12')
                self.hp_label_dict[card] = lbl
                self.base_overlays[card] = base_overlay_layout
                Clock.schedule_once(partial(self.draw_card_overlay, card, False), 0.1)
            rl1.add_widget(base_overlay_layout)
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

    def update_timer(self, instance):
        if self.backend.curr_game_state == game_properties.GameStates.MAIN_PHASE:
            self.timer_label.text = game_properties.state_to_str[self.backend.curr_game_state] + ' игрока ' + str(self.backend.current_active_player)
        else:
            self.timer_label.text = game_properties.state_to_str[self.backend.curr_game_state]

    def timer_update(self, duration, instance, value, completeion_ratio):
        try:
            minutes = int(completeion_ratio * duration) // 60
            rem_m = (duration - int(completeion_ratio * duration)) // 60
        except ZeroDivisionError:
            minutes = 0
            rem_m = 0
        total_min = duration//60
        seconds = completeion_ratio * duration - minutes * 60
        # Weired bar behaviour for low width values
        if (Window.width * 0.15) * (1 - completeion_ratio) > Window.width * 0.01:
            bar_w = (Window.width * 0.15) * (1 - completeion_ratio)
        else:
            bar_w = Window.width * 0.01
        self.timer_bar.size = (bar_w, Window.height * 0.03)
        if self.backend.curr_game_state == game_properties.GameStates.MAIN_PHASE:
            txt = game_properties.state_to_str[self.backend.curr_game_state] + ' игрока ' + str(self.backend.current_active_player)
        else:
            txt = game_properties.state_to_str[self.backend.curr_game_state]
        self.timer_label.text = txt + ' ' + str(int(total_min-minutes))+':'+str(int(duration-rem_m*60-seconds)).zfill(2)

    def start_timer(self, *args):
        duration = args[0]
        if hasattr(self, 'timer'):
            self.timer.cancel(self.timer_label)
        if hasattr(self, 'timer_ly'):
            self.root.remove_widget(self.timer_ly)
        self.timer_ly = RelativeLayout()
        with self.timer_ly.canvas:
            self.timer_bar_back = BorderImage(size=(Window.width * 0.15, Window.height * 0.03),
                                              pos=(Window.width * 0.83, Window.height * 0.36),
                                              color=Color(0.6, 0.15, 0, 1), minimum_width=0)
            self.timer_bar = BorderImage(size=(Window.width * 0.15, Window.height * 0.03),
                                         pos=(Window.width * 0.83, Window.height * 0.36),
                                        color=Color(1,1,0.3,1), minimum_width=0)
            self.lbl = Label(text=game_properties.state_to_str[self.backend.curr_game_state],
                        pos=(Window.width * 0.88, Window.height * 0.36), color=(0, 0, 0, 1),
                        size=(CARD_X_SIZE * 0.3, CARD_Y_SIZE * 0.2),
                        pos_hint=(None, None), font_size=str(Window.height * 0.016))
            self.timer_label = self.lbl
        self.root.add_widget(self.timer_ly)

        self.timer = Animation(s=1 / 30, duration=duration)
        self.timer.bind(on_progress=partial(self.timer_update, duration))
        self.timer.start(self.timer_label)
        # ph_button.bind(on_press=Clock.schedule_once(self.update_timer, 0.1))
        self.timer.bind(on_complete=self.backend.next_game_state)
        self.timer.bind(on_complete=partial(self.start_timer, duration))


    def build(self):
        root = MainField()
        with root.canvas:
            root.bg_rect = Rectangle(source='data/bg/dark_bg_7.jpg', pos=root.pos, size=Window.size)
       # root.add_widget(Vertical())
       # root.add_widget(Horizontal())
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
        self.card_nameplates = []
        #self.card_nameplate_rect_dict = {}
        self.target_rectangles = []
        self.target_marks_cards = []
        self.card_nameplates_dict = collections.defaultdict(RelativeLayout)
        self.base_overlays = {}
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
        # when user clicked on square outside target card
        Window.bind(on_touch_down=self.delete_target_marks_on_unfocus)
        root.add_widget(self.layout)

        # Button for phase skip
        ph_button = Button(text="Пропустить", disabled=False,
                              pos=(Window.width * 0.83, Window.height * 0.28),
                                   size=(Window.width * 0.08, Window.height * 0.05), size_hint=(None, None))
        ph_button.bind(on_press=self.backend.next_game_state)
        ph_button.bind(on_press=Clock.schedule_once(self.update_timer,))
        duration = 10
        ph_button.bind(on_press=partial(self.start_timer, duration))
        self.layout.add_widget(ph_button)

        # Button for end of turn
        eot_button = Button(text="Передать", disabled=False,
                           pos=(Window.width * 0.91, Window.height * 0.28),
                           size=(Window.width * 0.08, Window.height * 0.05), size_hint=(None, None))
        self.layout.add_widget(eot_button)

        self.timer_label = Label()
        Clock.schedule_once(lambda x: self.start_timer(5), 1)  # BUGGY?

        # Extra zones sliders
        self.dop_zone_1 = ScrollView(bar_pos_x='top', always_overscroll=False, do_scroll_x=False,
                                     size=(CARD_X_SIZE, Window.height*0.45), size_hint=(None, None), pos=(Window.width * 0.85, Window.height * 0.43))
        self.dop_zone_2 = ScrollView(bar_pos_x='top', always_overscroll=False, do_scroll_x=False,
                                     size=(CARD_X_SIZE, Window.height*0.45), size_hint=(None, None), pos=(Window.width * 0.01, Window.height * 0.43))
        self.dop_zone_1_gl = GridLayout(cols=1, size_hint=(1, None), row_default_height=CARD_Y_SIZE)
        self.dop_zone_2_gl = GridLayout(cols=1, size_hint=(1, None), row_default_height=CARD_Y_SIZE)
        self.dop_zone_1_gl.bind(minimum_height=self.dop_zone_1_gl.setter('height'))
        self.dop_zone_2_gl.bind(minimum_height=self.dop_zone_2_gl.setter('height'))
        self.dop_zone_1.add_widget(self.dop_zone_1_gl)
        self.dop_zone_2.add_widget(self.dop_zone_2_gl)
        self.dop_zone_1_buttons = []
        self.dop_zone_2_buttons = []
        self.dz1_btn = Button(text='Доп.Зона', size_hint=(None, None), size=(Window.width*0.12, Window.height * 0.04),
                                 pos=(Window.width * 0.84, Window.height * 0.88))
        self.dz2_btn = Button(text='Доп.Зона', size_hint=(None, None), size=(Window.width * 0.12, Window.height * 0.04),
                              pos=(Window.width * 0.01, Window.height * 0.88))
        self.dz1_btn.bind(on_press=partial(self.hide_scroll, self.dop_zone_1))
        self.dz2_btn.bind(on_press=partial(self.hide_scroll, self.dop_zone_2))

        root.add_widget(self.dop_zone_1)
        root.add_widget(self.dop_zone_2)
        root.add_widget(self.dz1_btn)
        root.add_widget(self.dz2_btn)

        # timeout otherwise some parts are not rendered
        self.reveal_cards(self.backend.input_cards1)
        self.reveal_cards(self.backend.input_cards2)
        #Clock.schedule_once(lambda x: self.reveal_cards(self.backend.input_cards1))
        #Clock.schedule_once(lambda x: self.reveal_cards(self.backend.input_cards2)
        return root



