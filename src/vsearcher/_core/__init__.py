# -*- encoding: utf-8 -*-
'''
@description: vsearcher entry module
@author: breath57
@email: breath57@163.com
'''
import os
from pathlib import Path
import shutil
from typing import Optional

import filetype

from .decorate import Maintain

from .._core.type import Type

from .._config import args
from .._config.path import RootPath
from .._core.video import Assember, DelAnd2Pickle, Video, Chapter, Course, Searcher
from .._core import vo


class Config:
    """ VSearcher的配置类

    类变量:
        args: 为一些基础的配置参数 \n
        rootPath: 与根路径相关的配置参数, 包括: 输出路路径, 模型路径等 \n
        performance: 与性能相关的配置参数, 包括: 是否使用GPU, 多线程, 多进程等
    """
    args = args
    rootPath = RootPath
    performance = args.Performance


class VSearcher:
    """ 所有vsearcher提供的方法和配置都可以通过该类(无需创建实例)进行使用 """

    config: Config = Config

    @classmethod
    def init(
        cls,
        domain_url: str = None, project_root_dir: str = None,
        static_folder: str = "static",
        output_dir="vs-output",
        step: Type[int, 'fps'] = args.step,
        speed_x: float = args.speed_x,
        ocr_model_dir: str = None
    ):
        """ 初始化与VSearcher后续处理相关的配置

        args:
            domain_url: 外部访问静态资源时的URL前半部分，例如：http://{domain_url}/a/b.mp4; 
                若设置：后续的处理结果中的资源路径，将为url路径(http://{domain_url}/a/b.mp4);

                不设置：结果将返回本地路径(a/b.mp4);

            project_root_dir: 默认为__main__文件所在目录的路径
            step: 视频遍历的帧间隔, 越大速度越快, 当取值为'fps'是为视频的帧率
            speed_x: 对step进行整数倍的加速, 即 最终的step = step * speed_x
            ocr_model_dir: 含有.pdmodel文件的目录相对路径, 默认为: ocrv3模型
            static_folder: 可以外部url访问的静态文件夹的目录路径, 该路径是相对于项目的根路径
            output_dir: vsearch处理结果输出的保存的相对于static_folder的路径, 即: 实际的输出目录为: {static_folder}/{output_dir}
        """
        # @RISK 以下初始化顺序最好不要有改动
        cls.config.rootPath.set_project_dir(project_root_dir or "")
        cls.config.args.url_prefix = domain_url
        cls.setStep(step, speed_x)
        cls.setPaddleOcrModelDir(ocr_model_dir)
        # 如下两方法顺序不可以变
        cls.setStaticDir(static_folder)
        cls.setOutputDir(relative_static_folder_path=output_dir)
        Assember.setOCR()  # 创建OCR对象

    @classmethod
    def setPaddleOcrModelDir(cls, model_dir: str = None):
        """ 指定使用paddle模型

        args:
            model_dir: 模型的目录路径

        默认使用的模型:
            rec: ch_ppocr_mobile_v2.0_rec_infer
            det: ch_ppocr_mobile_v2.0_det_infer
        可参考：https://gitee.com/paddlepaddle/PaddleOCR/blob/release/2.5/doc/doc_ch/models_list.md
        """
        cls.config.rootPath.set_model_dir(model_dir)

    @classmethod
    def setOutputDir(cls, relative_static_folder_path: str):
        """ 设置输出路径

        args:
            relative_static_folder_path: 该路径是相对于输出项目的相对路径

        示例: 
            假设:
                relative_static_folder_path: c/d
                project_dir: a/b

            最终的输出路径: {project_dir}/{relative_static_folder_path}, 即 a/b/c/d
        """
        cls.config.rootPath.set_output_dir(relative_static_folder_path)

    @classmethod
    def setStaticDir(cls, relative_project_dir_path: str):
        """ 设置静态文件夹路径

        args:
            relative_project_dir_path: 该路径是相对于输出项目的相对路径 
        示例：

            假设:
                project_dir: E://a/b/project_dir
                relative_project_dir_path: x

            那么:
                real static path is {project_dir}/{relative_project_dir_path}
                url_prefix_local_path: {project_dir}/x

            当:
                img_local_path: E://a/b/project_dir/x/ff/ss/c.png

            那么:
                url: http://localhost:5000/ff/ss/c.png
        """
        if relative_project_dir_path:
            cls.config.rootPath.set_static_folder_dir(
                relative_project_dir_path)

    @classmethod
    def setStep(cls, step: Type[int, 'fps'], speed_x: float):
        """ 设置全局默认step

        args:
            step: 视频遍历的帧间隔, 越大速度越快, 当取值为'fps'是为视频的帧率
            speed_x: 对step进行整数倍的加速, 即 最终的step = step * speed_x
         """
        Assember.set_step(step=step, speed_x=speed_x)

    @classmethod
    def executeVideo(
        cls,
        video_file_path: str,
        video_name: str = None,
        step: Type[int, 'fps'] = args.step,
        speed_x: float = args.speed_x,
        output_dir: str = None
    ) -> vo.VideoVO:
        """ 处理视频,并返回处理结果

        args:
            video_file_path: 视频文件的本地路径
            video_name: 默认自动从路径中获取
            step: 视频遍历的帧间隔, 越大速度越快, 当取值为'fps'是为视频的帧率
            speed_x: 对step进行整数倍的加速, 即 最终的step = step * speed_x
            output_dir: 处理过程中产生的输出结果存放的目录, 若该处不指定, 且也没有进行VSearcher.init()的初始化, 则路径为{project_dir}/static/vsearch-output/videos

        return: 
            vo.VideoVO
        """
        if not Path(video_file_path).exists():
            raise RuntimeError(f'路径: {video_file_path} 不存在!')
        if not filetype.is_video(video_file_path):
            raise RuntimeError(
                f'传入的路径: {video_file_path} 不是视频, 或传入的视频没有视频信息()')
        video = Assember.executeVideo(
            video_path=video_file_path, name=video_name, step=step, speed_x=speed_x, output_dir=output_dir)
        return vo.VideoVO.create(video=video)

    @classmethod
    def createCourseDir(cls, course_name: str) -> str:
        """ 创建课程资源对应的目录, 并返回路径

        args:
            course_name: 课程名称

        return: output_dir
        """
        return Assember.createPureDir(course_name=course_name)

    @classmethod
    def createChapterDir(cls, chapter_name: str, course_name: str) -> str:
        """ 创建章节资源对应的目录, 并返回路径

        args:
            chapter_name: 章节名称
            course_name: 课程名称

        return: output_dir
        """
        return Assember.createPureDir(chapter_name=chapter_name, course_name=course_name)

    @classmethod
    def executeChapter(
        cls,
        chapter_dir_path: str,
        chapter_name: Optional[str] = None,
        step: Type[int, 'fps'] = args.step,
        speed_x: float = args.speed_x
    ) -> vo.ChapterVO:
        """ 处理章节,并返回处理结果

        args:
            chapter_dir_path: 章节的根目录, 即该目录下含有一个或以上的视频
            chapter_name: 默从路径中自动获取
            step: 视频遍历的帧间隔, 越大速度越快, 当取值为'fps'是为视频的帧率
            speed_x: 对step进行整数倍的加速, 即 最终的step = step * speed_x
            output_dir: 处理过程中产生的输出结果存放的目录, 若该处不指定, 且也没有进行VSearcher.init()的初始化, 则路径为{project_dir}/static/vsearch-output/videos

        return: 
            vo.ChapterVO
        """
        if not Path(chapter_dir_path).exists():
            print(f'路径: {chapter_dir_path} 不存在!')
            return None
        chapter = Assember.executeChapter(
            chapter_dir_path=chapter_dir_path, chapter_name=chapter_name, step=step, speed_x=speed_x)
        return vo.ChapterVO.create(chapter)

    @classmethod
    def executeCourse(
        cls,
        course_dir_path: str,
        course_name: str = None,
        step: Type[int, 'fps'] = args.step,
        speed_x: float = args.speed_x
    ) -> vo.CourseVO:
        """ 处理课程,并返回处理结果

        args:
            course_dir_path: 课程的根目录, 即该目录下含有一个或以上的章节
            course_name: 默从路径中自动获取
            step: 视频遍历的帧间隔, 越大速度越快, 当取值为'fps'是为视频的帧率
            speed_x: 对step进行整数倍的加速, 即 最终的step = step * speed_x
            output_dir: 处理过程中产生的输出结果存放的目录, 若该处不指定, 且也没有进行VSearcher.init()的初始化, 则路径为{project_dir}/static/vsearch-output/videos

        return: 
            vo.CourseVO
        """
        if not Path(course_dir_path).exists():
            print(f'路径: {course_dir_path} 不存在!')
            return None
        course = Assember.executeCourse(
            course_dir_path=course_dir_path, course_name=course_name, step=step, speed_x=speed_x)
        return vo.CourseVO.create(course)

    @classmethod
    def loadResource(cls, o_path: str) -> vo.ResourceVO:
        """ 将处理输出的pickle对象文件, 载入为python的vo.Resource的父类对象

        args:
            o_path: vo.对象的本地路径
        """
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
    def releaseResource(cls, o_or_path: Type[vo.ResourceVO, str]) -> None:
        """ 释放o_path对应的pickle对象对应的所有存储资源

        args:
            o_or_path: [vo.ResourceVO], 即调用execute{Chapter | Course | Video}()返回的对象, 或者对象中o_path属性对应的pickle对象路径
        """
        if isinstance(o_or_path, vo.ResourceVO):
            o_or_path.release()
        else:
            o = DelAnd2Pickle.loadPickle(o_path=o_or_path)
            o.releaseResource()

    @Maintain.deprecating
    @classmethod
    def search(cls, o_or_path: Type[vo.ResourceVO, str], key: str, json_dumps=False) -> vo.ResourceVO:
        """ 搜索某个资源的内容 

        args:
            o_or_path: [vo.ResourceVO], 即调用execute{Chapter | Course | Video}()返回的对象, 或者对象中o_path属性对应的pickle对象路径
            key: 关键字

        return: vo.{Chapter | Course | Video}VO 对象作为结果
        """
        if isinstance(o_or_path, vo.ResourceVO):
            return o_or_path.search(key=key, json_dumps=json_dumps)
        return Searcher(o_or_path=o_or_path).search(key)

    @Maintain.deprecating
    @classmethod
    def releaseByOutputDir(cls, output_dir: str) -> None:
        """ 释放处理产生的输出文件, 包括： 1. 注释文件 2.视频文件 3.图片文件 4. 课件 @WAIT（或许实时生成比较好，就是get的时候进行获取文件） 

        args:
            output_dir: vo.ResourceVO对象的output_dir属性, 执行execute{Chapter | Course | Video}()方法时, 设置的output_dir
        """
        if os.path.exists(output_dir):
            shutil.rmtree(output_dir, ignore_errors=True)
