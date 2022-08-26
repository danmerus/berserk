import os
import socket
import socketserver
import pickle
import time
import threading
from copy import copy
from kivy.clock import mainthread
import kivy.uix.button


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


################# GAME SERVER ##################################

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


def client_left(host, port, *args):
    res = -1
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s1:
            s1.connect((host, int(port)))
            res = s1.sendall(b'client_left')
    except Exception as e:
        print(e)
    return res

def on_entering_next_screen(host, port, turn, parent, *args):
    res = -1
    try:
        s2 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s2.bind((socket.gethostname(), 0))
        ip, h = s2.getsockname()
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s1:
            s1.connect((host, int(port)))
            res = s1.sendall(b'next_screen' + (str(ip)+'#'+str(h)+'#'+str(turn)).encode())
        s2.listen(5)
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

def timer_pressed(host, port, duration, turn):
    res = -1
    #print('timer pressed!', turn)
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s1:
            s1.connect((host, int(port)))
            res = s1.sendall(b'timer_pressed' + (str(duration)+'#' + str(turn)).encode())
    except Exception as e:
        print(e)
    return res

def ability_to_pickle(ability, card, victim, state, force):
    ability.button = None
    ability1 = copy(ability)
    card1 = copy(card)
    victim1 = copy(victim)
    if isinstance(state, kivy.uix.button.Button):
        state = 0
    if hasattr(victim1, 'id_on_board'):
        v = victim1.id_on_board
    else:
        v = victim1
    print(ability1, card1.id_on_board, v, state, force)
    return pickle.dumps([ability1, card1.id_on_board, v, state, force])

def pickle_to_ability(data, parent):
    ability, card, victim, state, force = pickle.loads(data)
    card = parent.backend.board.get_card_by_id(card)
    try:
        victim = parent.backend.board.get_card_by_id(victim)
    except:
        victim = victim
    return ability, card, victim, state, force


def ability_pressed(host, port, turn, ability, card, victim, state, force):
    res = -1
    # print('ability pressed!', turn)
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s1:
            s1.connect((host, int(port)))
            data = ability_to_pickle(ability, card, victim, state, force)
            byte_data = pickle.dumps(data)
            res = s1.sendall(b'ability_pressed' + (str(turn)).encode() + byte_data)
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
        elif datachunk.startswith(b'start_constr'):
            card_data = datachunk[len('start_constr'):]
            try:
                constr_cb3(pickle.loads(card_data), parent)
            except:
                print('error in decoding cards!')
            print('starting constracted game!')
        elif datachunk.startswith(b'timer_pressed'):
            duration = int(datachunk[len('timer_pressed'):].decode('utf-8'))
            constr_cb4(duration, parent)
        elif datachunk.startswith(b'ability_pressed'):
            byte_data = datachunk[len('ability_pressed'):]
            data = pickle.loads(byte_data)
            constr_cb5(data, parent)

    sock.close()

@mainthread
def constr_cb5(data, parent):
    ability, card, victim, state, force = pickle_to_ability(data, parent)
    print('Launching ability: ', ability, card, victim, state, force)
    parent.start_stack_action(ability, card, victim, state, force, imposed=True)

@mainthread
def constr_cb4(duration, parent):
    parent.start_timer(duration, True)

@mainthread
def constr_cb3(cards, parent):
    parent.on_game_start(cards)

@mainthread
def constr_cb2(nick, parent):
    try:
        parent.on_ready_to_start(nick)
    except:
        pass

@mainthread
def constr_cb1(data, parent):
    turn, ip, port = data.decode('utf-8').split('#')
    parent.start_for_constra(turn, ip, port)
    # print('got server addr!', data)
