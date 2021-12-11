from  dataclasses import dataclass


@dataclass
class Base:
    create_time: str
    delete_time: str
    update_time: str



@dataclass
class Frame():
    id: int
    img: str
    boxes: list
    name: str
    txts: list
    title: list

    def isEmpty(self):
        return len(self.boxes) == 0

@dataclass
class Video():
    id: int
    kfs: list
    name: str
    chapter_id: int

    def isEmpty(self):
        return len(self.kfs) == 0


@dataclass
class Chapter():
    id: int
    videos: list
    name: str
    course_id: int

    def isEmpty(self):
        return len( self.videos ) == 0

@dataclass
class Course():
    id: int
    chapters: list
    name: str

    def isEmpty(self):
        return len(self.chapters) == 0