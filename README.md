# Messaging
Messaging is a client/server app written in Python2.7 that allows multiple users to communicate over a shared channel.

# How it works ?

The server handle multiple connection by creating a temporary thread that either create a new user or authenticate an old one, then add it to the users queue. A number of threads are running synchronously (the number is specified using a configuration variable. See the Usage section) to process messages sent by clients. This image illustrate the architecture of the app:

![architecture](https://github.com/youben11/messaging/blob/master/architecture.jpg)

# Installation

You only need to have Python2.7 installed to run the server and the curses module to run the client.

Run the following command to get the code:
```bash
$ git clone https://github.com/youben11/messaging
```
If you are aiming to run the client then run the following command:
```bash
$ sudo pip2 install curses
```

### Docker
Docker lovers (users) can run the server quickly with the following command:
```bash
$ git clone https://github.com/youben11/messaging
$ cd messaging
$ docker build --tag messaging:latest .
$ docker run --rm -t -p <port>:4848 messaging
```
This will get the server started. You can connect to the server through your host IP address and the specified port number.

# Usage
Running the server:
```bash
$ cd messaging
$ python2.7 server.py
```

Running the client:
```bash
$ cd messaging
$ python2.7 client.py
[+] Usage:
            client.py connect username password server_ip [server_port]
            client.py create username password server_ip [server_port]

[*] usernmae: alphanumeric, 2 to 20 character (must begin with a letter)
[*] password: 8 to 15 characters
```

### Configuring the server
The server app has different variables that can be configured:

###### NUM_TH
This specify how many threads will handle the clients. Default is 2. It's recommended to increase this number if you have a lot of client.

###### ADDR
The IP Address that the server will bind to. Default is 0.0.0.0 which binds all the existing addresses.

###### PORT
The PORT number that the server will use. Default is 4848.
