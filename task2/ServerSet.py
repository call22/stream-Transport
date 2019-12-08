# -*- coding: utf-8 -*-
# this file to set up server
import sys
import socket
from Server import Server
MAX_LISTEN = 10


def serverSetup():
    try:
        serverPort = int(sys.argv[1])
    except IndexError as e:
        print('Wrong argument, {}'.format(str(e)))
    else:
        rtspSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        rtspSocket.bind(('', serverPort))
        rtspSocket.listen(MAX_LISTEN)
        while True:
            sock, address = rtspSocket.accept()
            print(sock, address)
            Server(address[0], sock)


if __name__ == '__main__':
    serverSetup()