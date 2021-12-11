
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
    output_dir = f'{project_dir}\\output'

    output_video_object_dir = f'{output_dir}\\video_object'
    # fm 代表需要进行format才能使用
    output_frame_dir_fm = output_dir + "\\keyframe\\v{}"

    _model_dir = f'{project_dir}\\vsearch\\model'

    det_model_dir = f'{_model_dir}\\ocr\\paddle\\ch_ppocr_mobile_v2.0_det_infer'

    rec_model_dir = f'{_model_dir}\\ocr\\paddle\\ch_ppocr_mobile_v2.0_rec_infer'