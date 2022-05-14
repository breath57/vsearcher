# threshold

speed_x = 1
step = "fps"

# [thread, process, other] thread: 多线程 |  process: 多进程 | other : 单线程
process_mode = 'thread'

# 启用多线程的最低要求，也就是说，如果存在一个线程的任务量比该情况低，那么就不触发多线程机制，一种动态多线程机制
th_mul_thread_on_frame_counts = 60
# th_mul_thread_on_frame_counts: 30  fps * 2 重复多
# @WAIT 去重相似度的阈值也需要独立成配置参数
re_dul_nums = 'auto'  # 去重的次数
th_thread_nums = 'auto' # auto： 自动    int： 具体个数
th_process_nums = 'auto' # 进程的数量
th_avg_score = 0.83  # 视频越清晰,越容易高分
th_sim_score = 0.85  # 前后两帧相似度 # 0.82
th_blur_score = 60  # 可以依靠统计 均值来定 | 根据视频的分别率来定

# 如果视频画面大小为 1920 *1080, 则 最小的高度为50像素, 其他比例的画面, 会自动根据1920*1080的标准进行缩放, 故按照1920 * 1080的假设来设置阈值
th_min_box_height = 50

th_min_boxes_num = 50  # 低于 th_min_box_height 阈值的框
th_min_boxes_rate = 0.9  # 最小框的比例, 超过该比例判断为内容过多, 不容易观看, 很大可能不是PPT

#  代码行过滤相关
height_multiple_x = 6  # 假设代码框, w/h的比值为 height_multiple_x
th_max_codeline_num = 7  # 最大代码框的数量, 大于该值判断为代码页


# th_max_boxes_num = 66  # 所有框的数量不能大于


use_gpu = True  # 是否使用GPU
gpu_name = 'gpu:0'  # 指定gpu

title_num = 3  # 帧获取的标题数量

img_format = "png"  # 图片保存的格式
img_name_gap = "-"  # 1-1072%804.png | 1代表章节
# url_prefix = "http://127.0.0.1:5000"  # 第三方访问图片路径的域名? 本地图片存储的位置
url_prefix = "https://389852tw96.oicp.vip"  # 第三方访问图片路径的域名? 本地图片存储的位置
# video_format= ['mp4', 'flv', 'avi', 'wmv', 'mpg', 'mpeg'] # 其他格式还未测试
path_space_fill_char = '_'   # 例如: 第六章 逻辑回归, 中间有空格, 浏览器无法打开
frame_name_gap = '-'  # name: 123-66, 其中, 123代表当前帧的帧编号, 66该帧内容帧的位置,即该画面开始的位置
# paddleOCR args
cpu_threads = 100
    # ocr相关
paddle_dir_name = 'paddle' # 目前有: [paddle: 手机轻量级, paddlev3: 16.3M中英]
ocr_num = 2 # 创建的OCR的个数
ocr_load = 1 # OCR载荷: 每个OCR对象同时处理的线程数量, 原因: 载荷过大, @RISK OCR识别的数据会错误, 和其它帧图像的数据混合
enable_mkldnn = True
det_db_unclip_ratio = 2.2
det_db_box_thresh = 0.5

stop_word_file = 'stop_word_common.txt'


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
