# -*- encoding: utf-8 -*-
'''
@description: view models
@author: breath57
@email: breath57@163.com
'''
from abc import abstractmethod, abstractstaticmethod
from dataclasses import dataclass
import os
import shutil
from typing import List
from .._config import args
from . import utils


class BaseVO:
    """ 定义抽象接口 """

    @abstractmethod
    def isEmpty(self) -> bool:
        """ 判断内容是否为空 """
        raise NotImplementedError("BaseVO.isEmpty() is not implemented")

    @abstractstaticmethod
    def create(object):
        """ 返回 video中的Video|Chapter|Course对象 对应 的VO对象"""
        raise NotImplementedError("BaseVO.create() is not implemented")

    def json(self) -> str:
        """ 发回序列化后的json字符串 """
        return utils.json_dumps(self)


@dataclass
class FrameVO(BaseVO):
    id: int  # 帧的id编号，具体为该帧在视频中的帧数
    name: str  # 帧的别名
    title: list  # 该帧对应的标题
    img: str  # 帧对应图片的url地址，[生成的原理]()
    img_local_path: str  # 帧对应图片的本地路径
    ms: int  # 帧对应的视频中的时间位置，单位：毫秒
    time: str  # 帧对应视频中的时间字符串
    txts: list  # 帧所含文本内容的列表
    boxes: list  # 帧所含文本框的位置信息

    # def draw_boxes(self):
    # draw_ocr()
    # 读取图片 -> 画圈保存-> 临时保存? -> 还是给前端自己画

    def isEmpty(self):
        return len(self.boxes) == 0

    @staticmethod
    def create(pf) -> BaseVO:
        return FrameVO(id=pf.id,
                       name=pf.name,
                       title=pf.getTitles(args.title_num),
                       img=pf.img,
                       img_local_path=pf.img_local_path,
                       ms=pf.ms,
                       txts=pf.txts,
                       boxes=pf.boxes,
                       time=utils.msToH_M_S_str(pf.ms))


class VOExtend:
    """ 扩展VO的能力 """

    def search(self, key, json_dumps=False, search_result_restore_time_seconds=None) -> BaseVO:
        """ 搜索对象中的内容，搜索结果超出{search_result_restore_time_seconds}时间后自动进行清理

        args:
            key: 搜索内容
            json_dumps: 返回的结果是否需要json序列化
            search_result_restore_time_seconds: 搜索结果保留的时间, 默认配置文件中的args.search_result_restore_time_seconds, 超出时间将自动进行清理

        return vo.BaseVO
        """
        from .video import Searcher  # 为了避免循环导入，所以放这里
        return Searcher(self.o_path).search(key, json_dumps=json_dumps, search_result_restore_time_seconds=search_result_restore_time_seconds)

    def release(self):
        """ 释放处理产生的输出文件, 包括： 1. 注释文件 2.视频文件 3.图片文件 4. 课件

        args:
            output_dir: 执行execute{Chapter | Course | Video}()方法时, 设置的output_dir
        """
        if not hasattr(self, 'output_dir'):
            raise AttributeError(
                "对象不存在属性: output_dir, 无法使用release()方法")

        if os.path.exists(self.output_dir):
            shutil.rmtree(self.output_dir, ignore_errors=True)


class ResourceVO(BaseVO, VOExtend):
    """ 记录资源的输出路径，和释放输出路径对应的资源 """
    o_path: str  # pickle对象所在的路径
    output_dir: str  # 资源的输出路径


@dataclass
class VideoVO(ResourceVO):
    id: int  # id
    name: str  # 视频名称
    local_path: str  # 视频的本地路径
    chapter_id: int  # 视频所属章节的id
    kfs: List[FrameVO]  # 关键帧列表
    url: str  # 视频的url路径
    img: str  # 封面图片的url路径，该图片为关键帧作的第一帧
    o_path: str  # 内部对象的路径，可以通过[VSearcher.loadResource(o_path)]进行读取
    cw: str  # 生成课件的url路径
    cw_local: str  # 生成课件的本地路径
    output_dir: str  # 资源的输出目录路径
    step: int  # 处理视频时的帧间隔 | 即，每间隔step帧读取一次视频帧
    speed_x: float  # real step = step * speed_x

    def isEmpty(self):
        return len(self.kfs) == 0
    # 不支持构造方法重载，可惜了
    # def __init__(self, id, kfs, name, local_path, chapter_id):
    #     self.id = id
    #     self.kfs = kfs
    #     self.name = name
    #     self.local_path = local_path
    #     self.chapter_id = chapter_id

    # def __init__(self, video: video.Video):
    #     self.id = video.id
    #     self.name = video.name
    #     self.local_path = video.local_path
    #     self.chapter_id = video.chapter_id
    #     self.kfs = video.getAllKfs()

    @staticmethod
    def create(video) -> BaseVO:
        return VideoVO(id=video.id, name=video.name,
                       local_path=video.local_path,
                       chapter_id=video.chapter_id,
                       kfs=[FrameVO.create(pf) for pf in video.kfs],
                       img=video.kfs[0].img if len(video.kfs) > 0 else None,
                       url=utils.local2url(video.local_path),
                       o_path=video.o_path,
                       output_dir=video.output_dir,
                       cw=video.courseware_url,
                       cw_local=video.courseware_path,
                       step=video.step,
                       speed_x=video.speed_x
                       )


@dataclass
class ChapterVO(ResourceVO):
    id: int  # id
    name: str  # 章节名称
    course_id: int  # 章节所属课程的课程id
    videos: List[VideoVO]  # 章节下的所有视频对象
    output_dir: str  # 资源的输出目录路径

    def isEmpty(self):
        return len(self.videos) == 0

    @staticmethod
    def create(chapter) -> BaseVO:
        return ChapterVO(id=chapter.id, name=chapter.name,
                         course_id=chapter.course_id, videos=[
                             VideoVO.create(v) for v in chapter.videos],
                         output_dir=chapter.output_dir)


@dataclass
class CourseVO(ResourceVO):
    id: int  # 课程id
    name: str  # 课程名称
    chapters: List[ChapterVO]  # 课程下的所有ChapterVO对象
    output_dir: str  # 资源的输出目录路径

    def isEmpty(self):
        return len(self.chapters) == 0

    @staticmethod
    def create(course):
        return CourseVO(id=course.id, name=course.name,
                        chapters=[ChapterVO.create(c)
                                  for c in course.chapters],
                        output_dir=course.output_dir)
