from tkinter import *
import tkinter.messagebox as tkMessageBox
from PIL import Image, ImageTk
import socket, threading, sys, traceback, os
import time

from RtpPacket import RtpPacket

CACHE_FILE_NAME = "cache-"
CACHE_FILE_EXT = ".jpg"


class Client:
    INIT = 0
    READY = 1
    PLAYING = 2
    state = INIT

    SETUP = 0
    PLAY = 1
    PAUSE = 2
    TEARDOWN = 3

    # Initiation..
    def __init__(self, master, serveraddr, serverport, rtpport, filename):
        self.serverAddr = serveraddr
        self.serverPort = int(serverport)
        self.rtpPort = int(rtpport)
        self.fileName = filename
        self.rtspSeq = 0
        self.sessionId = ''
        self.requestSent = -1
        self.teardownAcked = 0
        self.connectToServer()
        self.frameNbr = 0
        self.Movie = {"totalTime": 0, "nowTime": 0, "rate": 1}
        self.master = master
        self.master.protocol("WM_DELETE_WINDOW", self.handler)
        self.createWidgets()

    def createWidgets(self):
        """Build GUI."""
    # Create a label to display the movie
        self.label = Label(self.master, height=19)
        self.label.pack(expand=True, fill=BOTH, side=TOP, pady=8)

        # Create a progress bar to display progress
        self.scale = Scale(self.master, from_=0, to=0, orient=HORIZONTAL, sliderlength=4,
                           width=4, troughcolor="black", showvalue=NO)
        self.scale.pack(expand=False, fill=X)

        fm = Frame(self.master)
        fm.pack(expand=False, fill=X)
        self.bar = Canvas(fm, height=3, bg="white")
        self.bar.pack(fill=X, expand=True)
        self.fill_line = self.bar.create_rectangle(0, 0, 0, 3, width=3, fill="black")
        self.nowTime = Label(fm, text='0')
        self.nowTime.pack(side=LEFT, fill=NONE)
        self.totalTime = Label(fm, text='0')
        self.totalTime.pack(side=RIGHT, fill=NONE)

        fm1 = Frame(self.master)
        fm1.pack(expand=False, fill=X, pady=5)
        # Create Speed button
        self.speed = Button(fm1, width=20)
        self.speed.pack(side=LEFT, padx=2, expand=True)
        self.speed["text"] = "+15s"
        self.speed["command"] = self.goMovie

        # Create Rewind button
        self.rewind = Button(fm1, width=20)
        self.rewind.pack(side=LEFT, padx=2, expand=True)
        self.rewind["text"] = "-5s"
        self.rewind["command"] = self.rewindMovie

        # Create 2 speed button
        self.double = Button(fm1, width=20)
        self.double.pack(side=LEFT, padx=2, expand=True)
        self.double["text"] = "x2"
        self.double["command"] = self.doubleSpeed

        # Create 0.5 speed button
        self.half = Button(fm1, width=20)
        self.half.pack(side=LEFT, padx=2, expand=True)
        self.half["text"] = "x0.5"
        self.half["command"] = self.halfSpeed

        fm2 = Frame(self.master)
        fm2.pack(expand=False, fill=X, pady=5)
        # Create Setup button
        self.setup = Button(fm2, width=20)
        self.setup.pack(side=LEFT, padx=2, expand=True)
        self.setup["text"] = "Setup"
        self.setup["command"] = self.setupMovie

        # Create Play button
        self.start = Button(fm2, width=20)
        self.start.pack(side=LEFT, padx=2, expand=True)
        self.start["text"] = "Play"
        self.start["command"] = self.playMovie

        # Create Pause button
        self.pause = Button(fm2, width=20)
        self.pause.pack(side=LEFT, padx=2, expand=True)
        self.pause["text"] = "Pause"
        self.pause["command"] = self.pauseMovie

        # Create Teardown button
        self.teardown = Button(fm2, width=20)
        self.teardown.pack(side=LEFT, padx=2, expand=True)
        self.teardown["text"] = "Teardown"
        self.teardown["command"] = self.exitClient

    def goMovie(self):
        pass

    def updateTime(self, text):
        if self.state == self.PLAYING:
            print('update play...')
            self.Movie["nowTime"] = float(text)
            self.state = self.READY
            self.sendRtspRequest(self.PLAY)

    def rewindMovie(self):
        pass

    def doubleSpeed(self):
        pass

    def halfSpeed(self):
        pass

    def setupMovie(self):
        """Setup button handler."""
        if self.state == self.INIT:
            self.sendRtspRequest(self.SETUP)

    def exitClient(self):
        """Teardown button handler."""
        self.sendRtspRequest(self.TEARDOWN)
        self.master.destroy()  # Close the gui window
        os.remove(CACHE_FILE_NAME + self.sessionId + CACHE_FILE_EXT)  # Delete the cache image from video

    def pauseMovie(self):
        """Pause button handler."""
        if self.state == self.PLAYING:
            self.sendRtspRequest(self.PAUSE)

    def showProcess(self):  # show process
        pass

    def playMovie(self):
        """Play button handler."""
        if self.state == self.READY:
            # Create a new thread to listen for RTP packets
            threading.Thread(target=self.listenRtp).start()
            self.playEvent = threading.Event()
            self.playEvent.clear()
            self.sendRtspRequest(self.PLAY)

    def listenRtp(self):
        """Listen for RTP packets."""
        while True:
            try:
                data = self.rtpSocket.recv(60000)
                if data:
                    self._windows_update()

                    rtpPacket = RtpPacket()
                    rtpPacket.decode(data)

                    currFrameNbr = rtpPacket.seqNum()
                    if currFrameNbr > self.frameNbr:  # Discard the late packet
                        self.frameNbr = currFrameNbr
                        self.updateMovie(self.writeFrame(rtpPacket.getPayload()))
            except:
                # Stop listening upon requesting PAUSE or TEARDOWN
                if self.playEvent.isSet():
                    break

                # Upon receiving ACK for TEARDOWN request,
                # close the RTP socket
                if self.teardownAcked == 1:
                    self.rtpSocket.shutdown(socket.SHUT_RDWR)
                    self.rtpSocket.close()
                    break

    def writeFrame(self, data):
        """Write the received frame to a temp image file. Return the image file."""
        cachename = CACHE_FILE_NAME + self.sessionId + CACHE_FILE_EXT
        file = open(cachename, "wb")
        file.write(data)
        file.close()

        return cachename

    def updateMovie(self, imageFile):
        """Update the image file as video frame in the GUI."""
        photo = ImageTk.PhotoImage(Image.open(imageFile))
        self.label.configure(image=photo)
        self.label.image = photo

    def connectToServer(self):
        """Connect to the Server. Start a new RTSP/TCP session."""
        self.rtspSocket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            self.rtspSocket.connect((self.serverAddr, self.serverPort))
        except:
            tkMessageBox.showwarning('Connection Failed', 'Connection to \'%s\' failed.' % self.serverAddr)

    def sendRtspRequest(self, requestCode):
        """Send RTSP request to the server."""

        # Setup request
        if requestCode == self.SETUP and self.state == self.INIT:
            threading.Thread(target=self.recvRtspReply).start()
            # Update RTSP sequence number.
            self.rtspSeq += 1

            # Write the RTSP request to be sent.
            request = 'SETUP ' + self.fileName + ' RTSP/1.0\nCSeq: ' + str(
                self.rtspSeq) + '\nTransport: RTP/UDP; client_port= ' + str(self.rtpPort)

            # Keep track of the sent request.
            self.requestSent = self.SETUP

        # Play request
        elif requestCode == self.PLAY and self.state == self.READY:
            self.rtspSeq += 1
            request = 'PLAY ' + self.fileName + ' RTSP/1.0\nCSeq: ' + str(self.rtspSeq) + '\nSession: ' + \
                      self.sessionId + '\nRange: npt=' + str(self.Movie["nowTime"]) + '-' + str(self.Movie["totalTime"])  # Range设置播放时间范围
            self.requestSent = self.PLAY

        # Pause request
        elif requestCode == self.PAUSE and self.state == self.PLAYING:
            self.rtspSeq += 1
            request = 'PAUSE ' + self.fileName + ' RTSP/1.0\nCSeq: ' + str(
                self.rtspSeq) + '\nSession: ' + self.sessionId
            self.requestSent = self.PAUSE

        # Teardown request
        elif requestCode == self.TEARDOWN and not self.state == self.INIT:
            self.rtspSeq += 1
            request = 'TEARDOWN ' + self.fileName + ' RTSP/1.0\nCSeq: ' + str(
                self.rtspSeq) + '\nSession: ' + self.sessionId
            self.requestSent = self.TEARDOWN
        else:
            return

        # Send the RTSP request using rtspSocket.
        self.rtspSocket.send(request.encode())

        print('\nData sent:\n' + request)

    def recvRtspReply(self):
        """Receive RTSP reply from the server."""
        while True:
            reply = self.rtspSocket.recv(1024)

            if reply:
                self.parseRtspReply(reply.decode("utf-8"))

            # Close the RTSP socket upon requesting Teardown
            if self.requestSent == self.TEARDOWN:
                self.rtspSocket.shutdown(socket.SHUT_RDWR)
                self.rtspSocket.close()
                break

    def parseRtspReply(self, data):
        """Parse the RTSP reply from the server."""
        lines = str(data).split('\n')
        seqNum = int(lines[1].split(' ')[1])

        # Process only if the server reply's sequence number is the same as the request's
        if seqNum == self.rtspSeq:
            session = lines[2].split(' ')[1]
            # New RTSP session ID
            if self.sessionId == '':
                self.sessionId = session

            # Process only if the session ID is the same
            if self.sessionId == session:
                if int(lines[0].split(' ')[1]) == 200:
                    if self.requestSent == self.SETUP:
                        # Update RTSP state.
                        self.state = self.READY
                        # Open RTP port.
                        self.openRtpPort()
                    elif self.requestSent == self.PLAY:
                        self.state = self.PLAYING
                        # get now time
                        self.timeRecord = time.time()
                        self.Movie["totalTime"] = float(lines[3].split('-')[1])
                        self.Movie["nowTime"] = float(lines[3].split('=')[1].split('-')[0])
                        self.totalTime["text"] = str(round(self.Movie["totalTime"] / 60, 2))
                        self.scale["to"] = self.Movie["totalTime"]
                        # self.master.update()
                    elif self.requestSent == self.PAUSE:
                        self.state = self.READY
                        # The play thread exits. A new thread is created on resume.
                        self.playEvent.set()
                    elif self.requestSent == self.TEARDOWN:
                        self.state = self.INIT
                        # Flag the teardownAcked to close the socket.
                        self.teardownAcked = 1

    def openRtpPort(self):
        """Open RTP socket binded to a specified port."""
        # Create a new datagram socket to receive RTP packets from the server
        self.rtpSocket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

        # Set the timeout value of the socket to 0.5sec
        self.rtpSocket.settimeout(0.5)

        try:
            # Bind the socket to the address using the RTP port given by the client user
            self.rtpSocket.bind(("", self.rtpPort))
        except:
            tkMessageBox.showwarning('Unable to Bind', 'Unable to bind PORT=%d' % self.rtpPort)

    def handler(self):
        """Handler on explicitly closing the GUI window."""
        self.pauseMovie()
        if tkMessageBox.askokcancel("Quit?", "Are you sure you want to quit?"):
            self.exitClient()
        else:  # When the user presses cancel, resume playing.
            self.playMovie()

    def _windows_update(self):
        self.Movie["nowTime"] = self.Movie["nowTime"] + time.time() - self.timeRecord
        self.timeRecord = time.time()
        self.nowTime["text"] = str(round(self.Movie["nowTime"] / 60, 2))  # min 单位
        self.scale.set(self.Movie["nowTime"])
        self.bar.coords(self.fill_line, (0, 0, self.master.winfo_width() * self.Movie["nowTime"] / self.Movie["totalTime"], 3))
        # self.master.update()
