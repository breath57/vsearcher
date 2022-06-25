import os
from pathlib import Path
import shutil

import filetype

from .._config import args, path
from .._config.path import RootPath
from .._core.video import Assember, DelAnd2Pickle, Video, Chapter, Course, Searcher
from .._core import vo


class Config:

    args = args
    path = path
    RootPath = RootPath
    performance = args.Performance


class VSearcher:

    config: Config = Config

    def __init__(self, url_prefix, domain_url, step, speed_x):
        # 模仿学习那种参数
        # self.config = Config()
        pass

    @classmethod
    def init(cls, domain_url='http://localhost:5000', static_folder="static", output_dir="vs-output", step='fps', speed_x=1, ocr_model_dir=None):
        """
        domain_url: 外部访问静态资源时的URL前半部分
        step: 视频遍历的帧间隔, 越大速度越快
        speed_x: 对step进行整数倍的加速, 即 最终的step = step * speed_x
        ocr_model_dir: 含有.pdmodel文件的目录相对路径, 默认为: ocrv2模型
        static_folder: 可以外部url访问的静态文件夹的目录路径, 该路径是相对于项目的根路径
        output_dir: vsearch处理结果输出的保存的相对于static_folder的路径, 即: 实际的输出目录为: {static_folder}/{output_dir}
        """
        # cls.set_name_(_name_)
        cls.config.args.url_prefix = domain_url
        cls.set_step(step, speed_x)
        cls.set_paddle_ocr_model_dir(ocr_model_dir)
        cls.set_static_dir(static_folder)
        cls.set_output_dir(output_dir)

    # @classmethod
    # def set_name_(cls, _name_):
    #     cls.config.RootPath.set_project_dir(_name_)

    @classmethod
    def set_paddle_ocr_model_dir(cls, model_dir=None):
        """
        model_dir: 'resource/model/ocr/paddle'
        default:
            rec: ch_ppocr_mobile_v2.0_rec_infer
            det: ch_ppocr_mobile_v2.0_det_infer
        可参考：https://gitee.com/paddlepaddle/PaddleOCR/blob/release/2.5/doc/doc_ch/models_list.md
        """
        cls.config.RootPath.set_model_dir(model_dir)

    def __init_path(self):
        pass

    @classmethod
    def set_output_dir(cls, relative_static_folder_path):
        cls.config.RootPath.set_output_dir(relative_static_folder_path)

    @classmethod
    def set_static_dir(cls, relative_project_dir_path):
        """ 设置URL替换前缀路径
        例如：
            project_dir: E://a/b/project_dir
            img_local_path: E://a/b/project_dir/x/ff/ss/c.png
            relative_project_dir_path: x
            url_prefix_local_path: {project_dir}/x
            url: http://localhost:5000/ff/ss/c.png
        """
        if relative_project_dir_path:
            cls.config.RootPath.set_static_folder_dir(
                relative_project_dir_path)

    @classmethod
    def set_step(cls, step, speed_x):
        """ 设置全局默认step """
        Assember.set_step(step=step, speed_x=speed_x)

    @classmethod
    def executeVideo(cls, video_file_path, video_name=None, step=None, speed_x=None, output_dir=None) -> vo.VideoVO:
        """ video_name: if None 则为 video_file_path 所示的名字 """
        if not Path(video_file_path).exists():
            print(f'路径: {video_file_path} 不存在!')
            return None
        if not filetype.is_video(video_file_path):
            print(f'传入的路径: {video_file_path} 不是视频')
            return None
        video = Assember.executeVideo(
            video_path=video_file_path, name=video_name, step=step, speed_x=speed_x, output_dir=output_dir)
        return vo.VideoVO.create(video=video)

    @classmethod
    def createCourseDir(cls, course_name):
        """ 
        创建资源对应的目录, 并返回路径
        type: course | chapter 
        return: output_dir
        """
        return Assember.createPureDir(course_name=course_name)

    @classmethod
    def createChapterDir(cls, chapter_name, course_name):
        """ 
        创建资源对应的目录, 并返回路径
        type: course | chapter 
        return: output_dir
        """
        return Assember.createPureDir(chapter_name=chapter_name, course_name=course_name)

    @classmethod
    def executeChapter(cls, chapter_dir_path, step=None, speed_x=None) -> vo.ChapterVO:
        if not Path(chapter_dir_path).exists():
            print(f'路径: {chapter_dir_path} 不存在!')
            return None
        chapter = Assember.executeChapter(
            chapter_dir_path=chapter_dir_path, step=step, speed_x=speed_x)
        return vo.ChapterVO.create(chapter)

    @classmethod
    def executeCourse(cls, course_dir_path, step=None, speed_x=None) -> vo.CourseVO:
        if not Path(course_dir_path).exists():
            print(f'路径: {course_dir_path} 不存在!')
            return None
        course = Assember.executeCourse(
            course_dir_path=course_dir_path, step=step, speed_x=speed_x)
        return vo.CourseVO.create(course)

    @classmethod
    def loadResource(cls, o_path):
        if not Path(o_path).exists():
            raise ValueError('o_path不存在')
        o = DelAnd2Pickle.loadPickle(o_path)
        if isinstance(o, Video):
            return vo.VideoVO.create(o)
        elif isinstance(o, Chapter):
            return vo.ChapterVO.create(o)
        elif isinstance(o, Course):
            return vo.CourseVO.create(o)

    @classmethod
    def releaseResource(cls, o_path):
        """ 释放o_path对应的pickle对象对应的所有存储资源 """
        o = DelAnd2Pickle.loadPickle(o_path=o_path)
        o.releaseResource()

    @classmethod
    def search(cls, o_or_path, key):
        return Searcher(o_or_path=o_or_path).search(key)

    @classmethod
    def releaseByOutputDir(cls, output_dir):
        """ 释放处理产生的文件： 1. 注释文件 2.视频文件 3.图片文件 4. 课件 @WAIT（或许实时生成比较好，就是get的时候进行获取文件） """
        if os.path.exists(output_dir):
            shutil.rmtree(output_dir, ignore_errors=True)
