
# ['__builtins__', '__cached__', '__doc__', '__file__', '__loader__', '__name__', '__package__', '__spec__']

def getProjectRootPath():
    r = __name__.replace('.', '\\')
    i = __file__.index(r)
    return __file__[: i-1]


def getThisPackageRootPath():
    r = __name__.replace('.', '\\')
    # @risk 不能随意切换到其他目录, 修复方案: zai, __init__文件中获取相应的项目路径
    i = r.index('config')
    return getProjectRootPath() + "\\" + r[:i-1]


class RootPath:
    # 当前项目的根路径
    project_root_dir = getProjectRootPath()

    # vsearch包的根路径
    vsearch_root_dir = getThisPackageRootPath()

    # 视频文件的根路径
    video_dir = f'{project_root_dir}\\video'

    # 输出目录的路径
    output_dir = f'{project_root_dir}\\static\\vsearch-output'

    # 搜索结果输出目录
    output_search_result_dir = f'{output_dir}\\search-result'

    # 处理视频后产生的对象保存的路径
    output_video_object_dir = f'{output_dir}\\objects\\videos'
    output_chapter_object_dir = f'{output_dir}\\objects\\chapters'
    output_course_object_dir = f'{output_dir}\\objects\\courses'

    # 处理视频后产生的关键图片保存的路径
    output_courses_dir = output_dir + "\\course"
    output_chapters_dir = output_dir + "\\chapters"
    output_videos_dir = output_dir + "\\videos"

    # 导入训练好的机器学习模型路径
    _model_dir = f'{vsearch_root_dir}\\model'

    # paddleocr 文字检测 和 文字分类模型 | 最新版可以自行去git的paddleocr查看, 将此处的路径末尾改名字即可自动下载
    det_model_dir = f'{_model_dir}\\ocr\\paddle\\ch_ppocr_mobile_v2.0_det_infer'
    rec_model_dir = f'{_model_dir}\\ocr\\paddle\\ch_ppocr_mobile_v2.0_rec_infer'


for k in RootPath.__dict__.keys():
    # new_temp = list(RootPath.__dict__[k])
    # new_temp[0] = new_temp[0].upper()
    print(k)
    # RootPath.__dict__[k] = ''.join(new_temp)

print(f'最开始 RootPath.output_videos_dir: {RootPath.output_videos_dir}')
print(RootPath.__dict__)
