import socket, threading
from random import randint
from hashlib import md5
from RtpPacket import RtpPacket
from StreamReposity import StreamRepo
import time

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
    # l = threading.Lock()

    def __init__(self, address, sock):
        self.clientInfo = {'clientAddress': address,
                           'rtspSocket': sock}  # record: 1. rtpPort, 2. client address, 3. rtsp socket, 4. rtpSocket
        self.sessionId = ''
        self.tearDownRequest = 0
        self.rtspSeq = 0
        self.rtpDataRepository = None
        self.playEvent = None
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
        try:
            request = data.split('\n')
            requestCommand = request[0].split(' ')[0]
            requestFile = request[0].split(' ')[1]
            requestRtspV = request[0].split(' ')[2]
            rtspSeq = int(request[1].split(' ')[1])
        except Exception as e:
            print(data,'\n')
            print('error {}\n'.format(str(e)))
            pass
        else:
            # only sessionId and seq same pass
            if rtspSeq == self.rtspSeq + 1:
                condition = False
                if self.sessionId == '':
                    condition = True
                else:
                    sessionId = request[2].split(' ')[1]
                    if sessionId == self.sessionId:
                        condition = True
                if condition:
                    if requestCommand == 'SETUP' and self.state == self.INIT:  # check file legal
                        print('\n parse Setup processiong....')
                        try:
                            self.rtpDataRepository = StreamRepo(requestFile)
                            self.totalFrame = self.rtpDataRepository.getTotalFrame()
                            self.rate = self.rtpDataRepository.getRate()
                            self.speed = self.rtpDataRepository.getSpeed()
                            self.fbps = 1/self.rate/self.speed * 2
                            self.framenum = self.rtpDataRepository.getFramNum()
                        except IOError:
                            print("RTSP/1.0 404 NOT FOUND")
                            reply = 'RTSP/1.0 404 NOT FOUND\nCSeq: ' + str(rtspSeq) + '\nSession: ' + self.sessionId
                            self.clientInfo['rtspSocket'].send(reply.encode())
                        else:
                            self.state = self.READY
                            self.clientInfo['rtpPort'] = request[2].split(' ')[3]
                            self.sessionId = md5(str(randint(1000, 10000)).encode('utf-8')).hexdigest()     # md5加密的session
                            self.rtspSeq += 1
                            self.sendRtspReply(rtspSeq, requestRtspV)

                    elif requestCommand == 'PLAY' and (self.state == self.READY or self.state == self.PLAYING):
                        #   set play position
                        print('\n parse Play processiong....')
                        self.requestPlayPos = int(request[3].split('=')[1].split('-')[0])

                        self.requestSpeed = float(request[4].split(' ')[1])
                        # pause or setup
                        if self.state == self.READY or self.playEvent.isSet():
                            print('\n New rtpPacket send Threading')
                            # create new thread, send rtp packet
                            self.clientInfo['rtpSocket'] = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
                            self.playEvent = threading.Event()
                            self.playEvent.clear()
                            threading.Thread(target=self.sendRtpPacket).start()

                        self.state = self.PLAYING
                        self.rtspSeq += 1
                        newRange = str(self.requestPlayPos) + '-' + str(self.totalFrame)
                        self.sendRtspReply(rtspSeq, requestRtspV, newRange, self.requestSpeed, self.rate)

                    elif requestCommand == 'PAUSE' and self.state == self.PLAYING:
                        print('\n parse Pause processing....')
                        self.state = self.READY
                        self.rtspSeq += 1
                        # stop sendRtpPacket
                        self.playEvent.set()

                        self.sendRtspReply(rtspSeq, requestRtspV)
                    elif requestCommand == 'TEARDOWN':
                        print('\n parse Teardown procession....')
                        self.state = self.TEARDOWN
                        self.rtspSeq += 1
                        # stop sendRtpPacket
                        self.tearDownRequest = 1

                        self.sendRtspReply(rtspSeq, requestRtspV)

    def sendRtspReply(self, rtspSeq, requestV, range='', speed=0.0, rate=0.0):
        """Reply for explicit command"""
        reply = requestV + ' 200 OK\nCSeq: ' + str(rtspSeq) + '\nSession: ' + self.sessionId
        if range != '':
            reply = reply + '\nRange: npt=' + range
        if speed != 0.0:
            reply = reply + '\nSpeed: ' + str(speed)
        if rate != 0.0:
            reply = reply + '\nRate: ' + str(rate)
        reply += '\n\n'
        self.clientInfo['rtspSocket'].send(reply.encode())
        print('\nRTSP -> client: \n' + reply)

    def sendRtpPacket(self):
        formerTime = time.time()
        nextTime = formerTime + self.fbps
        while True:
            if self.tearDownRequest:
                self.clientInfo['rtpSocket'].shutdown(socket.SHUT_RDWR)
                self.clientInfo['rtpSocket'].close()
                self.rtpDataRepository.removTempSrc()
                break
            if self.playEvent.isSet():
                break

            nowTime = time.time()
            if nowTime >= nextTime:
                formerTime = nowTime
                nextTime = formerTime + self.fbps
            else:
                time.sleep(nextTime-nowTime)

            if self.state == self.PLAYING:
                if self.requestPlayPos != self.framenum and self.requestPlayPos <= self.totalFrame:
                    self.rtpDataRepository.setFramPos(self.requestPlayPos)
                    self.framenum = self.requestPlayPos

                if self.requestSpeed != self.speed and self.requestSpeed in [1.0, 0.5, 2.0]:
                    self.rtpDataRepository.setSpeed(self.requestSpeed)
                    self.speed = self.requestSpeed
                    self.fbps = 1 / self.rate / self.speed * 2

            data = self.rtpDataRepository.getNextData()
            seq = self.rtpDataRepository.getFramNum()

            if data:
                address = self.clientInfo['clientAddress']
                port = int(self.clientInfo['rtpPort'])
                packet = makeRtpPacket(data, seq)
                self.clientInfo['rtpSocket'].sendto(packet, (address, port))
