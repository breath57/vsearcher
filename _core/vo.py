from dataclasses import dataclass
from typing import List

from .._config import args
from . import utils


@dataclass
class Base:
    # 目前不需要
    create_time: str
    delete_time: str
    update_time: str


# @WAIT 通过反射机制，或者继续学习flask
@dataclass
class FrameVO:
    id: int
    name: str
    title: list
    img: str
    img_local_path: str  # @WAIT 没必要返回
    ms: int
    time: str
    txts: list  # @WAIT 没必要返回 | 全都返回，数据裁剪不应该这里做
    boxes: list  # @WAIT 没必要返回

    # def draw_boxes(self):
    # draw_ocr()
    # 读取图片 -> 画圈保存-> 临时保存? -> 还是给前端自己画

    def isEmpty(self):
        return len(self.boxes) == 0

    @staticmethod
    def create(pf):
        return FrameVO( id=pf.id,
                        name=pf.name,
                        title=pf.getTitles( args.title_num ),
                        img=pf.img,
                        img_local_path=pf.img_local_path,
                        ms=pf.ms,
                        txts=pf.txts,
                        boxes=pf.boxes,
                        time=utils.msToH_M_S_str( pf.ms ) )


@dataclass
class VideoVO:
    id: int
    name: str
    local_path: str
    chapter_id: int
    kfs: List[FrameVO]
    url: str
    img: str
    o_path: str
    cw: str
    output_dir: str

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
    def create(video):
        return VideoVO( id=video.id, name=video.name,
                        local_path=video.local_path,
                        chapter_id=video.chapter_id,
                        kfs=[FrameVO.create(pf) for pf in video.kfs],
                        img=video.kfs[0].img if len(video.kfs) > 0 else None,
                        url=utils.local2url( video.local_path ),
                        o_path=video.o_path,
                        output_dir=video.output_dir,
                        cw=video.courseware_url
                        )


@dataclass
class ChapterVO:
    id: int
    name: str
    course_id: int
    videos: List[VideoVO]
    # o_path: str
    output_dir: str

    def isEmpty(self):
        return len(self.videos) == 0

    @staticmethod
    def create(chapter):
        return ChapterVO(id=chapter.id, name=chapter.name,
                         course_id=chapter.course_id, videos=[
                             VideoVO.create(v) for v in chapter.videos],
                         output_dir=chapter.output_dir)


@dataclass
class CourseVO:
    id: int
    name: str
    chapters: List[ChapterVO]
    output_dir: str

    def isEmpty(self):
        return len(self.chapters) == 0

    @staticmethod
    def create(course):
        return CourseVO(id=course.id, name=course.name,
                        chapters=[ChapterVO.create(c)
                                  for c in course.chapters],
                        output_dir=course.output_dir)
