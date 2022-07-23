# -*- encoding: utf-8 -*-
'''
@description: 路径相关配置, 包括: 项目、输出、模型等路径
@author: breath57
@email: breath57@163.com
'''

from inspect import ismethod
import os
from pathlib import Path


class RootPath:
    """ 命名规范: 目录变量名以 "_dir"为结尾 """

    # 当前项目的根路径
    project_root_dir = "" # 默认为__main__所在目录路径

    # 外部可访问的静态文件夹
    static_folder_dir = str(
        Path(project_root_dir).joinpath("static"))  # 静态文件夹路径, 默认值
    # 静态文件夹的前缀 a/c/static -> a/c
    static_folder_dir_prefix = str(Path(static_folder_dir).parent)
    # | 作用: 用于锁定url 例如: a/c/e.png -> url: http://xxx/a/c/e.png 但是 static_url为 http://xxx/c/e.png才能访问
    # 输出目录的路径
    output_dir = str(Path(static_folder_dir, 'vsearch-output'))

    # 搜索结果输出目录
    output_search_result_dir = str(Path(output_dir).joinpath('search-result'))

    # 处理视频后产生的关键图片保存的路径
    output_courses_dir = str(Path(output_dir).joinpath('courses'))
    output_chapters_dir = str(Path(output_dir).joinpath('chapters'))
    output_videos_dir = str(Path(output_dir).joinpath('videos'))

    # paddleocr 文字检测 和 文字分类模型 | 最新版可以自行去git的paddleocr查看, 将此处的路径末尾改名字即可自动下载
    det_model_dir, rec_model_dir = None, None  # 导入训练好的机器学习模型路径

    @classmethod
    def set_model_dir(cls, dir_path):
        """ dir_path: 项目相对路径
        case: {project_dir}/{dir_path}/**mobile**/inference.pdmodel
        """
        base_path = Path(cls.project_root_dir).joinpath(dir_path)
        result = list(base_path.glob('*det*'))
        # 判断是否真的存在模型文件
        if len(result) == 0 or len(list(result[0].glob('*.pdmodel'))) == 0:
            print(f'路径: {dir_path} |  没有det模型文件, 将使用默认的模型文件')
        else:
            print(f'使用的检测模型为: {result[0].stem}')
            cls.det_model_dir = str(result[0])
        result = list(base_path.glob('*rec*'))
        # 判断是否真的存在模型文件
        if len(result) == 0 or len(list(result[0].glob('*.pdmodel'))) == 0:
            print(f'路径: {dir_path} |  没有rec模型文件, 将使用默认的模型文件')
        else:
            print(f'使用的识别模型为: {result[0].stem}')
            cls.rec_model_dir = str(result[0])
        print(
            f'ocr_det_dir: {cls.det_model_dir}\nocr_rec_dir: {cls.rec_model_dir}')

    @classmethod
    def join_output_dir(cls, path):
        return str(Path(cls.output_dir, path))

    @classmethod
    def set_project_dir(cls, project_root_dir):
        old_project_root_dir = cls.project_root_dir or ""
        print(
            f'old_project_root_dir: {old_project_root_dir}\nproject_root: {project_root_dir}')
        print("=========路径更新前========")
        for key, value in cls.__dict__.items():
            if "_dir" in key and value is not None \
                    and key != 'project_root_dir' \
                    and not isinstance(value, classmethod) \
                    and not isinstance(value, staticmethod) \
                    and not ismethod(value):  # paddle的路径可以为None
                print(f'{key}: {value}')
                if old_project_root_dir == "" or old_project_root_dir == '.':  # 原先没有值
                    setattr(cls, key, str(Path(project_root_dir, value)))
                else:  # 原先不为空
                    setattr(cls, key, value.replace(
                        old_project_root_dir, project_root_dir))
        cls.project_root_dir = project_root_dir  # 完全替换
        print("=========路径更新后========")
        for key, value in cls.__dict__.items():
            if "_dir" in key \
                    and not isinstance(value, classmethod) \
                    and not isinstance(value, staticmethod) \
                    and not ismethod(value):  # paddle的路径可以为None
                print(f'{key}: {value}')

    # | 此时就有用了

    @classmethod
    def set_output_dir(cls, relative_static_folder_path: str = ""):
        """
             {project_dir}/{static_folder_dir}/${relative_static_folder_path}
        """
        print(f'old_output_dir: {cls.output_dir}')
        if relative_static_folder_path[0] in ['/', '\\']:  # 为了避免变为F:/a/b的绝对路径
            relative_static_folder_path = relative_static_folder_path[1:]
        cls.output_dir = str(
            Path(cls.static_folder_dir, relative_static_folder_path))

        print(f'new_output_dir: {cls.output_dir}')
        # 与output_dir有关的所有路径都需要重置
        cls.output_courses_dir = cls.join_output_dir('courses')
        cls.output_chapters_dir = cls.join_output_dir('chapters')
        cls.output_videos_dir = cls.join_output_dir('videos')
        cls.output_search_result_dir = cls.join_output_dir('search-result')

    @classmethod
    def set_static_folder_dir(cls, relative_project_dir_path):
        """ 设置URL替换前缀路径
        例如：
            project_dir: E://a/b/project_dir
            img_local_path: E://a/b/project_dir/x/ff/ss/c.png
            relative_project_dir_path: x
            url_prefix_local_path: {project_dir}/x
            url: http://localhost:5000/ff/ss/c.png
        """
        old_static_folder_dir = cls.static_folder_dir
        cls.static_folder_dir = os.path.join(
            cls.project_root_dir, relative_project_dir_path)
        cls.static_folder_dir_prefix = str(Path(cls.static_folder_dir).parent)

        # 更新基于此的输出路径
        for k, v in cls.__dict__.items():
            if k.startswith('output_'):
                setattr(cls, k, v.replace(
                    old_static_folder_dir, cls.static_folder_dir))
