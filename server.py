import socket
import sqlite3
from threading import Thread
from Queue import Queue
from Crypto.Hash import SHA256

MAX_CLIENT = 0 #infinite
CLIENTS = Queue(MAX_CLIENT) # ("username",socket)
DB_NAME = "messaging.db"

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

def client_handler(client_sock):
    try:
        user, password = client_sock.recv(1024).split(' ')
    except:
        pass
    client_sock.close()

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
            server.close()
