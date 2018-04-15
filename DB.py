import sqlite3
from hashlib import sha256

DB_NAME = "messaging.db"

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
        h = sha256()
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
        h = sha256()
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
