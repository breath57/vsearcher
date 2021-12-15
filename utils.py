import json
import pickle
import shutil
import cv2 as cv
import numpy as np
from vsearch import video

from vsearch.config import path

from .config import args
import os


def saveObject(out_path, o, name=''):
    name = name or o.name
    name = name.replace(' ', '%').replace('\t', '%')
    if not os.path.exists(out_path):
        os.makedirs(out_path, mode=0o777, exist_ok=True)
    output_hal = open(f'{out_path}\\{name}.pkl', 'wb')
    _str = pickle.dumps(o)
    output_hal.write(_str)
    output_hal.close()
    return name


def readObject(input_path, name):
    input_path = os.path.join(input_path, name) + '.pkl'
    with open(input_path, 'rb') as file:
        return pickle.loads(file.read())


def cvimread(path):
    """
    读取路径包含中文的图片
    """
    return cv.imdecode(np.fromfile(path, dtype=np.uint8), -1)


def cvimwrite(path, img):
    """
    保存路径包含中文的图片
    """
    # cv2.imencode(保存格式, 保存图片)[1].tofile(保存路径)
    cv.imencode(f'.{args.img_format}', img)[1].tofile(path)


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


def msToH_M_S_str(ms):
    print(f'ms: {ms}')
    s = ms//1000
    ss = str(int(s % 60))
    if len(ss) == 1:
        ss = '0' + ss
    m = s//60
    mm = str(int(m % 60))
    if len(mm) == 1:
        mm = '0' + mm
    h = str(int(m//60))
    if len(h) == 1:
        h = '0' + h
    time = f'{h}:{mm}:{ss}'
    print(f'time: {time}')
    return time


def local2url(local_path):
    url = local_path.replace(
        path.RootPath.project_root_dir, args.img_url_prefix)
    return url.replace('\\', '/')


def url2local(url):
    # @wait 是否有必要兼容win 还是全局 统一/
    local_path = url.replace(
        args.img_url_prefix, path.RootPath.project_root_dir)
    return local_path.replace('/', '\\')


# @wait
def copy_video_by_img_url(local_path, img_url, file_name='v'):
    """
    将视频在电脑的位置，拷贝到img_url对应在本地的文件夹中的位置，
    然后生成视频支持的http访问的url 
    """
    video_format = local_path.split('.')[-1]
    local_img_path = url2local(img_url)
    dest = local_img_path.replace(
        local_img_path.split('\\')[-1], f'{file_name}.{video_format}')
    if not os.path.exists(dest):
        shutil.copy(local_path, dest)
    video_url = local2url(dest)
    return video_url


class time:

    def wrapper(self):
        pass
