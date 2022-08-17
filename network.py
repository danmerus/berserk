import os
import socket
import threading
import socketserver
import pickle
import time
import threading
from kivy.clock import mainthread


def get_free_port():
    out = 12333
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.bind(('', 0))
        out = s.getsockname()[1]
    return out

@mainthread
def get_waiting_players(host, port, parent, *args):
    res = []
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s1:
            s1.connect((host, int(port)))
            s1.sendall(b'get_waiting_clients')
            data = s1.recv(8192)
            res = pickle.loads(data)
    except Exception as e:
        print(e)
    # time.sleep(4)
    if res:
        parent.update_serverlist_gui(res)

def join_server(host, port, nick, *args):
    res = -1
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s1:
            s1.connect((host, int(port)))
            res = s1.sendall(b'joining'+nick.encode('utf-8'))
    except Exception as e:
        print(e)
    return res

def start_waiting(host, port, *args):
    res = -1
    # try:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s1:
        s1.connect((host, int(port)))
        res = s1.sendall(b'start_waiting')
        # s1.listen()
        # conn, address = s1.accept()
        print('starting loop', s1.getsockname())
        while True:
            datachunk = s1.recv(8192)
            if datachunk:
                print('recieved!:', datachunk)
                break
    # except Exception as e:
    #     print('start_waiting: ', e)
    return res

# def start_waiting_listener(parent):
#     s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
#     s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
#     s.listen(1)
#     conn, address = s.accept()
#     while True:
#         datachunk = conn.recv(8192)
#         if not datachunk:
#             break
#     conn.close()
#     parent.update_serverlist_gui()

def accept_game(host, port, ip, *args):
    res = -1
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s1:
            s1.connect((host, int(port)))
            res = s1.sendall(b'start_game' + ip.encode('utf-8'))
    except Exception as e:
        print(e)
    return res

def client_left(host, port, *args):
    res = -1
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s1:
            s1.connect((host, int(port)))
            res = s1.sendall(b'client_left')
    except Exception as e:
        print(e)
    return res


