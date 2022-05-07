import time
from typing import List
from unicodedata import name
import img2pdf
import json
import pickle
import shutil
import cv2 as cv
import numpy as np
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
    """
        http://127.0.0.1/xxx -> http://服务器域名/xxx
    """
    url = local_path.replace(
        path.RootPath.project_root_dir, args.img_url_prefix)
    print(
        f'project_root_dir: {path.RootPath.project_root_dir} img_url_prefix: {args.img_url_prefix}  ')
    return url.replace('\\', '/')


def url2local(url):
    """
        http://服务器域名/xxx -> http://127.0.0.1/xxx
    """
    # @wait 是否有必要兼容win 还是全局 统一/
    local_path = url.replace(
        args.img_url_prefix, path.RootPath.project_root_dir)
    return local_path.replace('/', '\\')


# @wait
def copy_video_by_img_local_path(video_local_path, img_local_path, file_name='v'):
    """
    将视频在电脑的位置，拷贝到img_url对应在本地的文件夹中的位置，
    然后生成视频支持的http访问的url 
    """
    # __drive_unified(video_local_path)
    # __drive_unified(img_local_path)
    video_format = os.path.basename(video_local_path).split('.')[-1]
    # local_img_path = url2local(img_local_path)
    # img_local_path  /12321.png
    dest = img_local_path.replace(
        # @risking 如果路径中含有 / 怎么办, 因此应该自定义一个获取文件路径的方法, 兼容问题
        # @modify
        # img_local_path.split('\\')[-1]
        os.path.basename(img_local_path), f'{file_name}.{video_format}')
    if not os.path.exists(dest):
        shutil.copy(video_local_path, dest)
    print(f'dest: {dest}')
    video_url = local2url(dest)
    print(f'video_url: {video_url}')
    return video_url


# def __drive_unified(local_path):
#     local_path[0] = str.upper(local_path[0])


def glob_sort(paths, regex='(\d+)'):
    """
    # 由于glob出来的路径, 是乱序的, 因此根据个人设定的文件名, 按照读取到的视频帧排序
    # 例如: '-6625%6600.png' => 6625    '-6625.png' => 6625  '6625.png' => 6625
    """

    import re
    # @modify file_path -> os.path.basename(file_name)
    return sorted(paths,  key=lambda file_path: int(re.findall(regex, os.path.basename(file_path))[0]))


# class time:

#     def wrapper(self):
#         pass

# 需要一个获取随机生成不可能重复的字符串


def get_unique_str() -> str:
    """
        含有时序信息的名唯一名称
    """
    return str(int(time.time()))


def img2pdf(sorted_paths: List[str], output_dir=None, file_name='temp') -> str:
    """
        如果不传入输出目录, 则直接生成在图片的目录下, 并且返回pdf文件的本地路径

        return:
            if file_name = 'temp' then {name}_{get_unique_str()}.pdf
    """
    if not sorted_paths:
        return None
    if output_dir is None:
        """
            Example: D:/t\\a/b.cn
        """
        output_dir = os.path.dirname()
    # img_file = "myImg.jpg"  # 图片路径

    pdf_file_path = f'{output_dir}/{name}_{get_unique_str()}.pdf' if file_name is 'temp' else f'{output_dir}/{name}.pdf'

    # 创建一个PDF文件 并以二进制方式写入
    with open(pdf_file_path, "wb") as f:
        # convert函数 用来转PDF
        write_content = img2pdf.convert(sorted_paths)
        f.write(write_content)  # 写入文件
    print(f"pdf生成成功: {pdf_file_path}")  # 提示语
    return pdf_file_path
