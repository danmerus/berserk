# import upnpclient
# devices = upnpclient.discover()
# d = devices[0]
# d.WANIPConnection.AddPortMapping(
#     NewRemoteHost='0.0.0.0',
#     NewExternalPort=12345,
#     NewProtocol='TCP',
#     NewInternalPort=12345,
#     NewInternalClient='192.168.1.10',
#     NewEnabled='1',
#     NewPortMappingDescription='Testing',
#     NewLeaseDuration=10000)
import socket

HOST = "185.237.96.75"
PORT = 12345

with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.bind((HOST, PORT))
    s.listen()
    conn, addr = s.accept()
    with conn:
        print(f"Connected by {addr}")
        while True:
            data = conn.recv(1024)
            if not data:
                break
            conn.sendall(data)