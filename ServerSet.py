# -*- coding: utf-8 -*-
# this file to set up server
import sys
from Server import Server

def serverSetup():
    try:
        serverPort = int(sys.argv[1])
    except IndexError as e:
        print('Wrong argument, {}'.format(str(e)))
    else:
        Server(serverPort)


if __name__ == '__main__':
    serverSetup()