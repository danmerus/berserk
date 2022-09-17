import os
import socket
import threading
import socketserver
import pickle
import network
import random
from collections import defaultdict
import game

class MainHandler(socketserver.BaseRequestHandler):

    def handle(self):
        # self.request is the TCP socket connected to the client
        self.data = self.request.recv(8192).strip()
        print(self.data.decode())
        if self.data.decode().startswith('get_waiting_clients'):
            data = [(x[0][0], self.server.clients[x[0][0]]) for x in self.server.waiting_clients]  # ip, nickname (from dict)
            clients_b = pickle.dumps(data)
            self.request.sendall(clients_b)
        elif self.data.decode().startswith('start_waiting'):
            if not self.client_address[0] in [x[0][0] for x in self.server.waiting_clients]:
                self.server.waiting_clients.append((self.client_address, self.data[13:]))  # ((ip, port), b'listening_ip+listening_port' of a client)
        elif self.data.decode().startswith('client_left'):
            try:
                del self.server.clients[self.client_address[0]]
                for el in self.server.waiting_clients:
                    if el[0][0] == self.client_address[0]:
                        self.server.waiting_clients.remove(el)
            except Exception as e:
                print("client_left exc ", e)
        elif self.data.decode().startswith('joining'):
            self.server.clients[self.client_address[0]] = self.data[7:]
        elif self.data.decode().startswith('accept_game'):
            ip_accepter, port_accepter, ip_joiner = self.data[len('accept_game'):].decode('utf-8').split('#')
            # print('self.server.waiting_clients: ', self.server.waiting_clients, ip_accepter, port_accepter, ip_joiner)
            for el in self.server.waiting_clients:
                if el[0][0] == ip_joiner:
                    ip_creater, port_creater = el[1].decode('utf-8').split('#')
            # print('creater: ', ip_creater, port_creater)
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s1:
                s1.connect((ip_creater, int(port_creater)))
                game_id = self.server.get_game_id()
                s1.sendall(str(game_id).encode('utf-8'))
            # print('accepter: ', ip_accepter, port_accepter)
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s1:
                s1.connect((ip_accepter, int(port_accepter)))
                s1.sendall(str(game_id).encode('utf-8'))
        elif self.data.decode().startswith('start_constr'):
            ip_, port_, game_id = self.data[len('start_constr'):].decode('utf-8').split('#')
            self.server.game_id_ip_dict[game_id].append((ip_, port_, self.server.clients[self.client_address[0]]))
            if len(self.server.game_id_ip_dict[game_id]) == 2:
                print(f'game {game_id} sobrana!')
                ip1, port1, nick1 = self.server.game_id_ip_dict[game_id][0]
                ip2, port2, nick2 = self.server.game_id_ip_dict[game_id][1]
                gs = GameServer(game_id, ip1, port1, ip2, port2, nick1, nick2)
                t = threading.Thread(target=gs.start, args=(), daemon=True)
                t.start()
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s1:
                    s1.connect((ip1, int(port1)))
                    s1.sendall(b'game_server'+(str(gs.turn_rng) +'#'+gs.server_address[0]+'#'+str(gs.server_address[1])).encode('utf-8'))
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s1:
                    s1.connect((ip2, int(port2)))
                    s1.sendall(b'game_server'+(str(3-gs.turn_rng) +'#'+gs.server_address[0]+'#'+str(gs.server_address[1])).encode('utf-8'))


class GameHandler(socketserver.BaseRequestHandler):

    def handle(self):
        self.data = self.request.recv(65536).strip()
        print('Game_server:', len(self.data), self.data)
        if self.data.startswith(b'next_screen'):
            ip, port, turn = self.data[len('next_screen'):].decode('utf-8').split('#')
            turn = int(turn)
            ip1, port1, nick1 = self.server.player1
            ip2, port2, nick2 = self.server.player2
            if (turn == 2 and self.server.turn_rng==1) or (turn == 1 and self.server.turn_rng==2):
               with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s1:
                   s1.connect((ip2, int(port2)))
                   s1.sendall(b'close')
               self.server.player2 = (ip, port, nick2)
            elif (turn == 1 and self.server.turn_rng==1) or (turn == 2 and self.server.turn_rng==2):
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s1:
                    s1.connect((ip1, int(port1)))
                    s1.sendall(b'close')
                self.server.player1 = (ip, port, nick1)
        elif self.data.startswith(b'placement_ready'):
            turn = int(self.data[len('placement_ready'):len('placement_ready') + 1].decode('utf-8'))
            card_data = self.data[len('placement_ready')+1:]
            ip1, port1, nick1 = self.server.player1
            ip2, port2, nick2 = self.server.player2
            self.server.ready_count.add(turn)
            if (turn == 2 and self.server.turn_rng == 1) or (turn == 1 and self.server.turn_rng == 2):
                try:
                    self.server.player2_cards = pickle.loads(card_data)
                except:
                    print('error in decoding card data!')
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s1:
                    s1.connect((ip1, int(port1)))
                    s1.sendall(b'ready' + nick2)
            elif (turn == 1 and self.server.turn_rng == 1) or (turn == 2 and self.server.turn_rng == 2):
                try:
                    self.server.player1_cards = pickle.loads(card_data)
                except:
                    print('error in decoding card data!')
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s1:
                    s1.connect((ip2, int(port2)))
                    s1.sendall(b'ready' + nick1)
            if len(self.server.ready_count) == 2:
                self.server.game.set_cards(self.server.player1_cards, self.server.player2_cards, self.server.game)
                self.server.ready_count = set()
                if self.server.turn_rng == 1:
                    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s1:
                        s1.connect((ip1, int(port1)))
                        s1.sendall(b'start_constr')
                    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s1:
                        s1.connect((ip2, int(port2)))
                        s1.sendall(b'start_constr')
                elif self.server.turn_rng == 2:
                    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s1:
                        s1.connect((ip1, int(port1)))
                        s1.sendall(b'start_constr')
                    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s1:
                        s1.connect((ip2, int(port2)))
                        s1.sendall(b'start_constr')
        elif self.data.startswith(b'eot_pressed'):
            turn = self.data[len('eot_pressed'):len('eot_pressed')+1].decode('utf-8')
            turn = int(turn)
            self.server.game.eot_clicked()
        elif self.data.startswith(b'ph_pressed'):
            turn = self.data[len('ph_pressed'):len('ph_pressed')+1].decode('utf-8')
            turn = int(turn)
            self.server.game.ph_clicked()
        elif self.data.startswith(b'ability_clicked'):
            turn, ix = self.data[len('ability_clicked'):].decode('utf-8').split('#')
            ix = int(ix)
            turn = int(turn)
            self.server.game.ability_clicked(ix, turn)
        elif self.data.startswith(b'get_roll'):
            count = self.data[len('get_roll'):].decode('utf-8')
            count = int(count)
            if not self.server.rolls or len(self.server.rolls) != count:
                self.server.rolls = []
                for _ in range(count):
                    self.server.rolls.append(random.randint(1, 7))
            data = pickle.dumps(self.server.rolls)
            self.server.sent_rolls += 1
            self.request.sendall(data)
            if self.server.sent_rolls == 2:
                self.server.sent_rolls = 0
                self.server.rolls = []
        elif self.data.startswith(b'client_loaded'):
            turn = self.data[len('client_loaded'):].decode('utf-8')
            turn = int(turn)
            self.server.ready_count.add(turn)
            if len(self.server.ready_count) == 2:
                self.server.game.on_load()
        elif self.data.startswith(b'card_clicked'):
            turn, card_id = self.data[len('card_clicked'):].decode('utf-8').split('#')
            turn = int(turn)
            card_id = int(card_id)
            self.server.game.card_clicked(card_id, turn)
        elif self.data.startswith(b'mark_clicked'):
            turn = self.data[len('mark_clicked'):len('mark_clicked')+1].decode('utf-8')
            turn = int(turn)
            mark_data = pickle.loads(self.data[len('mark_clicked')+1:])
            self.server.game.mark_clicked(mark_data, turn)
        elif self.data.startswith(b'timer_completed'):
            turn = self.data[len('timer_completed'):].decode('utf-8')
            # turn = int(turn)
            self.server.game.timer_completed()
        elif self.data.startswith(b'pop_up_clicked'):
            ix, type_ = self.data[len('pop_up_clicked'):].decode('utf-8').split('#')
            ix = int(ix)
            self.server.game.pop_up_clicked(ix, type_)


class GameServer:
    def __init__(self, game_id, ip1, port1, ip2, port2, nick1='Унгар1', nick2='Унгар1'):
        HOST = socket.gethostname()
        self.server = socketserver.TCPServer(("", 0), GameHandler)
        print(f'starting game {game_id} on: ', self.server.server_address)
        self.server_address = self.server.server_address
        self.game = game.Game(server=self, server_ip=self.server_address[0], server_port=self.server_address[1])
        self.server.game = self.game
        self.server.game.mode = 'online'
        self.game_id = game_id
        self.turn_rng = random.randint(1, 2)
        self.server.turn_rng = self.turn_rng
        self.player1 = (ip1, port1, nick1)
        self.player2 = (ip2, port2, nick2)
        self.server.player1 = self.player1
        self.server.player2 = self.player2
        self.ready_count = set()
        self.server.ready_count = self.ready_count
        self.player1_cards = []
        self.player2_cards = []
        self.server.player1_cards = self.player1_cards
        self.server.player2_cards = self.player2_cards
        self.server.sent_rolls = 0
        self.server.rolls = []

    def end_game(self, text):
        ip1, port1, nick1 = self.server.player1
        ip2, port2, nick2 = self.server.player2
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s1:
            s1.connect((ip1, int(port1)))
            s1.sendall(b'end_game' + (str(text)).encode())
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s1:
            s1.connect((ip2, int(port2)))
            s1.sendall(b'end_game' + (str(text)).encode())

    def send_state(self, player, state_obj):
        data = pickle.dumps(state_obj)
        ip1, port1, nick1 = self.server.player1
        ip2, port2, nick2 = self.server.player2
        if self.turn_rng == 1 and player == 1:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s1:
                s1.connect((ip1, int(port1)))
                s1.sendall(b'state_obj'+data)
        elif self.turn_rng == 1 and player == 2:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s1:
                s1.connect((ip2, int(port2)))
                s1.sendall(b'state_obj'+data)
        elif self.turn_rng == 2 and player == 1:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s1:
                s1.connect((ip2, int(port2)))
                s1.sendall(b'state_obj'+data)
        elif self.turn_rng == 2 and player == 2:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s1:
                s1.connect((ip1, int(port1)))
                s1.sendall(b'state_obj' + data)



    def start(self):
        self.server.serve_forever()

class MainServer:

    def __init__(self, port=None):
        if port:
            HOST, PORT = socket.gethostname(), port
        else:
            HOST = socket.gethostname()
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                s.bind(("", 0))
                PORT = s.getsockname()[1]
        self.HOST = socket.gethostbyname(HOST)
        self.PORT = PORT
        print('starting on: ', socket.gethostbyname(HOST), PORT)
        self.server = socketserver.TCPServer((HOST, PORT), MainHandler)
        self.clients = {}
        self.game_id_ip_dict = defaultdict(list)
        self.waiting_clients = []
        self.curr_game_ids = set()
        self.server.clients = self.clients
        self.server.waiting_clients = self.waiting_clients
        self.server.get_game_id = self.get_game_id
        self.server.game_id_ip_dict = self.game_id_ip_dict

    def get_game_id(self):
        if self.curr_game_ids:
            ret = max(self.curr_game_ids) + 1
            self.curr_game_ids.add(ret)
            return ret
        else:
            self.curr_game_ids.add(0)
            return 0

    def start(self):
        self.server.serve_forever()


if __name__ == "__main__":
    s = MainServer(12345)
    s.start()
