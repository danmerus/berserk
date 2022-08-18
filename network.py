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

# @mainthread
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
        get_waiting_players_cb(parent, res)

@mainthread
def get_waiting_players_cb(parent, res):
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

# @mainthread
def start_waiting_helper(sock):
    while True:
        conn, address = sock.accept()
        datachunk = conn.recv(8192)
        if datachunk:
            # print('recieved!:', datachunk)
            start_waiting_cb(datachunk)
            sock.close()
            break

@mainthread
def start_waiting_cb(data):
    print('recieved!:', data)

def start_waiting(host, port, *args):
    res = -1
    # try:

    s2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s2.bind(('', 0))
    ip, h = s2.getsockname()
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s1:
        # s1.settimeout(100)
        s1.connect((host, int(port)))
        res = s1.sendall(b'start_waiting'+str(h).encode())
    s2.listen(1)
    print('starting loop', s2.getsockname())
    t = threading.Thread(target=start_waiting_helper, args=([s2]), daemon=True)
    t.start()
    # while True:
    #     conn, address = s2.accept()
    #     datachunk = conn.recv(8192)
    #     if datachunk:
    #         print('recieved!:', datachunk)
    #         s2.close()
    #         break
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
            res = s1.sendall(b'start_game' + str(ip).encode('utf-8'))
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


