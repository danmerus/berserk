import os
import socket
import socketserver
import pickle
import time
import threading
from kivy.clock import mainthread


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


def start_waiting_helper(sock, parent):
    while True:
        conn, address = sock.accept()
        datachunk = conn.recv(8192)
        if datachunk:
            start_waiting_cb(datachunk, parent)
            sock.close()
            break

@mainthread
def start_waiting_cb(data, parent):
    parent.handle_start_game_response(data.decode('utf-8'))

def start_waiting(host, port, parent, *args):
    res = -1
    # try:

    s2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s2.bind((socket.gethostname(), 0))
    ip, h = s2.getsockname()
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s1:
        # s1.settimeout(100)
        s1.connect((host, int(port)))
        res = s1.sendall(b'start_waiting'+(str(ip)+'#'+str(h)).encode())
    s2.listen(1)
    print('starting loop creater', s2.getsockname())
    t = threading.Thread(target=start_waiting_helper, args=([s2, parent]), daemon=True)
    t.start()
    return res

def accept_game(host, port, parent, ip_to_join, *args):
    res = -1
    try:
        s2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s2.bind((socket.gethostname(), 0))
        ip, h = s2.getsockname()
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s1:
            s1.connect((host, int(port)))
            res = s1.sendall(b'accept_game'+(str(ip)+'#'+str(h)+'#'+str(ip_to_join)).encode())
        s2.listen(1)
        print('starting loop accepter', s2.getsockname())
        t = threading.Thread(target=start_waiting_helper, args=([s2, parent]), daemon=True)
        t.start()
    except Exception as e:
        print(e)
    return res


def start_constr_game(host, port, parent, game_id, *args):
    res = -1
    try:
        s2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s2.bind((socket.gethostname(), 0))
        ip, h = s2.getsockname()
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s1:
            s1.connect((host, int(port)))
            res = s1.sendall(b'start_constr'+(str(ip)+'#'+str(h)+'#'+str(game_id)).encode())
        s2.listen(1)
        t = threading.Thread(target=start_constr_helper, args=([s2, parent]), daemon=True)
        t.start()
    except Exception as e:
        print(e)
    return res

def start_constr_helper(sock, parent):
    while True:
        conn, address = sock.accept()
        datachunk = conn.recv(8192)
        if datachunk.startswith(b'game_server'):
            constr_cb1(datachunk[len('game_server'):], parent)
        elif datachunk.startswith(b'close'):
            break
        elif datachunk.startswith(b'ready'):
            nick = datachunk[len('ready'):].decode('utf-8')
            constr_cb2(nick, parent)
    sock.close()


@mainthread
def constr_cb2(nick, parent):
    parent.on_ready_to_start(nick)

@mainthread
def constr_cb1(data, parent):
    turn, ip, port = data.decode('utf-8').split('#')
    parent.start_for_constra(turn, ip, port)
    # print('got server addr!', data)

def client_left(host, port, *args):
    res = -1
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s1:
            s1.connect((host, int(port)))
            res = s1.sendall(b'client_left')
    except Exception as e:
        print(e)
    return res

def on_entering_placement(host, port, turn, parent, *args):
    res = -1
    try:
        s2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s2.bind((socket.gethostname(), 0))
        ip, h = s2.getsockname()
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s1:
            s1.connect((host, int(port)))
            res = s1.sendall(b'in_placement' + (str(ip)+'#'+str(h)+'#'+str(turn)).encode())
        s2.listen(1)
        t = threading.Thread(target=start_constr_helper, args=([s2, parent]), daemon=True)
        t.start()
    except Exception as e:
        print(e)
    return res

def placement_ready(host, port, turn, data, *args):
    res = -1
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s1:
            s1.connect((host, int(port)))
            byte_data = pickle.dumps(data)
            res = s1.sendall(b'placement_ready'+(str(turn)).encode()+byte_data)
    except Exception as e:
        print(e)
    return res


