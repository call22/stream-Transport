import os
from PIL import Image

MAX_SIZE = 40000


def getImageRepo(filename):
    dirname = os.path.dirname(filename)
    filelist = os.listdir(dirname)
    imagelist = []
    for item in filelist:
        if item.split('.')[1] in ['jpg','jpeg']:
            imagelist.append(os.path.join(dirname, item))
    return imagelist


def compressPic(filelist):
    for img in filelist:
        im = Image.open(img)
        size = 500, 400
        im.thumbnail(size)
        im.save(img, 'JPEG')


class PicRepo:
    def __init__(self, filename):
        self.filelist = getImageRepo(filename)
        compressPic(self.filelist)
        try:
            self.file = open(self.filelist[0], 'rb')  # file pointer
        except IOError:
            raise IOError('open %s fail.\n' % filename)
        self.framNum = 0
        self.index = 0
        self.listlength = len(self.filelist)

    def getNextData(self):
        data = self.file.read(MAX_SIZE)
        self.file.close()
        self.index = (self.index + 1) % self.listlength
        self.file = open(self.filelist[self.index], 'rb')
        self.framNum += 1
        return data

    def getFramNum(self):
        return self.framNum
