speed_x = 1
step = "fps"
search_clear_period_seconds = 120  # seconds
# 用线程和进程安全的数据结构, 对OCR的创建进行控制
default_clear_period_seconds = 120


class Performance:
    '''
        性能相关的配置类
    '''
    th_mul_thread_on_frame_counts = 60  # 启用多线程的最低要求，也就是说，如果存在一个线程的任务量比该情况低，那么就不触发多线程机制，一种动态多线程机制

    # 全局线程默认设置, 当细粒度有设置时, 将优先细粒度的设置
    # [thread, process, other] thread: 多线程 |  process: 多进程 | other : 单线程
    process_mode = 'thread'
    th_thread_nums = 1  # 'auto' # [auto：自动, N: 指定个数]
    th_process_nums = 1  # 'auto' # 进程的数量 ['auto': 系统自动分配, N: 指定个数 ]
    # 线程 | 进程 细粒度的配置
    # [thread, process, other] thread: 多线程 |  process: 多进程 | other : 单线程
    course_process_mode = 'thread'
    # 处理一个课程, 处理章节分配的线程|进程 数量 | 总线程(进程)数 = 课程线程 * 章节线程 * 视频线程
    th_course_multiple_nums = 1
    # [thread, process, other] thread: 多线程 |  process: 多进程 | other : 单线程
    chapter_process_mode = 'thread'
    # 处理一个章节的每个视频的线程|进程 数量 | 总线程(进程)数 = 章节线程 * 视频线程
    th_chapter_multiple_nums = 1
    # @RISK 目前只能使用线程, 不能使用多进程 # [thread, process, other] thread: 多线程 |  process: 多进程 | other : 单线程
    video_process_mode = 'thread'  # @WAIT 多进程问题
    th_video_multiple_nums = 1  # 处理一个视频分配的线程|进程数量 |　总线程(进程)数 = 视频线程

    cpu_threads = 20  # paddleOCR参数  # 或许对于GPU版本来说没有用
    # 目前有: [paddle: 手机轻量级, paddlev3: 16.3M中英] 具体位置为: resource/model/ocr/{$paddle_dir_name}
    paddle_dir_name = 'paddle'
    ocr_num = 1  # 创建的OCR的个数 = 进程数量 * 线程数量 # WAIT 让所有的线程共享
    # OCR载荷: 每个OCR对象同时处理的线程数量 (| 当前的paddleocr版本建议设置1, 多了可能出问题|), 原因: 载荷过大, @RISK OCR识别的数据会错误, 和其它帧图像的数据混合
    ocr_load = 1

    use_gpu = True  # 是否使用GPU
    gpu_name = 'gpu:0'  # 指定gpu  @NOTE 至于多GPU, 该项目目前对GPU的要求内存要求不高, 对CPU内存要求高


# # 性能配置
# process_mode = 'thread' # [thread, process, other] thread: 多线程 |  process: 多进程 | other : 单线程
# th_mul_thread_on_frame_counts = 60 # 启用多线程的最低要求，也就是说，如果存在一个线程的任务量比该情况低，那么就不触发多线程机制，一种动态多线程机制
# th_thread_nums = 2 # 'auto' # [auto：自动, N: 指定个数]
# th_process_nums = 2  # 'auto' # 进程的数量 ['auto': 系统自动分配, N: 指定个数 ]
#
# cpu_threads = 100 # paddleOCR参数
# paddle_dir_name = 'paddle' # 目前有: [paddle: 手机轻量级, paddlev3: 16.3M中英] 具体位置为: resource/model/ocr/{$paddle_dir_name}
# ocr_num = 1 # 创建的OCR的个数
# ocr_load = 1 # OCR载荷: 每个OCR对象同时处理的线程数量 (| 当前的paddleocr版本建议设置1, 多了可能出问题|), 原因: 载荷过大, @RISK OCR识别的数据会错误, 和其它帧图像的数据混合
#
# use_gpu = True  # 是否使用GPU
# gpu_name = 'gpu:0'  # 指定gpu  @NOTE 至于多GPU, 该项目目前对GPU的要求内存要求不高, 对CPU内存要求高

# 课件帧筛选参数
title_num = 3  # 帧获取的标题数量
th_avg_score = 0.83  # 视频越清晰,越容易高分
th_sim_score = 0.85  # 前后两帧相似度 # 0.82
th_blur_score = 60  # 可以依靠统计 均值来定 | 根据视频的分别率来定
# (已经进行适配处理)如果视频画面大小为 1920 *1080, 则 最小的高度为50像素, 其他比例的画面, 会自动根据1920*1080的标准进行缩放, 故按照1920 * 1080的假设来设置阈值
th_min_box_height = 50
th_min_boxes_num = 50  # 低于 th_min_box_height 阈值的框
th_min_boxes_rate = 0.9  # 最小框的比例, 超过该比例判断为内容过多, 不容易观看, 很大可能不是PPT

#  代码行过滤相关
height_multiple_x = 6  # 假设代码框, w/h的比值为 height_multiple_x
th_max_codeline_num = 7  # 最大代码框的数量, 大于该值判断为代码页

#   th_max_boxes_num = 66  # 所有框的数量不能大于
img_format = "png"  # 图片保存的格式
img_name_gap = "-"  # 1-1072%804.png | 1代表视频的id
section_gap = "#"  # 3#1-1072%804.png  | 3 代表第三区
url_prefix = "http://127.0.0.1:5000"  # 第三方访问图片路径的域名? 本地图片存储的位置
# url_prefix = "https://389852tw96.oicp.vip"  # 第三方访问图片路径的域名? 本地图片存储的位置
# video_format= ['mp4', 'flv', 'avi', 'wmv', 'mpg', 'mpeg'] # 其他格式还未测试
# (已解决使用quote方法) path_space_fill_char = '_'   # 例如: 第六章 逻辑回归, 中间有空格, 浏览器无法打开
frame_name_gap = '-'  # name: 123-66, 其中, 123代表当前帧的帧编号, 66该帧内容帧的位置,即该画面开始的位置

# paddleOCR args
enable_mkldnn = True
det_db_unclip_ratio = 2.2
det_db_box_thresh = 0.5

stop_word_file = 'stop_word_common.txt'  # 去停用词的配置文件


def set_step(step_="fps", speed_x_=1):
    """
    真实的读取步长: real_step = step * speed_x
    :param step: 基本读取帧的步长
    :param speed_x: 步长加倍的倍数
    :return:
    """
    global step, speed_x
    step, speed_x = step_, speed_x_


th_min_box_height = str(th_min_box_height)


def update_th_min_box_height(video_height):
    global th_min_box_height
    if type(th_min_box_height) == str:
        th_min_box_height = video_height * int(th_min_box_height) / 1080
        return th_min_box_height
    return th_min_box_height


stop_word_set = set([
'--',
'-',
'?',
'<',
'>',
'!',
',',
'.',
'"',
"/",
"~",
"`",
"-",
"=",
"+",
"(",
")",
"*",
":",
";",
"－－",
"－",
"、",
"。",
"“",
"”",
"《",
"》",
"（",
"）",
"【",
"】",
"[",
"]",
"！",
"，",
"：",
"；",
"？",
])