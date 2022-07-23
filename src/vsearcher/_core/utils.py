import shutil
from threading import Thread
from pathlib import Path
import time
from typing import List
import img2pdf
import json
import pickle
import cv2 as cv
import numpy as np
from .._config import path
from .._config import args
import os


def save_object_and_get_path(out_path, o, name=''):
    name = name or o.name
    if not os.path.exists(out_path):
        os.makedirs(out_path, mode=0o777, exist_ok=True)
    o_path = f'{Path(out_path).joinpath(name)}.pkl'
    with open(o_path, 'wb') as output_hal:
        _str = pickle.dumps(o)
        output_hal.write(_str)
    return o_path


def saveObject(out_path, o, name=''):
    name = name or o.name
    if not os.path.exists(out_path):
        os.makedirs(out_path, mode=0o777, exist_ok=True)
    o_path = f'{Path(out_path).joinpath(name)}.pkl'
    with open(o_path, 'wb') as output_hal:
        _str = pickle.dumps(o)
        output_hal.write(_str)
    return name


def readObject(input_path, name):
    input_path = os.path.join(input_path, name) + '.pkl'
    if not os.path.exists(input_path):
        raise RuntimeError(f'path: {input_path} 不存在! ')
        # return None
    with open(input_path, 'rb') as file:
        return pickle.loads(file.read())


def readVideoObject(name):
    return readObject(path.RootPath.output_video_object_dir, name)


def readChapterObject(name):
    return readObject(path.RootPath.output_chapter_object_dir, name)


def readCourseObject(name):
    return readObject(path.RootPath.output_course_object_dir, name)


def cvimread(path):
    """ (兼容)读取路径包含中文的图片"""
    return cv.imdecode(np.fromfile(path, dtype=np.uint8), -1)


def cvimwrite(path, img):
    """ (兼容)保存路径包含中文的图片 """
    # cv2.imencode(保存格式, 保存图片)[1].tofile(保存路径)
    cv.imencode(f'.{args.img_format}', img)[1].tofile(path)


def __json_dumps_default_func(o):
    """ 将{o}序列化 """
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
    可以兼容: 含有numpy数值对象, 或有__dict__方法的对象 的序列化
    """
    return json.dumps(o, default=__json_dumps_default_func)


def json_loads(json_str):
    return json.loads(json_str)

# def saveChapterObject(input, )


def msToH_M_S_str(ms):
    """ 将毫秒 格式化为 时:分:秒 """
    # print(f'ms: {ms}')
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
    # print(f'time: {time}')
    return time


def local2url(local_path):
    """ 将本地路径转换为可通过http访问的URL路径

    note!: 如果url_prefix 不符合 url链接前缀规则, 将不进行路径转换并返回None

    转换过程：
        static_folder_dir_prefix = a/b
        a/b/c/d/xxx -> c/d/xxx
        c/d/xxx ->  http://${args.url_prefix}/c/d/xxx
    """

    #  source_path = local_path.replace(  # 作用： http://服务器域名/xxx  -> 得到内容 /xxx
    #     path.RootPath.static_folder_dir, '').replace( '\\', '/' )  # 获取路径 排除域名，域名不能进行编码否则容易出问题
    if not args.url_prefix or not args.url_prefix.startswith('http'):
        """ 如果url_prefix 不符合 url链接前缀规则, 将不进行路径转换并返回None """
        return None

    local_path = str(Path(local_path))\
        .replace(path.RootPath.static_folder_dir_prefix, '')

    if local_path[0] in ['/', "\\"]:
        local_path = local_path[1:]
    url = f'{args.url_prefix}/{local_path}'.replace("\\", '/')
    # print(f'url: {url}')
    # print(
    #     f'project_root_dir: {path.RootPath.project_root_dir} img_url_prefix: {args.img_url_prefix}  ')
    return url  # @MODIFY 为了应对本地路径中含有空白字符和转义字符, 导致url路径不正确

def url2local(url):
    """ 将url路径转换为本地路径

        note!: 如果不是url路径(包括None), 那么将不进行处理直接返回None
        http://${domain_url}/${static_folder_dir_prefix}/xxx ->  local_path
    """
    if not url or not url.startswith('http'):
        # local_path = url
        return None

    local_path = url.replace(
        args.url_prefix + '/', "")  # http://服务器域名/xxx  ->  xxx
    local_path = str(Path(path.RootPath.static_folder_dir_prefix).joinpath(
        local_path))  # xxx -> {static_prefix}/xxx
    return local_path


def glob_sort(paths, regex='(\d+)'):
    """ 由于glob出来的路径, 是乱序的, 因此根据个人设定的文件名, 按照读取到的视频帧排序

    例如: '-6625%6600.png' => 6625    '-6625.png' => 6625  '6625.png' => 6625
    """

    import re
    # @MODIFY file_path -> os.path.basename(file_name)
    return sorted(paths,  key=lambda file_path: int(re.findall(regex, os.path.basename(file_path))[0]))


# class time:

#     def wrapper(self):
#         pass

# 需要一个获取随机生成不可能重复的字符串


def get_unique_str() -> str:
    """ 获取含有时序信息的名唯一字符串 """
    return f'{time.time()}'


def imgs2pdf(sorted_paths: List[str], output_dir=None, file_name='temp') -> str:
    """ 将图片转换为pdf, 并返回pdf的本地路径

    @Notice 如果不传入输出目录, 则直接生成在图片的目录下, 并且返回pdf文件的本地路径
    @Notice 如果文件已经存在则直接使用, 不会重新生成和覆盖

    return:
        if file_name = 'temp' then {name}_{get_unique_str()}.pdf

    @MODIFIED img2pdf是一个库, 函数不能重名 所以改为 imgs2pdf
    @RISKED 新的视频和旧的视频重名了（通过重命名 | 覆盖 方式，已经解决）
    @SOLUTION 所以可以考虑为每个视频生成md5(指纹), 就可以避免已经存在的文件, 重新加载
    """
    if not sorted_paths:
        return None
    if output_dir is None:
        """
            Example: D:/t\\a/b.cn
        """
        output_dir = os.path.dirname(sorted_paths[0])
    # img_file = "myImg.jpg"  # 图片路径

    pdf_file_path = \
        os.path.join(output_dir, f'{file_name}_{get_unique_str()}.pdf') \
        if file_name == 'temp' \
        else os.path.join(output_dir, f'{file_name}.pdf')
    # 创建一个PDF文件 并以二进制方式写入
    print(f'pdf_file_path: {pdf_file_path}')
    print(Path(pdf_file_path).exists())
    if not Path(pdf_file_path).exists():
        with open(pdf_file_path, "wb") as f:
            # convert函数 用来转PDF
            write_content = img2pdf.convert(sorted_paths)
            f.write(write_content)  # 写入文件
        print(f"pdf生成成功: {pdf_file_path}")  # 提示语
    return pdf_file_path


def calculate_runtime(func, *args, **kwargs):
    start_time = time.time()
    func(*args, **kwargs)
    end_time = time.time()
    print(f'运行时间: {end_time - start_time}')


def timeIntervalClear(del_path, search_clear_period_seconds=args.search_result_restore_time_seconds) -> Thread:
    """ 定时删除某个目录或者问价，构建一个删除队列 """

    def temp(del_path):
        time.sleep(search_clear_period_seconds)
        print(f'即将删除:{del_path}')
        if(Path(del_path).is_file()):
            os.remove(del_path)
        else:
            shutil.rmtree(del_path, ignore_errors=True)
    Thread(target=temp, args=(del_path,)).start()


class EvaluateTime:
    def __init__(self, note=None):
        self.start_time = 0
        self.end_time = 0
        self.note = note

    def __enter__(self):
        self.start_time = time.time()

    def __exit__(self, exc_type, exc_value, trace):
        self.end_time = time.time()
        self.__calculate_time()

    def __calculate_time(self):
        print("==================== Evaluate Time =====================")
        print(f'{f"note: {self.note}" if self.note else ""} | spend time: {self.end_time - self.start_time}')
        print("========================================================")
 