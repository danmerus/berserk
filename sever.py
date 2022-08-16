import os
import socket
import threading
import socketserver
import pickle

class MyTCPHandler(socketserver.BaseRequestHandler):

    def handle(self):
        # self.request is the TCP socket connected to the client
        self.data = self.request.recv(8192).strip()
        print(self.data)
        if self.data.decode().startswith('get_waiting_clients'):
            clients_b = pickle.dumps(self.server.clients)
            self.request.sendall(clients_b)
        elif self.data.decode().startswith('start_waiting'):
            if not self.client_address[0] in self.server.clients:
                self.server.clients.append(self.client_address[0])
        elif self.data.decode().startswith('client_left'):
            print('here', self.server.clients, self.client_address)
            self.server.clients.remove(self.client_address[0])


class MainServer:

    def __init__(self):
        HOST, PORT = socket.gethostname(), 12345
        print(HOST, PORT)
        self.server = socketserver.TCPServer((HOST, PORT), MyTCPHandler)
        self.clients = []
        self.server.clients = self.clients

    def start(self):
        self.server.serve_forever()

if __name__ == "__main__":
    s = MainServer()
    s.start()
