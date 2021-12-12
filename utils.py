import json
import pickle
import cv2 as cv
import numpy as np

from vsearch.config import args
import os
def saveObject(out_path, name, o):
    if not os.path.exists(out_path):
        os.makedirs(out_path, mode=0o777, exist_ok=True)
    output_hal = open(f'{out_path}\\{name}.pkl', 'wb')
    _str = pickle.dumps(o)
    output_hal.write(_str)
    output_hal.close()


def readObject(input_path):
    with open(input_path, 'rb') as file:
        return pickle.loads(file.read())


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



def __json_dumps_default_func(o):
    tp = str(type(o))
    # print(f'current type: {tp}  type: {type(o)}   value: {o}  ')
    if tp.find('float') != -1:
        o = float(o)
    elif tp.find('array') != -1:
        o = o.tolist()
    else:
        o = o.__dict__
    return o

def json_dumps(o) -> str:
    """
    可以兼容: 含有numpy 还有 该项目中对象的 json序列化
    """
    return json.dumps(o, default=__json_dumps_default_func)

def json_loads(json_str):
    return json.loads(json_str)

# def saveChapterObject(input, )


class time:

    def wrapper(self):
        pass