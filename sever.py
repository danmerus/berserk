import os
import socket
import threading
import socketserver
import pickle
import network
import random
from collections import defaultdict

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
            print('ip_, port_, game_id ', self.client_address[0], port_, game_id, self.server.clients)
            self.server.game_id_ip_dict[game_id].append((ip_, port_, self.server.clients[self.client_address[0]]))
            if len(self.server.game_id_ip_dict[game_id]) == 2:
                print(f'game {game_id} sobrana!')
                ip1, port1, nick1 = self.server.game_id_ip_dict[game_id][0]
                ip2, port2, nick2 = self.server.game_id_ip_dict[game_id][1]
                gs = GameServer(game_id, ip1, port1, ip2, port2, nick1, nick2)
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s1:
                    s1.connect((ip1, int(port1)))
                    s1.sendall(b'game_server'+(str(gs.turn_rng) +'#'+gs.server_address[0]+'#'+str(gs.server_address[1])).encode('utf-8'))
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s1:
                    s1.connect((ip2, int(port2)))
                    s1.sendall(b'game_server'+(str(3-gs.turn_rng) +'#'+gs.server_address[0]+'#'+str(gs.server_address[1])).encode('utf-8'))


class GameHandler(socketserver.BaseRequestHandler):

    def handle(self):
        pass

class GameServer:
    def __init__(self, game_id, ip1, port1, ip2, port2, nick1='Унгар1', nick2='Унгар1'):
        HOST = socket.gethostname()
        self.server = socketserver.TCPServer((HOST, 0), GameHandler)
        print(f'starting game {game_id} on: ', self.server.server_address)
        self.server_address = self.server.server_address
        self.game_id = game_id
        self.turn_rng = random.randint(1, 2)
        if self.turn_rng == 1:
            self.player1 = (ip1, port1, nick1)
            self.player2 = (ip2, port2, nick2)
        else:
            self.player2 = (ip1, port1, nick1)
            self.player1 = (ip2, port2, nick2)




    def start(self):
        self.server.serve_forever()

class MainServer:

    def __init__(self):
        HOST, PORT = socket.gethostname(), 12345
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
    s = MainServer()
    s.start()
