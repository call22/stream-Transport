from tkinter import *
import tkinter.messagebox as tkMessageBox
import socket, threading, sys, traceback, os
from random import randint
from hashlib import md5
from RtpPacket import RtpPacket
from StreamReposity import StreamRepo
from time import sleep

MAX_SEND = 40000


def makeRtpPacket(payload, seqNum):
    version = 1
    padding = 0
    extension = 0
    cc = 0
    marker = 0
    pt = 26  # JPEG
    ssrc = 0
    seqnum = seqNum
    payload = payload
    rtpPacket = RtpPacket()
    rtpPacket.encode(version, padding, extension, cc, seqnum, marker, pt, ssrc, payload)
    return rtpPacket.getPacket()


class Server:
    # request
    SETUP = 0
    PLAY = 1
    PAUSE = 2
    TEARDOWN = 3
    # status
    INIT = 0
    READY = 1
    PLAYING = 2
    state = INIT

    def __init__(self, address, sock):
        self.clientInfo = {}  # record: 1. rtpPort, 2. client address, 3. rtsp socket, 4. rtpSocket
        self.clientInfo['clientAddress'] = address
        self.clientInfo['rtspSocket'] = sock
        self.sessionId = ''
        self.tearDownRequest = 0
        self.rtpDataRepository = None
        # setup listen
        self.setupRtsp()

    def setupRtsp(self):
        threading.Thread(target=self.recvRtspRequest).start()

    def recvRtspRequest(self):
        while True:
            request = self.clientInfo['rtspSocket'].recv(1024)
            if request:
                self.parseRtspRequest(request.decode('utf-8'))

    def parseRtspRequest(self, data):
        """Get public information"""
        request = data.split('\n')
        requestCommand = request[0].split(' ')[0]
        requestFile = request[0].split(' ')[1]
        requestRtspV = request[0].split(' ')[2]
        rtspSeq = int(request[1].split(' ')[1])

        if requestCommand == 'SETUP' and self.state == self.INIT:  # check file legal
            try:
                self.rtpDataRepository = StreamRepo(requestFile, 1)
            except IOError:
                print("RTSP/1.0 404 NOT FOUND")
                reply = 'RTSP/1.0 404 NOT FOUND\nCSeq: ' + str(rtspSeq) + '\nSession: ' + self.sessionId
                self.clientInfo['rtspSocket'].send(reply.encode())
            else:
                self.state = self.READY
                self.clientInfo['rtpPort'] = request[2].split(' ')[3]
                self.sessionId = md5(str(randint(1000, 10000)).encode('utf-8')).hexdigest()
                self.sendRtspReply(rtspSeq, requestRtspV)

        elif requestCommand == 'PLAY' and self.state == self.READY:
            self.state = self.PLAYING
            # create new thread, send rtp packet
            self.clientInfo['rtpSocket'] = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            self.playEvent = threading.Event()
            self.playEvent.clear()
            threading.Thread(target=self.sendRtpPacket).start()

            self.sendRtspReply(rtspSeq, requestRtspV)

        elif requestCommand == 'PAUSE':
            self.state = self.READY
            # stop sendRtpPacket
            self.playEvent.set()

            self.sendRtspReply(rtspSeq, requestRtspV)
        elif requestCommand == 'TEARDOWN':
            self.state = self.TEARDOWN
            # stop sendRtpPacket
            self.tearDownRequest = 1

            self.sendRtspReply(rtspSeq, requestRtspV)

    def sendRtspReply(self, rtspSeq, requestV):
        """Reply for explicit command"""
        reply = requestV + ' 200 OK\nCSeq: ' + str(rtspSeq) + '\nSession: ' + self.sessionId
        self.clientInfo['rtspSocket'].send(reply.encode())
        print('\nRTSP -> client: \n' + reply)

    def sendRtpPacket(self):
        while True:
            if self.tearDownRequest:
                self.clientInfo['rtpSocket'].shutdown(socket.SHUT_RDWR)
                self.clientInfo['rtpSocket'].close()
                break
            if self.playEvent.isSet():
                break
            # send data
            data = self.rtpDataRepository.getNextData()
            print(len(data))
            if data:
                address = self.clientInfo['clientAddress']
                port = int(self.clientInfo['rtpPort'])
                packet = makeRtpPacket(data, self.rtpDataRepository.getFramNum())
                self.clientInfo['rtpSocket'].sendto(packet, (address, port))
