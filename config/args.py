# threshold

speed_x = 1
step = "fps"

# @wait 去重相似度的阈值也需要独立成配置参数
re_dul_nums = 1  # 去重的次数
th_avg_score = 0.83  # 视频越清晰,越容易高分
th_sim_score = 0.82  # 前后两帧相似度
th_blur_score = 60  # 可以依靠统计 均值来定 | 根据视频的分别率来定

# 如果视频画面大小为 1920 *1080, 则 最小的高度为50像素, 其他比例的画面, 会自动根据1920*1080的标准进行缩放, 故按照1920 * 1080的假设来设置阈值
th_min_box_height = 44
th_min_boxes_num = 40
th_min_boxes_rate = 0.83

use_gpu = True
gpu_name = 'gpu:0'

title_num = 3  # 帧获取的标题数量

img_format = "png"  # 图片保存的格式
img_name_gap = "-"
img_url_prefix = "http://127.0.0.1:5000"
# video_format= ['mp4', 'flv', 'avi', 'wmv', 'mpg', 'mpeg'] # 其他格式还未测试

# paddleOCR args
cpu_threads = 100
enable_mkldnn = True
det_db_unclip_ratio = 2.2
det_db_box_thresh = 0.65


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
