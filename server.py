import socket
import re
import time
from threading import Thread
from Queue import Queue
from DB import *
from messaging_proto import *

MAX_CLIENT = 0 #infinite
CLIENTS = Queue(MAX_CLIENT) # username
CLIENTS_SOCKETS = dict() # "usename": socket

SLEEP_T = 0.5 #time to sleep to wait data
BYTE_R = 1024 #number of byte per recv
NUM_TH = 2 #number of working threads
TH_FLAGS = [1 for i in range(NUM_TH)]
TH_END = "##END##"

ADDR = "0.0.0.0"
PORT = 4848
BINDING = (ADDR, PORT)


def read(sock, ntry):
    sock.settimeout(SLEEP_T)
    buf = []
    found = False
    while ntry:
        try:
            r = sock.recv(BYTE_R)
            if not len(r):
                return None #socket closed
            buf.extend(list(r))
            found = True
            continue
        except socket.timeout as st:
            if found:
                return "".join(buf)
        ntry -= 1
    return "".join(buf)

def client_handler(client_sock):
    buf = read(client_sock, 100)
    if buf == None: #socket closed
        client_sock.shutdown(socket.SHUT_RDWR)
        return None
    if not len(buf):
        client_sock.shutdown(socket.SHUT_RDWR)
        return None
    if buf[0] == DELEM_USER_ADD:
        add_user(client_sock,buf[1:])
    elif buf[0] == DELEM_USER_LOGIN:
        login_user(client_sock, buf[1:])
    else:
        client_sock.send(STATUS_ERROR)
        client_sock.shutdown(socket.SHUT_RDWR)

def add_user(client_sock, user_pass):
    if re.match(re_user_password, user_pass):
        username, password = user_pass.split(":")
        db = DB()
        if db.add_user(username, password):
            client_sock.send(STATUS_SUCCESS)
            print "[%d] User %s created from %s:%d" % ((time.time(), username) + client_sock.getpeername())
            CLIENTS.put(username)
            CLIENTS_SOCKETS[username] = client_sock
        else:
            client_sock.send(STATUS_USER_EXISTS)
            client_sock.shutdown(socket.SHUT_RDWR)
    else:
        client_sock.send(STATUS_ERROR)
        client_sock.shutdown(socket.SHUT_RDWR)

def login_user(client_sock, user_pass):
    if re.match(re_user_password, user_pass):
        username, password = user_pass.split(":")
        db = DB()
        if db.match_user(username, password):
            client_sock.send(STATUS_SUCCESS)
            print "[%d] User %s is on %s:%d" % ((time.time(), username) + client_sock.getpeername())
            CLIENTS.put(username)
            CLIENTS_SOCKETS[username] = client_sock
        else:
            client_sock.send(STATUS_WRONG_CREDENTIAL)
            client_sock.shutdown(socket.SHUT_RDWR)
    else:
        client_sock.send(STATUS_ERROR)
        client_sock.shutdown(socket.SHUT_RDWR)

def server_thread(th_num):
    while True:
        if not TH_FLAGS[th_num]:
            print "[*] Thread%d ending..." % (th_num + 1)
            exit()
        username = CLIENTS.get()
        try:
            client_sock = CLIENTS_SOCKETS[username]
        except:
            if username == TH_END:
                CLIENTS.put(TH_END)
                continue
        buf = read(client_sock, 1)
        if buf == None: #socket closed
            CLIENTS_SOCKETS.pop(username).shutdown(socket.SHUT_RDWR)
            continue
        buf = buf.split('~')
        for msg in buf:
            if len(msg):
                print "[%d] Message from %s: %s" % (time.time(), \
                                                    username, \
                                                    msg)
                packet_to_send = ("%s%s%s%s%s" % (DELEM_SEND, \
                                                    username, \
                                                    DELEM_MSG, \
                                                    msg, \
                                                    DELEM_MSG))
                for u in CLIENTS_SOCKETS.keys():
                    try:
                        CLIENTS_SOCKETS[u].send(packet_to_send)
                    except:
                        CLIENTS_SOCKETS.pop(username).shutdown(socket.SHUT_RDWR)
        CLIENTS.put(username)


if __name__ == "__main__":
    #INIT DB
    db = DB()
    db.init_db()
    #INIT socket
    server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server.bind(BINDING)
    server.listen(5)
    #Create threads to handle incoming messages
    server_ths = [Thread(target=server_thread, args=(i,)) for i in range(NUM_TH)]
    for th in server_ths:
        th.start()

    print "[+] Server Started."
    print "[+] Listening on %s:%d" % BINDING
    while True:
        try:
            client_sock, client_addr = server.accept()
            print "[%d] Connection From %s:%d" % ((time.time(),) + client_addr)
            th = Thread(target=client_handler, args=(client_sock,))
            th.start()
        except socket.error:
            continue
        except KeyboardInterrupt:
            CLIENTS.put(TH_END)
            for i in range(NUM_TH): #signal to threads to end
                TH_FLAGS[i] = 0
                server_ths[i].join()
            for s in CLIENTS_SOCKETS.values():
                try:
                    s.shutdown(socket.SHUT_RDWR)
                except:
                    pass
            print "[*] Server Stopped."
            server.shutdown(socket.SHUT_RDWR)
            exit()
