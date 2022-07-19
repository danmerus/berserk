from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.lang import Builder

Builder.load_string("""
<ButtonsApp>:
    orientation: "vertical"
    Button:
        text: "B1"
        Image:
            source: 'kivy.png'
            y: self.parent.y + self.parent.height - 200
            x: self.parent.x
    Label:
        text: "A label"
""")

class ButtonsApp(App, BoxLayout):
    def build(self):
        return self

if __name__ == "__main__":
    ButtonsApp().run()