import socket
import sqlite3
import re
import time
from threading import Thread
from Queue import Queue
from Crypto.Hash import SHA256

MAX_CLIENT = 0 #infinite
CLIENTS = Queue(MAX_CLIENT) # username
CLIENTS_SOCKETS = dict() # "usename": socket
DB_NAME = "messaging.db"

re_user_password = r"^[a-zA-Z]\w{1,19}:\S{8,15}$"

SLEEP_T = 0.5 #time to sleep to wait data
BYTE_R = 1024 #number of byte per recv
NUM_TH = 2 #number of working threads

DELEM_MSG = '~'
DELEM_USER_ADD = "+"
DELEM_USER_LOGIN = "*"
DELEM_STATUS = "#"
DELEM_SEND = "@"
STATUS_ERROR = "%sERROR" % DELEM_STATUS
STATUS_SUCCESS = "%sSUCCESS" % DELEM_STATUS
STATUS_USER_EXISTS = "%sUSER_EXISTS" % DELEM_STATUS
STATUS_WRONG_CREDENTIAL = "%sWRONG_CREDENTIAL" % DELEM_STATUS

ADDR = "0.0.0.0"
PORT = 4848
BINDING = (ADDR, PORT)

class DB(object):
    CREATE_TABLE = "CREATE TABLE IF NOT EXISTS USERS(username text PRIMARY KEY, password text);"
    INSERT_USER = "INSERT INTO USERS VALUES (?, ?);"
    SELECT_USER = "SELECT * from USERS where username= ?;"
    SELECT_USER_WITH_PASS = "SELECT * from USERS where username= ? and password= ?;"

    def __init__(self, db_name=DB_NAME):
        self.db_name = db_name
        self.conn = sqlite3.connect(self.db_name)

    def init_db(self):
        cur = self.conn.cursor()
        cur.execute(DB.CREATE_TABLE)
        self.conn.commit()

    def add_user(self, username, password):
        #hashing the password
        h = SHA256.new()
        h.update(password)
        password = h.hexdigest()
        #try to insert the user
        cur = self.conn.cursor()
        try:
            cur.execute(DB.INSERT_USER, (username, password))
            self.conn.commit()
            return True
        except sqlite3.IntegrityError as ie: #the user already exists
            return False

    def match_user(self, username, password):
        #hashing the password
        h = SHA256.new()
        h.update(password)
        password = h.hexdigest()
        #try to find the user
        cur = self.conn.cursor()
        cur.execute(DB.SELECT_USER_WITH_PASS, (username, password))
        if cur.fetchone(): # the user exists
            return True
        else:
            return False

    def close(self):
        self.conn.close()

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
        client_sock.close()
        return None
    if not len(buf):
        client_sock.close()
        return None
    if buf[0] == DELEM_USER_ADD:
        add_user(client_sock,buf[1:])
    elif buf[0] == DELEM_USER_LOGIN:
        login_user(client_sock, buf[1:])
    else:
        client_sock.send(STATUS_ERROR)
        client_sock.close()

def add_user(client_sock, user_pass):
    if re.match(re_user_password, user_pass):
        username, password = user_pass.split(":")
        db = DB()
        if db.add_user(username, password):
            client_sock.send(STATUS_SUCCESS)
            CLIENTS.put(username)
            CLIENTS_SOCKETS[username] = client_sock
        else:
            client_sock.send(STATUS_USER_EXISTS)
            client_sock.close()
    else:
        client_sock.send(STATUS_ERROR)
        client_sock.close()

def login_user(client_sock, user_pass):
    if re.match(re_user_password, user_pass):
        username, password = user_pass.split(":")
        db = DB()
        if db.match_user(username, password):
            client_sock.send(STATUS_SUCCESS)
            CLIENTS.put(username)
            CLIENTS_SOCKETS[username] = client_sock
        else:
            client_sock.send(STATUS_WRONG_CREDENTIAL)
            client_sock.close()
    else:
        client_sock.send(STATUS_ERROR)
        client_sock.close()

def server_thread():
    while True:
        username = CLIENTS.get()
        client_sock = CLIENTS_SOCKETS[username]
        buf = read(client_sock, 1)
        if buf == None: #socket closed
            CLIENTS_SOCKETS.pop(username).close()
            continue
        buf = buf.split('~')
        for msg in buf:
            if len(msg):
                print "[%d]Message from %s: %s" % (time.time(), \
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
                        CLIENTS_SOCKETS.pop(username).close()
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
    server_ths = [Thread(target=server_thread) for i in range(NUM_TH)]
    for th in server_ths:
        th.start()

    print "[+] Server Started."
    print "[+] Listening on %s:%d" % BINDING
    while True:
        try:
            client_sock, client_addr = server.accept()
            print "[+] Connection From %s:%d" % client_addr
            th = Thread(target=client_handler, args=(client_sock,))
            th.start()
        except: # keyboard inerrupt or something
            for s in CLIENTS_SOCKETS.values():
                s.close()
            server.close()
