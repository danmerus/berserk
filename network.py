import os
import socket
import socketserver
import pickle
import time
import threading
from copy import copy
from kivy.clock import mainthread
import kivy.uix.button
from cards.card_properties import *


def get_waiting_players(host, port, parent, *args):
    res = []
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s1:
            s1.connect((host, int(port)))
            s1.sendall(b'get_waiting_clients')
            data = s1.recv(8192)
            res = pickle.loads(data)
    except Exception as e:
        print('get_waiting_players ', e)
    # time.sleep(4)
    if res:
        get_waiting_players_cb(parent, res)

@mainthread
def get_waiting_players_cb(parent, res):
    parent.update_serverlist_gui(res)

def join_server(host, port, nick, *args):
    res = -1
    client_id = -1
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s1:
            s1.settimeout(5)
            s1.connect((host, int(port)))
            res = s1.sendall(b'joining'+nick.encode('utf-8'))
            client_id = s1.recv(2048).decode('utf-8')
    except Exception as e:
        print('join_server: ', e)
    return res, int(client_id)


def start_waiting_helper(sock, parent):
    while True:
        datachunk = sock.recv(8192)  #  receiving game_id here
        if datachunk:
            start_waiting_cb(datachunk, parent)
            sock.close()
            break

@mainthread
def start_waiting_cb(data, parent):
    parent.handle_start_game_response(data.decode('utf-8'))

def start_waiting(host, port, parent, client_id, *args):
    s1 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s1.connect((host, int(port)))
    s1.sendall(b'start_waiting' + (str(client_id)).encode())
    print('starting loop creater', s1)
    t = threading.Thread(target=start_waiting_helper, args=([s1, parent]), daemon=True)
    t.start()

def accept_game(host, port, parent, self_id, id_to_join, *args):
    try:
        s1 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s1.bind(('', 0))
        s1.connect((host, int(port)))
        t = threading.Thread(target=start_waiting_helper, args=([s1, parent]), daemon=True)
        t.start()
        s1.sendall(b'accept_game'+(str(self_id)+'#'+str(id_to_join)).encode())
        print('starting loop accepter', s1)
    except Exception as e:
        print('accept_game', e)

################################### GAME SERVER ############################################

def start_constr_game(host, port, parent, game_id, client_id, *args):
    try:
        s1 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s1.connect((host, int(port)))
        s1.sendall(b'start_constr'+(str(game_id)+'#'+str(client_id)).encode())
        t = threading.Thread(target=start_constr_helper, args=([s1, parent]), daemon=True)
        t.start()
    except Exception as e:
        print('start_constr_game: ', e)


def client_left(host, port, *args):
    res = -1
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s1:
            s1.settimeout(5)
            s1.connect((host, int(port)))
            res = s1.sendall(b'client_left')
    except Exception as e:
        print('client_left: ', e)
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
        print('on_entering_next_screen: ', e)
    return res


def placement_ready(host, port, turn, data, *args):
    res = -1
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s1:
            s1.connect((host, int(port)))
            byte_data = pickle.dumps(data)
            print('card data length: ', len(byte_data))
            res = s1.sendall(b'placement_ready'+(str(turn)).encode()+byte_data)
    except Exception as e:
        print('placement_ready: ', e)
    return res

def eot_pressed(host, port, turn, *args):
    res = -1
    #print('timer pressed!', turn)
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s1:
            s1.connect((host, int(port)))
            res = s1.sendall(b'eot_pressed' + (str(turn)).encode())
    except Exception as e:
        print('eot_pressed: ', e)
    return res

def ph_pressed(host, port, turn, *args):
    res = -1
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s1:
            s1.connect((host, int(port)))
            res = s1.sendall(b'ph_pressed' + (str(turn)).encode())
    except Exception as e:
        print('ph_pressed: ', e)
    return res

def timer_completed(host, port, turn, *args):
    res = -1
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s1:
            s1.connect((host, int(port)))
            res = s1.sendall(b'timer_completed' + (str(turn)).encode())
    except Exception as e:
        print('timer_completed: ', e)
    return res

def pop_up_clicked(host, port, turn, ix, type_, *args):
    res = -1
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s1:
            s1.connect((host, int(port)))
            res = s1.sendall(b'pop_up_clicked' + (str(ix)+'#'+str(type_)).encode())
    except Exception as e:
        print('pop_up_clicked: ', e)
    return res

def client_loaded(host, port, turn, *args):
    res = -1
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s1:
            s1.connect((host, int(port)))
            res = s1.sendall(b'client_loaded' + (str(turn)).encode())
    except Exception as e:
        print('client_loaded: ', e)
    return res

def card_clicked(host, port, turn, card, *args):
    res = -1
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s1:
            s1.connect((host, int(port)))
            res = s1.sendall(b'card_clicked' + (str(turn)+'#'+str(card)).encode())
    except Exception as e:
        print('card_clicked: ', e)
    return res

def mark_clicked(host, port, turn, marks, *args):
    res = -1
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s1:
            marks_data = pickle.dumps(marks)
            s1.connect((host, int(port)))
            res = s1.sendall(b'mark_clicked' + (str(turn)).encode() + marks_data)
    except Exception as e:
        print('mark_clicked: ', e)
    return res

def ability_clicked(host, port, turn, ix, *args):
    res = -1
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s1:
            s1.connect((host, int(port)))
            res = s1.sendall(b'ability_clicked' + (str(turn)+'#'+str(ix)).encode())
    except Exception as e:
        print('ability_clicked: ', e)
    return res

def get_rolls(host, port, count):
    res = -1
    # print('ability pressed!', turn)
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s1:
            s1.connect((host, int(port)))
            s1.sendall(b'get_roll' + (str(count)).encode())
            data = s1.recv(8192)
            res = pickle.loads(data)
    except Exception as e:
        print('get_rolls: ', e)
    return res


def start_constr_helper(sock, parent):
    while True:
        datachunk = sock.recv(8192)
        if datachunk.startswith(b'game_server'):
            constr_cb1(datachunk[len('game_server'):], parent)
        elif datachunk.startswith(b'close'):
            break
        elif datachunk.startswith(b'ready'):
            nick = datachunk[len('ready'):].decode('utf-8')
            constr_cb2(nick, parent)
        elif datachunk.startswith(b'start_constr'):
            constr_cb3(parent)
            print('starting constracted game!')
        elif datachunk.startswith(b'eot_pressed'):
            constr_cb4(parent)
        elif datachunk.startswith(b'ph_pressed'):
            constr_cb6(parent)
        elif datachunk.startswith(b'ability_pressed'):
            byte_data = datachunk[len('ability_pressed'):]
            data = pickle.loads(byte_data)
            # constr_cb5(data, parent)
        elif datachunk.startswith(b'state_obj'):
            byte_data = datachunk[len('state_obj'):]
            data = pickle.loads(byte_data)
            constr_cb7(data, parent)
        elif datachunk.startswith(b'end_game'):
            txt = datachunk[len('end_game'):].decode('utf-8')
            constr_cb8(txt, parent)

    sock.close()

@mainthread
def constr_cb8(txt, parent):
    parent.on_game_end(txt)


@mainthread
def constr_cb7(state, parent):
    # print('Sending state: ', state)
    parent.on_state_received(state)

# @mainthread
# def constr_cb5(data, parent):
#     ability, card, victim, state, force = pickle_to_ability(data, parent)
#     print('Launching ability: ', ability, card, victim, state, force)
#     parent.start_stack_action(ability, card, victim, state, force, imposed=True)

@mainthread
def constr_cb6(parent):
    parent.on_online_press_skip()

@mainthread
def constr_cb4(parent):
    parent.on_online_press_turn()

@mainthread
def constr_cb3(parent):
    parent.on_game_start()

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
    print('got server addr!', data)
