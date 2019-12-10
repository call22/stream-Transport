import cv2
import os
from PIL import Image

MAX_SIZE = 40000
VideoTypeList = ['mp4']
PlayTypeList = [0]


def compressPic(img):
    im = Image.open(img)
    size = 700, 600
    im.thumbnail(size)
    im.save(img, 'JPEG')

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
        # self.playType = play    # 播放类型, 决定清晰度, 压缩不同

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

    def getTotalTime(self):
        return self.duration

    def getNowTime(self):
        print('getNowTime', self.vc.get(0)/1000)
        return self.vc.get(0)/1000

    def setFramPos(self, time):
        print('setFramPos: ',time)
        self.vc.set(cv2.CAP_PROP_POS_MSEC, time*1000)

    def _deal_video(self, filename):
        self.vc = cv2.VideoCapture(filename)
        self.rsuccess = self.vc.isOpened()
        if self.rsuccess:
            rate = self.vc.get(5)
            totalFrames = self.vc.get(7)
            print('rate: ', rate, '\ntotalFrames: ', totalFrames)
            self.duration = totalFrames/rate

    def _change_frame_to_data(self, frame):
        img = self.filename.split('.')[0] + '.jpg'
        cv2.imencode('.jpg', frame)[1].tofile(img)
        compressPic(img)
        fi = open(img, 'rb')
        data = fi.read(MAX_SIZE)
        fi.close()
        return data
