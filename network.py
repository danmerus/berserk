import os
import socket
import threading
import socketserver
import pickle
import time
import asyncio
from kivy.clock import mainthread

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

def start_waiting(host, port, *args):
    res = -1
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s1:
            s1.connect((host, int(port)))
            res = s1.sendall(b'start_waiting')
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


