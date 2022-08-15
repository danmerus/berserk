import os
import pickle

FILEDIRS = ['cards/set_1']

class Library:

    def __init__(self):
        self.cards = {}

    def get_all_cards(self):
        card_names = []
        for filedir in FILEDIRS:
            modules = [f[:-3] for f in os.listdir(filedir) if
                       os.path.isfile(os.path.join(filedir, f)) and f.endswith('.py') and f != '__init__.py']
            card_names.extend([f"{module}" for module in sorted(modules)])
        return card_names

    def populate(self):
        all_cards = self.get_all_cards()
        for card in all_cards:
            self.cards[card] = 6

    def save(self):
        try:
            with open('user_decks/library.blib', 'wb') as f:
                pickle.dump(self.cards, f)
        except:
            pass

    def load(self):
        try:
            with open('user_decks/library.blib', 'rb') as f:
                self.cards = pickle.load(f)
        except:
            pass

    def get_cards(self):
        out = []
        for c_name, count in self.cards.items():
            cls_ = globals()[c_name]
            out.append((cls_(), count))
        return out


class Deck:

    def __init__(self):
        self.cards = []
        self.create_card_mappings()

    def save_deck(self, cards, name):
        txt = ''
        for c in cards:
            code = self.card_num_map[c.__name__]
            txt += f'{code:x}!'
        try:
            with open('user_decks/'+name+'.bdck', 'w') as f:
                f.write(txt)
        except:
            pass

    def load_deck(self, path):
        deck = []
        try:
            with open(path) as f:
                data = f.read()
            for x in data.split('!'):
                if x:
                    code = int(x, 16)
                    cls_ = globals()[self.card_num_map_reversed[code]]
                    deck.append(cls_)
        except:
            pass
        return deck

    def import_deck(self, string_):
        deck = []
        if not string_:
            return []
        for x in string_.split('!'):
            if x:
                try:
                    code = int(x, 16)
                    cls_ = globals()[self.card_num_map_reversed[code]]
                    deck.append(cls_)
                except:
                    pass
        return deck


    def create_card_mappings(self):
        self.card_num_map = {}
        self.card_num_map_reversed = {}
        imports = []
        for filedir in FILEDIRS:
            modules = [f[:-3] for f in os.listdir(filedir) if
                       os.path.isfile(os.path.join(filedir, f)) and f.endswith('.py') and f != '__init__.py']
            imports.extend([f"{module}" for module in sorted(modules)])
        for i, c in enumerate(imports):
            self.card_num_map[c] = i
            self.card_num_map_reversed[i] = c



filedir = 'cards/set_1'
modules = [f[:-3] for f in os.listdir(filedir) if
           os.path.isfile(os.path.join(filedir, f)) and f.endswith('.py') and f != '__init__.py']
imports = [f"from cards.set_1 import {module}\nfrom cards.set_1.{module} import *" for module in sorted(modules)]
for imp in imports:
    exec(imp)

# l = Library()
# l.populate()
# l.save()
# l.load()
# print(l.get_cards())
# print(l.cards)
# klass = globals()["Draks_1"]
# instance = klass()

# d = Deck()
# t = d.save_deck([Lovets_dush_1(), Cobold_1(), Draks_1(), Lovets_dush_1(), Voin_hrama_1(), Draks_1(),
#           Lovets_dush_1(), PovelitelMolniy_1(), Draks_1(),Lovets_dush_1(), PovelitelMolniy_1(), Draks_1(),
#           Lovets_dush_1(), PovelitelMolniy_1(), Draks_1()], 'start')
# print(d.load_deck('user_decks/start.bdck'))