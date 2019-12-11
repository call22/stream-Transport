# -*- coding: utf-8 -*-
# this file to set up a client window
import tkinter as tk
from Client import Client
import sys


def clientSetup():
    try:
        serveraddr = sys.argv[1]
        serverport = sys.argv[2]
        rtpport = sys.argv[3]
        filename = sys.argv[4]
    except IndexError as e:
        print('Wrong argument, {}'.format(str(e)))
    else:
        master = tk.Tk()
        master.title('RTPClient')
        master.geometry('700x600')
        Client(master=master, serveraddr=serveraddr, serverport=serverport,
                           rtpport=rtpport, filename=filename)
        master.mainloop()

if __name__ == '__main__':
    clientSetup()