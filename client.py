import socket
import time
import re
import signal
from sys import argv
from threading import Thread
from messaging_proto import *
from Queue import Queue


HELP = """[+] Usage:
            %s connect username password server_ip [server_port]
            %s create username password server_ip [server_port]

[*] usernmae: alphanumeric, 2 to 20 character (must begin with a letter)
[*] password: 8 to 15 characters
"""

re_cmd = r"^(connect|create) [a-zA-Z]\w{1,19} \S{8,15} ((25[0-5]|2[0-4][0-9]|1[0-9]{2}|[1-9]?[0-9])\.){3}(25[0-5]|2[0-4][0-9]|1[0-9]{2}|[1-9]?[0-9])( \d+)?$"

CMD_CONNECT = "connect"
CMD_CREATE = "create"

TH_FLAGS = [1,1]
SENDER = 0
RECEIVER = 1
MSG_Q = Queue()
MSG_END = "#END#"

DEFAULT_PORT = 4848

def sender(sock):
    while True:
        try:
            # get msg from a queue instead of stdin
            msg = MSG_Q.get()
            if not TH_FLAGS[SENDER]:
                exit()
            msg = msg.replace("~","&(tilde)")
            sock.send("%s%s%s" % (DELEM_MSG, msg, DELEM_MSG))
        except socket.error:
            print "[-] Connection lost..."
            print "[*] Sender Stopped."
            exit()
        except KeyboardInterrupt:
            exit()

def receiver(sock):
    while True:
        sock.settimeout(0.5)
        try:
            buf = sock.recv(4096)
            if not TH_FLAGS[RECEIVER]:
                exit()
            if not len(buf):
                print "[-] Connection lost..."
                print "[*] Receiver Stopped."
                TH_FLAGS[SENDER] = 0
                exit()
        except socket.timeout as st:
            if not TH_FLAGS[RECEIVER]:
                exit()
            continue
        messages = re.findall(r'@(\w+)~([^~]+)~', buf)
        for sender, message in messages:
            message = message.replace("&(tilde)","~")
            #print it using a curse func
            print "[%s] %s: %s" % (time.asctime().split()[3], sender, message)

def connect(sock, username, password):
    sock.send("%s%s:%s" % (DELEM_USER_LOGIN, username, password))
    buf = sock.recv(1024)
    if buf.startswith(STATUS_SUCCESS):
        print "[+] Successfully connected as %s" % username
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
    if len(argv) not in [5,6]:
        print HELP % (argv[0], argv[0])
        exit()
    if not re.match(re_cmd, " ".join(argv[1:])):
        print HELP % (argv[0], argv[0])
        exit()
    username, password = argv[2:4]
    if len(argv) == 5:
        host = argv[4], DEFAULT_PORT
    else:
        host = argv[4], int(argv[5])

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(host)
    if argv[1] == CMD_CONNECT:
        if not connect(sock, username, password):
            exit()
    elif argv[1] == CMD_CREATE:
        if not create_user(sock, username, password):
            exit()
    else:
        print HELP % (argv[0], argv[0])
        exit()
    sth = Thread(target=sender, args=(sock,))
    rth = Thread(target=receiver, args=(sock,))
    sth.start()
    rth.start()
    #call a draw() func and exit only when it returns
    try:
        while True:
            buf = raw_input()
            MSG_Q.put(buf)
    except KeyboardInterrupt:
        sock.shutdown(socket.SHUT_RDWR)
        TH_FLAGS[SENDER] = 0
        TH_FLAGS[RECEIVER] = 0
        MSG_Q.put(MSG_END) #deblock the sender
        rth.join()
        sth.join()
        exit()
