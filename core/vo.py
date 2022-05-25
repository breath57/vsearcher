from dataclasses import dataclass
from . import  utils

@dataclass
class Base:
    create_time: str
    delete_time: str
    update_time: str


# @WAIT 通过反射机制，或者继续学习flask
@dataclass
class Frame:
    id: int
    name: str
    title: list
    img_url: str
    img_local_path: str  # @WAIT 没必要返回
    ms: int
    time: str
    txts: list  # @WAIT 没必要返回
    boxes: list  # @WAIT 没必要返回

    # def draw_boxes(self):
    # draw_ocr()
    # 读取图片 -> 画圈保存-> 临时保存? -> 还是给前端自己画

    def isEmpty(self):
        return len(self.boxes) == 0

    @staticmethod
    def create(pf):
        return Frame( id=pf.id, name=pf.get_name(), title=pf.getTitles(), img_url=pf.img_url,
                      img_local_path=pf.img_local_path, ms=pf.ms, txts=pf.txts,
                      boxes=pf.boxes, time=utils.msToH_M_S_str( pf.ms ) )


@dataclass
class Video:
    id: int
    name: str
    local_path: str
    chapter_id: int
    kfs: list
    url: str

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
    #     self.kfs = video.getKfs()
    @staticmethod
    def create(video):
        return Video(id=video.id, name=video.name,
                     local_path=video.local_path,
                     chapter_id=video.chapter_id,
                     kfs=[Frame.create(pf) for pf in video.getKfs()],
                     url=utils.local2url( video.local_path )
                     )


@dataclass
class Chapter:
    id: int
    name: str
    course_id: int
    videos: list

    def isEmpty(self):
        return len(self.videos) == 0


@dataclass
class Course:
    id: int
    name: str
    chapters: list

    def isEmpty(self):
        return len(self.chapters) == 0
