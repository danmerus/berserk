from kivymd.app import MDApp
from kivy.uix.screenmanager import Screen, ScreenManager
from kivy.lang import Builder

KV = '''
<home>:
    progression_value:25

    BoxLayout:
        orientation:'vertical'
        padding:dp(24),0,dp(24),0
        Widget:

        MDProgressBar:
            value: root.progression_value
            color: 0,0,0,0
            size_hint_y:None
            height:dp(48)                                   
            canvas:

                Color:
                    rgba:1,1,0,1
                BorderImage:
                    border: (dp(48), dp(48), dp(48), dp(48))
                    pos: self.x, self.center_y - dp(24)
                    size: self.width, dp(48)
                Color:
                    rgba:1,0,0,1                        
                BorderImage:
                    border: [int(min(self.width * (self.value / float(self.max)) if self.max else 0, dp(48)))] * 4
                    pos: self.x, self.center_y -dp(24)
                    size: self.width * (self.value / float(self.max)) if self.max else 0, dp(48)

        Widget:            
'''


class home(Screen):
    pass


class Test(MDApp):
    def build(self):
        Builder.load_string(KV)
        self.sm = ScreenManager()
        self.sm.add_widget(home(name="home"))

        return self.sm


Test().run()