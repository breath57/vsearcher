from dataclasses import dataclass
from paddleocr import draw_ocr


@dataclass
class Base:
    create_time: str
    delete_time: str
    update_time: str


@dataclass
class Frame:
    id: int
    name: str
    title: list
    img: str
    ms: int
    time: str
    txts: list
    boxes: list

    def draw_boxes(self):
        # draw_ocr()
        # 读取图片 -> 画圈保存-> 临时保存? -> 还是给前端自己画

    def isEmpty(self):
        return len(self.boxes) == 0


@dataclass
class Video:
    id: int
    name: str
    chapter_id: int
    kfs: list

    def isEmpty(self):
        return len(self.kfs) == 0


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
