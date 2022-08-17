import os
import socket
import threading
import socketserver
import pickle
import network

class MyTCPHandler(socketserver.BaseRequestHandler):

    def handle(self):
        # self.request is the TCP socket connected to the client
        self.data = self.request.recv(8192).strip()
        print(self.data)
        if self.data.decode().startswith('get_waiting_clients'):
            data = [(x[0], self.server.clients[x[0][0]]) for x in self.server.waiting_clients]
            print('data: ', data)
            clients_b = pickle.dumps(data)
            self.request.sendall(clients_b)
        elif self.data.decode().startswith('start_waiting'):
            if not self.client_address[0] in self.server.waiting_clients:
                self.server.waiting_clients.append((self.client_address, self.request))
        elif self.data.decode().startswith('client_left'):
            print('here', self.server.waiting_clients, self.client_address)
            try:
                del self.server.clients[self.client_address[0]]
                for el in self.server.waiting_clients:
                    if el[0][0] == self.client_address[0]:
                        self.server.waiting_clients.remove(el)
            except:
                pass
        elif self.data.decode().startswith('joining'):
            self.server.clients[self.client_address[0][0]] = self.data[7:]
        elif self.data.decode().startswith('start_game'):
            ip = self.data[10:].decode('utf-8')
            for el in self.server.waiting_clients:
                if el[0][0] == self.client_address[0]:
                    sock = el[1]
            print('sock: ', sock)
            sock.sendall(b'start!')



class MainServer:

    def __init__(self):
        HOST, PORT = socket.gethostname(), 12345
        print(socket.gethostbyname(HOST), PORT)
        self.server = socketserver.TCPServer((HOST, PORT), MyTCPHandler)
        self.clients = {}
        self.waiting_clients = []
        self.server.clients = self.clients
        self.server.waiting_clients = self.waiting_clients

    def start(self):
        self.server.serve_forever()

if __name__ == "__main__":
    s = MainServer()
    s.start()
