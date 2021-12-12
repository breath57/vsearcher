
# ['__builtins__', '__cached__', '__doc__', '__file__', '__loader__', '__name__', '__package__', '__spec__']



def getProjectRootPath():
    r = __name__.replace('.', '\\')
    i = __file__.index(r)
    return __file__[: i-1]


class RootPath:
    # 当前项目的根路径
    project_dir = getProjectRootPath()

    # 视频文件的根路径
    video_dir = f'{project_dir}\\video'

    # 输出目录的路径
    output_dir = f'{project_dir}\\vsearch-output'

    # 处理视频后产生的对象保存的路径
    output_video_object_dir = f'{output_dir}\\objects\\videos'
    output_chapter_object_dir = f'{output_dir}\\objects\\chapters'
    output_course_object_dir = f'{output_dir}\\objects\\courses'

    # 处理视频后产生的关键图片保存的路径
    output_courses_dir = output_dir + "\\course"
    output_chapters_dir = output_dir + "\\chapters"
    output_videos_dir = output_dir + "\\videos"

    # 导入训练好的机器学习模型路径
    _model_dir = f'{project_dir}\\vsearch\\model'

    # paddleocr 文字检测 和 文字分类模型
    det_model_dir = f'{_model_dir}\\ocr\\paddle\\ch_ppocr_mobile_v2.0_det_infer'
    rec_model_dir = f'{_model_dir}\\ocr\\paddle\\ch_ppocr_mobile_v2.0_rec_infer'