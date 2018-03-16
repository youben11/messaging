import socket
import time
from threading import Thread

ADDR = "127.0.0.1"
PORT = 4848
HOST = (ADDR, PORT)
USERNAME = "youben"
PASSWORD = "123456789"

DELEM_MSG = '~'
DELEM_USER_ADD = "+"
DELEM_USER_LOGIN = "*"
DELEM_STATUS = "#"
DELEM_SEND = "@"
STATUS_ERROR = "%sERROR" % DELEM_STATUS
STATUS_SUCCESS = "%sSUCCESS" % DELEM_STATUS
STATUS_USER_EXISTS = "%sUSER_EXISTS" % DELEM_STATUS
STATUS_WRONG_CREDENTIAL = "%sWRONG_CREDENTIAL" % DELEM_STATUS

def sender(sock):
    while True:
        buf = raw_input()
        sock.send("%s%s%s" % (DELEM_MSG, buf, DELEM_MSG))

def receiver(sock):
    while True:
        buf = sock.recv(4096)
        print "[%d]%s" % (time.time(), buf)

def connect(sock, username, password):
    sock.send("%s%s:%s" % (DELEM_USER_LOGIN, username, password))
    buf = sock.recv(1024)
    if buf.startswith(STATUS_SUCCESS):
        print "[+] Successfully connected"
        return True
    elif buf.startswith(STATUS_WRONG_CREDENTIAL):
        print "[-] Wrong Credentail"
        return False
    elif buf.startswith(STATUS_ERROR):
        print "[-] Error"
        return False

def create_user(sock, usernmae, password):
    sock.send("%s%s:%s" % (DELEM_USER_ADD, username, password))
    buf = sock.recv(1024)
    if buf.startswith(STATUS_SUCCESS):
        print "[+] Successfully added, you are now connected as %s" % username
        return True
    elif buf.startswith(STATUS_USER_EXISTS):
        print "[-] User already exists"
        return False
    elif buf.startswith(STATUS_ERROR):
        print "[-] Error"
        return False

if __name__ == "__main__":
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(HOST)
    connect(sock, USERNAME, PASSWORD)
    sth = Thread(target=sender, args=(sock,))
    rth = Thread(target=receiver, args=(sock,))
    sth.start()
    rth.start()
