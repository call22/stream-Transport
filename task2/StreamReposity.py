import cv2
import os
from PIL import Image

MAX_SIZE = 40000
VideoTypeList = ['mp4']
PlayTypeList = [0]


def compressPic(img):
    im = Image.open(img)
    size = 700, 500
    im.thumbnail(size)
    im.save(img, 'JPEG')


def compressFrame(data, type):
    # if type == 0:
    #     return data
    return data


class StreamRepo:
    def __init__(self, filename, play):
        # check filename
        self._check_filename(filename)
        self.filename = filename
        try:
            # self.file = open(filename, 'rb')  # file pointer
            self.vc = cv2.VideoCapture(filename)
            self.rval = self.vc.isOpened()
        except IOError:
            raise IOError('open %s fail.\n' % filename)
        self.framNum = 0
        self.playType = play    # 播放类型, 决定清晰度, 压缩不同

    # get a frame from video, write in jpg, compress, read
    def getNextData(self):
        if self.videoType == 'mp4':
            self.rval, frame = self.vc.read()
            if self.rval:
                data = self._change_frame_to_data(frame)
                # data = compressFrame(data, self.playType)
                self.framNum += 1
                return data
            self.vc.release()
            print(self.framNum)

    def getFramNum(self):
        return self.framNum

    def _check_filename(self, filename):
        ext = filename.split('.')[1]
        if ext in VideoTypeList:
            self.videoType = ext
        else:
            raise KeyError('filename %s illegal' % filename)

    def _change_frame_to_data(self, frame):
        img = self.filename.split('.')[0] + '.jpg'
        cv2.imencode('.jpg', frame)[1].tofile(img)
        compressPic(img)
        fi = open(img, 'rb')
        data = fi.read(MAX_SIZE)
        fi.close()
        return data
