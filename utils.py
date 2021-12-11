import pickle
import cv2 as cv
import numpy as np

from vsearch.config import args
import os
def saveObject(out_path, name, o):
    if not os.path.exists(out_path):
        os.mkdir(out_path)
    output_hal = open(f'{out_path}\\{name}.pkl', 'wb')
    _str = pickle.dumps(o)
    output_hal.write(_str)
    output_hal.close()


def readObject(input_path):
    with open(input_path, 'rb') as file:
        return pickle.loads(file.read())


# def saveVideoObject(out_path, name, o):
#     o.cap = None
#     saveObject(out_path, name, o)
#
#
# def readVideoObject(input_path):
#     v = readObject(input_path)
#     v.cap = cv.VideoCapture(v.path)
#     return v

def cvimread(path):
    """
    读取路径包含中文的图片
    """
    return cv.imdecode( np.fromfile(path, dtype=np.uint8 ), -1)

def cvimwrite(path, img):
    """
    保存路径包含中文的图片
    """
    # cv2.imencode(保存格式, 保存图片)[1].tofile(保存路径)
    cv.imencode( f'.{args.img_format}', img )[1].tofile( path )


# def saveChapterObject(input, )


class time:

    def wrapper(self):
        pass