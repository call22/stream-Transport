import cv2
import numpy as np
from random import randint
import os
import time

MAX_SIZE = 40000
VideoTypeList = ['mp4']
PlayTypeList = [0]


# time 以s为单位
class StreamRepo:
    def __init__(self, filename):
        # check filename
        self.filename = filename
        try:
            self._deal_video(filename)
        except IOError:
            raise IOError('open %s fail.\n' % filename)
        self.framNum = 0
        self.speed = 1  # 播放速度

    # get a frame from video, write in jpg, compress, read
    def getNextData(self):
        self.rsuccess, frame = self.vc.read()
        if self.rsuccess:
            data = self._change_frame_to_data(frame)
            self.framNum += 1
            return data
        self.vc.release()

    def getFramNum(self):
        return self.framNum

    def getTotalFrame(self):
        return self.totalFrames

    def getSpeed(self):
        return self.speed

    def getRate(self):
        return self.rate

    def setFramPos(self, frame):
        self.vc.set(cv2.CAP_PROP_POS_FRAMES, frame)
        self.framNum = frame

    def setSpeed(self, speed):
        self.speed = speed

    def removTempSrc(self):
        os.remove(self.img)

    def _deal_video(self, filename):
        self.vc = cv2.VideoCapture(filename)
        self.rsuccess = self.vc.isOpened()
        if self.rsuccess:
            self.rate = self.vc.get(5)
            self.totalFrames = int(self.vc.get(7))
            self.img = self.filename.split('.')[0] + str(randint(10, 50)) + '.jpg'

    def _change_frame_to_data(self, frame):
        # compress image
        height, weight = frame.shape[0:2]
        ratio = np.sqrt(100000/(height * weight))
        newsize = (int( weight * ratio), int(height * ratio))
        newFrame = cv2.resize(frame, newsize)
        cv2.imwrite(self.img, newFrame)

        fi = open(self.img, 'rb')
        data = fi.read(MAX_SIZE)
        fi.close()
        return data
