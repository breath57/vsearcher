
# ['__builtins__', '__cached__', '__doc__', '__file__', '__loader__', '__name__', '__package__', '__spec__']
import glob
import os
from pathlib import Path

from .args import Performance as performance_config


# @RISK 路径的生成问题, 需要统一用 Path拼接, 不然换个系统就没用了
def getProjectRootPath(_name_):
    # r = str(Path(__name__.replace('.', '\\')))
    # i = __file__.index(r)
    # return __file__[: i-1]
    # return "F:\Document\研究生总汇\其他\open-source\\vsearch\pypi\src"
    return ""
    # if _name_ == '__main__':
    #     return ""
    # res =  _name_.split('.')
    # if len(res) == 1:
    #     return ""
    # path = Path()
    # for p in res[1:]:
    #     path.joinpath(p)
    # return str(path)


def getThisPackageRootPath():
    return ''


# 路径生成辅助函数

# def load_ocr_path(model_dir, paddle_name):
#     ''' 用于生成ocr路径 '''
#     det_path = glob.glob(f'{model_dir}\\ocr\\{paddle_name}\\*det*')
#     if len(det_path) == 0:
#         print(f'路径: {model_dir}\\ocr\\{paddle_name} |  没有det模型文件, 将使用默认的模型文件')
#         det_path = None
#     rec_path = glob.glob(f'{model_dir}\\ocr\\{paddle_name}\\*rec*')
#     if len(rec_path) == 0:
#         print( f'路径: {model_dir}\\ocr\\{paddle_name} |  没有rec模型文件, 将使用默认的模型文件' )
#         rec_path = None
#     return det_path, rec_path
#     # return None,None


class RootPath:

    # 当前项目的根路径
    project_root_dir = ""

    # 输出目录的路径
    output_dir = str(Path(project_root_dir).joinpath(
        'static').joinpath('vsearch-output'))

    # 搜索结果输出目录
    output_search_result_dir = str(Path(output_dir).joinpath('search-result'))

    # # 处理视频后产生的对象保存的路径
    # output_video_object_dir = f'{output_dir}\\objects\\videos'
    # output_chapter_object_dir = f'{output_dir}\\objects\\chapters'
    # output_course_object_dir = f'{output_dir}\\objects\\courses'

    # 处理视频后产生的关键图片保存的路径
    output_courses_dir = str(Path(output_dir).joinpath('courses'))
    output_chapters_dir = str(Path(output_dir).joinpath('chapters'))
    output_videos_dir = str(Path(output_dir).joinpath('videos'))

    # paddleocr 文字检测 和 文字分类模型 | 最新版可以自行去git的paddleocr查看, 将此处的路径末尾改名字即可自动下载
    det_model_dir, rec_model_dir = None, None  # 导入训练好的机器学习模型路径

    # # 停用词的目录
    # step_word_path = f'{_resource_dir}\\step_word'

    @classmethod
    def set_model_dir(cls, dir_path):
        """ dir_path: 项目相对路径 """
        result = glob.glob(f'{dir_path}/*det*')
        # 判断是否真的存在模型文件
        if len(result) == 0 or len(glob.glob(f'{result[0]}/*.pdmodel')) == 0:
            print(f'路径: {dir_path} |  没有det模型文件, 将使用默认的模型文件')
        else:
            print(f'使用的检测模型为: {Path(result[0]).stem}')
            cls.det_model_dir = result[0]

        result = glob.glob(f'{dir_path}/*rec*')
        # 判断是否真的存在模型文件
        if len(result) == 0 or len(glob.glob(f'{result[0]}/*.pdmodel')) == 0:
            print(f'路径: {dir_path} |  没有rec模型文件, 将使用默认的模型文件')
        else:
            print(f'使用的识别模型为: {Path( result[0] ).stem}')
            cls.rec_model_dir = result[0]

    @classmethod
    def join_output_dir(cls, path):
        return str(Path(cls.output_dir).joinpath(path))

    # @classmethod
    # def set_project_dir(cls, _name_):
    #     cls.project_root_dir = getProjectRootPath(_name_)
    #     print( '-----------------------------------' )
    #     print( f'项目根目录: {RootPath.project_root_dir}' )
    #     print( '-----------------------------------' )

    @classmethod
    def set_output_dir(cls, relative_static_folder_path: str = ""):
        """
             relative_project_dir_path: project_dir/{relative_project_dir_path}
        """
        if relative_static_folder_path[0] in ['/', '\\']:  # 为了避免变为F:/a/b的绝对路径
            relative_static_folder_path = relative_static_folder_path[1:]
        cls.output_dir = str(
            Path(cls.static_folder_dir).joinpath(relative_static_folder_path))
        print(f'output_dir: {cls.output_dir}')
        # 与output_dir有关的所有路径都需要重置
        cls.output_courses_dir = cls.join_output_dir('courses')
        cls.output_chapters_dir = cls.join_output_dir('chapters')
        cls.output_videos_dir = cls.join_output_dir('videos')
        cls.output_search_result_dir = cls.join_output_dir('search-result')

    static_folder_dir = str(
        Path(project_root_dir).joinpath("static"))  # 静态文件夹路径, 默认值
    static_folder_dir_prefix = ""  # 静态文件夹的前缀 a/c/static -> a/c
    # | 作用: 用于锁定url 例如: a/c/e.png -> url: http://xxx/a/c/e.png 但是 static_url为 http://xxx/c/e.png才能访问
    # | 此时就有用了

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
        cls.static_folder_dir = os.path.join(
            cls.project_root_dir, relative_project_dir_path)
        cls.static_folder_dir_prefix = str(Path(cls.static_folder_dir).parent)
