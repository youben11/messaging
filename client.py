import socket
import time
import re
import signal
import curses
from sys import argv
from threading import Thread
from messaging_proto import *
from Queue import Queue
from string import printable


HELP = """[+] Usage:
            %s connect username password server_ip [server_port]
            %s create username password server_ip [server_port]

[*] usernmae: alphanumeric, 2 to 20 character (must begin with a letter)
[*] password: 8 to 15 characters
"""

re_cmd = r"^(connect|create) [a-zA-Z]\w{1,19} \S{8,15} ((25[0-5]|2[0-4][0-9]|1[0-9]{2}|[1-9]?[0-9])\.){3}(25[0-5]|2[0-4][0-9]|1[0-9]{2}|[1-9]?[0-9])( \d+)?$"

CMD_CONNECT = "connect"
CMD_CREATE = "create"

TH_FLAGS = [1,1,1]
SENDER = 0
RECEIVER = 1
MAIN = 2
#Message Queue Sender
MSG_Q_S = Queue()
MSG_END = "#END#"
#Message List Receiver
MSG_R = []

DEFAULT_PORT = 4848

def sender(sock):
    while True:
        try:
            msg = MSG_Q_S.get()
            if not TH_FLAGS[SENDER]:
                exit()
            msg = msg.replace("~","&(tilde)")
            sock.send("%s%s%s" % (DELEM_MSG, msg, DELEM_MSG))
        except socket.error:
            TH_FLAGS[RECEIVER] = 0
            TH_FLAGS[MAIN] = 0
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
                TH_FLAGS[SENDER] = 0
                TH_FLAGS[MAIN] = 0
                exit()
        except socket.timeout as st:
            if not TH_FLAGS[RECEIVER]:
                exit()
            continue
        messages = re.findall(r'@(\w+)~([^~]+)~', buf)
        for sender, message in messages:
            message = message.replace("&(tilde)","~")
            MSG_R.append((time.asctime().split()[3], sender, message))

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

def start_curses(screen):
    screen.clear()
    screen.refresh()
    screen.timeout(1)
    curses.curs_set(0)
    buf = list()
    x = 0
    y = 0
    key = 0

    while key != curses.KEY_F1:
        try:
            if not TH_FLAGS[MAIN]:
                #red color here
                screen.addstr(height-1,0, "Connection Lost... Press something to exit")
                screen.timeout(-1)
                screen.getch()
                return None

            screen.refresh()
            height, width = screen.getmaxyx()

            if key == curses.KEY_DOWN:
                y = y + 1
            elif key == curses.KEY_UP:
                y = y - 1
            elif key == curses.KEY_RIGHT:
                x = x + 1
            elif key == curses.KEY_LEFT:
                x = x - 1
            elif key == 127 and len(buf): #DELETE
                buf.pop()
            elif key == 10: #ENTER
                MSG_Q_S.put("".join(buf))
                buf = []
                key = 0

            try:
                c = chr(key)
                if c in printable:
                    buf.append(c)
            except:
                pass

            #x and y must be in their allowed range
            x = max(0, x)
            x = min(width - 1, x)
            y = max(0, y)
            y = min(width - 1, y)

            #strings
            str_status = "Exit: F1 | Send: Enter"[:width-1]
            str_msg = ("message: %s" % "".join(buf))[:width-1]
            str_msg = str_msg + " " * (width - 1 - len(str_msg))

            #displaying
            display_msgs(screen, height, width)
            screen.addstr(height-1, 0, str_status)
            screen.addstr(height-2, 0, str_msg)

            key = screen.getch()

        except KeyboardInterrupt:
            return None

def display_msgs(screen, height, width):
    #manage size
    messages = ["[%s] %s: %s" % m for m in MSG_R]
    screen.addstr(0,0, "\n".join(messages))


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
    #start the gui
    curses.wrapper(start_curses)
    #the client will shut down
    sock.shutdown(socket.SHUT_RDWR)
    TH_FLAGS[SENDER] = 0
    TH_FLAGS[RECEIVER] = 0
    MSG_Q_S.put(MSG_END) #deblock the sender
    rth.join()
    sth.join()
    exit()
