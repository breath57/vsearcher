from pathlib import Path
import time
from typing import List
from unittest import result
import filetype
import shutil
import copy as cp
import glob
import os
import cv2 as cv
import numpy as np
from paddleocr import PaddleOCR, draw_ocr
import os

from prometheus_client import Enum
# import paddle

from . import utils
from .config import args
from .sim_v1 import TextSimilarity
from .config.path import RootPath

from .vo import vo
from vsearch.config import path

if args.use_gpu:
    print('启用GPU............')
    import paddle
    os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

    # @RISK 判断设备是否存在 再设置
    if paddle.get_device() != 'cpu':
        paddle.set_device(args.gpu_name)
    print(f'current use device: {args.gpu_name}')
# paddle.set_device('gpu:0')

"""
PaddleFrame遍历完后, 自动去除cap对象,
图片保存后自动删除self.frame对象
args.speed_x
del self.cap self.result 将 paddleOCR置出 节约持久化
"""
# @RISK 环境迁移之后没有cuda可能会报错
# paddle.device.set_device('gpu:0')
# class Frame():
#     """
#      如果业务复杂, 需要考虑多种OCR识别库, 由于返回的格式不一样, 再抽象出该类
#     """
#     warnings.warn('暂未开发完成, 无法使用', DeprecationWarning)
#     pass

# class ISearch(object):
#     @abstractmethod
#     def searchByKey(self, key):
#         pass

from PIL import Image
# @WAIT 设计的不合理


class Searcher:
    """
        读取结果
        另存为有标记的图片
        设置线程监视1分钟删除
        生成图片目录  temp -> 随机名称 
    """

    search_timestamp = ''

    @classmethod
    def processPfVo(cls, pf: vo.Frame, unique_file_name=""):
        """
        功能: 将pf中的img_url更改为搜索结果,并且可提供第三方访问的url
            cls: 就是Search, 代表class, 类名
            pf: 为搜索结果帧
        """
        # @WAIT 文件名包含 key, 可以避免重复请求 处理返回
        # @PERFORMANCE wait 算法流程优化
        # @WAIT 程名 + 章节名 + 视频名称 + key
        print('需要读取的图片路径')
        # http://127.0.0.1:5000/static/vsearch-output/videos/pattern_pure_ppt/-0.png'
        file_path = utils.url2local(pf.img_url)  # url路径转本地路径
        frame = utils.cvimread(file_path)

        im_show = draw_ocr(frame, pf.boxes)  # 圈出搜索结果
        im_show = cv.cvtColor(im_show, cv.COLOR_BGR2RGB)  # 修正色域为Image读取正常
        im_show = Image.fromarray(im_show)
        # im_show shape h,w,c

        # 图片的输出目录 定义
        output_dir = path.RootPath.output_search_result_dir
        output_dir = f'{output_dir}\\{cls.search_timestamp}'  # 构建输出目录
        output_dir = Searcher.__setDir(output_dir)

        # 用时间标识每次产出的图片的唯一性, 符合url的唯一定位特点
        file_path = f'{output_dir}\\_{int(time.time_ns())%100000000}_.{args.img_format}'
        print(f"处理过的图片保存路径: {file_path}")
        im_show.save(file_path)  # 结果图片保存在代码同级文件夹中, (output_dir下更准确)
        img_url = utils.local2url(file_path)
        pf.img_url = img_url  # 此时的 pf中的img_url为框出搜索结果的图片url
        print(f"图片url: {img_url}")
        return pf
        # 图片保存

    @staticmethod
    def __setDir(dir_path: str):
        """
        设置搜索结果图片保存的根目录
        如果目录不存在, 就创建目录; 存在不处理
        :param dir_path:
        :return:
        """
        # @MODIFY 为了可以找到图片的路径, 就是有空格的情况
        dir_path = dir_path.replace(" ", args.path_space_fill_char).replace(
            "\t", args.path_space_fill_char)
        if not os.path.exists(dir_path):
            os.makedirs(dir_path, mode=0o777, exist_ok=True)
            # os.mkdir( dir_path )
        return dir_path

    @classmethod
    def __reset_time_stamp(cls):
        """
        功能: 生成此处所有搜索的时间戳
        作用: 用于一次搜索结果图片的内容存放目录的唯一标识
        """
        cls.search_timestamp = str(int(time.time()))

    @classmethod
    def search(cls, _type, name: str, key: str, json_dumps=False) -> object:
        """
            功能: 根据搜索关键字返回各种各样的搜索结果
            @param: json_dumps  是否进行对搜索结果进行json序列化
        """
        # 重置搜索时间
        cls.__reset_time_stamp()
        o = None
        if _type == Assember.VIDEO:
            o = utils.readObject(RootPath.output_video_object_dir, name)
        elif _type == Assember.CHAPTER:
            o = utils.readObject(RootPath.output_chapter_object_dir, name)
        elif _type == Assember.COURSE:
            o = utils.readObject(RootPath.output_course_object_dir, name)
        if o:  # 如果搜索到了内容
            return o.searchByKey(key, json_dumps)
        # dosearch
        return o


# @WAIT Video内容的遍历，有开关控制是否延时加载，还是立即生成， 还有那个apply函数， 目前可以内嵌了， 作为初始化
# @WAIT 每种对象都需要可以支持传入输出路径，当然最终肯行是需要配置的，所以都是需要装配的
# @WAIT video图片保存的目录需要保存到配置目录
# @REQUIREMENT 不管是单个视频，还是章节， 还是课程， 都需要支持导出的功能，

# PaddleOCR对象的创建, 方便后续算法的使用
paddleOCR = PaddleOCR(
    det_model_dir=RootPath.det_model_dir, rec_model_dir=RootPath.rec_model_dir,
    cpu_threads=args.cpu_threads,
    enable_mkldnn=args.enable_mkldnn,
    det_db_box_thresh=args.det_db_box_thresh,
    det_db_unclip_ratio=args.det_db_unclip_ratio
)

# paddleOCR_video_inner = PaddleOCR(
#     det_model_dir=RootPath.det_model_dir, rec_model_dir=RootPath.rec_model_dir,
#     cpu_threads=args.cpu_threads,
#     enable_mkldnn=args.enable_mkldnn,
#     det_db_box_thresh=args.det_db_box_thresh
# )


class PaddleFrame:
    """
    处理paddle调用ocr(det=True, rec=True, cls=False)方法的结果
    主要完成以下功能:
        1. 返回所有的结果
        2. 返回所有检测框
        3. 返回所有检测框的分数
        4. 返回所有检测框的文本内容
        5. 关键词提取: 框框越大的内容, 越可能是关键内容
        6. 返回平均置信度, 也就是平均分数
    """

    # def _name(self):
    #     return f'{self.video_id}  # {self.id}'

    def __init__(self, id, frame, ms, img_outpath, video_id=""):
        """
        @WAIT 具体的id形式, 具体再确定
        params:
            id: 帧id
            frame: opencv读取的图片的具体帧, 是一个特定的数组        
            ms: 处于该视频中的播放位置
            img_outpath: 图片的保存路径
            video_id: 该帧所属的视频的id
        """
        self.id = id
        self.frame = frame
        self.is_into_iter = self.__is_into_iter()  # @IMPROVEMENT 算是性能优化, 可以让下面的代码不需要执行
        if not self.is_into_iter:
            return

        self.outpath = img_outpath
        self.video_id = video_id
        self.ms = ms
        self.name = f"{video_id}{args.img_name_gap}{self.id}" if video_id != "" else f"{self.id}"
        self.blur_score = cv.Laplacian(frame, cv.CV_32F).var()
        """
        @WAIT 返回的结果是否需要去除 停用词
        @PERFORMANCE 把np.array去除, 因为只有txts使用到np.array方法
        """

        self.result = np.array(paddleOCR.ocr(frame, cls=False))  # 提取帧中的内容
        if len(self.result) == 0:  # 如果帧中没有内容
            self.has_txt = False
            self.boxes = np.array([])
            self.txts = np.array([])
            self.scores = np.array([])
            self.avg_score = 0
        else:  # 如果帧中有内容
            self.has_txt = True
            self.boxes = np.array(self.result[:, 0])
            self.txts = np.array(
                list(map(lambda x: x[0], self.result[:, 1])))  # 将所有OCR文字拼接为字符串
            self.scores = np.array(
                list(map(lambda x: x[1], self.result[:, 1])))  # @NOTING 统计所有检测框的分数? 文字的分数还是框是否正确的分数
            # @NOTING 平均分数, 作用: 用于筛选 需要文字识别的框? 好像不需要
            self.avg_score = np.mean(self.scores)
            # self._save() # 有结果, 图片才需要保存

    def __is_into_iter(self):
        """
           作用: 设定一系列条件, 判断当前帧是否需要,进行迭代的处理, 还是直接废弃
        """

        # 无内容过滤
        boxes = paddleOCR.text_detector(self.frame)[0]
        boxes_num = len(boxes)
        print(f'boxes_num: {boxes_num}')
        if boxes_num == 0:
            return False

        th_min_box_height = Video.th_min_box_height
        print(f'th_min_box_height: {th_min_box_height}')

        # 代码行数过滤
        # @WAIT 可以训练一个代码识别器, 直接判断是否是代码页
        # @RISK 不是代码框的也会被识别成代码框过滤
        max_codeline_num = list(
            filter(lambda box: (box[2][1]-box[0][1]) < th_min_box_height and (box[1][0] - box[0][0]) > th_min_box_height*args.height_multiple_x, boxes)).__len__()  # 根据候选框的框高 和 框的长度过滤, 计算过滤后的代码框的数量
        print(f'min_codeline_num: {max_codeline_num}')
        if max_codeline_num > args.th_max_codeline_num:
            return False

        # # 框数过滤
        # print(f'boxes_num: {boxes_num}')
        # if boxes_num > args.th_max_boxes_num:
        #     return False

        # 最小框数量过滤
        min_boxes_num = list(
            filter(lambda box: (box[2][1]-box[0][1]) < th_min_box_height, boxes)).__len__()
        print(f'min_boxes_num {min_boxes_num}')
        if min_boxes_num > args.th_min_boxes_num:
            return False

        # 最小框比例过滤
        min_boxes_rate = min_boxes_num/boxes_num
        print(f'min_boxes_rate: {min_boxes_rate}')
        if min_boxes_rate > args.th_min_boxes_rate:
            return False

        # 暂时不考虑 用平均值
        # average_height = reduce(lambda box: box[2][1] - box[0][1], boxes)/boxes_num

        return True

    def getTitles(self, nums=1):
        """
        获取最有可能是标题的文本内容
        @WAIT 获取标题, 或者说是该帧内的代表性文本列表
        @RISK 获取的title可能会有错误的概率
        """
        # 框框按照 y轴距离, 排序, 获取排序后的索引
        # 过滤掉 标点符号, 之类的内容, 就是除了中文和英文之外的内容
        # 内容长度不能小于几个字, 或者说字数和字体的大小, 都需要占据比重,
        # 因为有写 PPT的LOGO, 很大, 大过标题
        # 标题的位置, 一定是位于上半屏幕的
        # 是否: 去除连续好多页都出现的标题作为搜索关键词?, 不用去除, 还是当作PPT来应用
        # @WAITValidate
        # print(self.txts)
        h_weights = [
            self._getHeightWeight(index) for index in range(self.boxes.shape[0])
        ]
        h_indexs = np.argsort(h_weights)[: nums + 4]

        lu_weights = [self._getLeftUpWeight(index) for index in h_indexs]

        dicts = {}
        for i, w in enumerate(lu_weights):
            dicts.update({w: h_indexs[i]})

        lu_weights_top = np.sort(lu_weights)[:nums]
        indexs = []
        for i, w in enumerate(lu_weights_top):
            indexs.append(dicts.get(w))
        return self.txts[indexs]

    def _getLeftUpWeight(self, index):
        """
        说明: 权重值越小, 则越重要
        作用: 为了判别当前帧中的标题
        """
        box = self.boxes[index]
        # box[0]代表左上方的坐标, box[0][0] + box[0][1]越小, 说明越在左上方
        return box[0][0] + box[0][1]

    def _getHeightWeight(self, index):
        """
        说明: 为了减少一次argsort的排序, 权重值越小, 则越重要
        具体的权重计算还需要验证
        作用: 为了判别当前宽框是标题的可能性
        @WAIT
        """
        # txt = self.txts[index]
        box = self.boxes[index]
        # @WAITValidate
        box_height = box[3][1] - box[0][1]
        # txt_width = box[1][0] - box[0][0]
        txt_height = box_height
        # txt_len = len(txt)

        # return txt_height * 0.7 + txt_len * 0.3
        return -(txt_height)

    def getBoxesLen(self):
        return len(self.boxes)

    def getAllTextArray(self) -> list:
        """
            功能: 数据的形式返回所有文本
        """
        return self.txts

    def getAllTextStr(self) -> str:
        """
            功能: 将所有的文本变成字符串统一返回
            @RISK 没有任何分隔符号进行拼接
        """
        return "".join(self.txts)

    # @WAIT 将搜索的方法外置
    def searchByKey(self, key, json_dumps=False, vo_process_func=Searcher.processPfVo):
        """
        :return [{box1相关信息}, {}, {}  ]= 关键帧的box位置的相关信息
            @WAIT返回True 还是, 返回在具体某个boxes的坐标, 有利于框出来
            @WAIT @PERFORMANCE好的搜索算法, 或者搜索这一步, 可以放到全局, 而不是每一个帧都搜索一次
            @IMPROVEMENT 将key进行分词 -> 逐搜索 -> 去重 -> 返回结果
            @IMPROVEMENT 支持语义: embedding为词向量 -> 余弦相似度搜索
        :params:
            vo_process_func(pfVo: vo.Frame): 将返回结果PfVo, 进行预处理函数, 
        """
        # result = []
        key = key.casefold()
        boxes = []
        txts = []
        for i, t in enumerate(self.txts):
            if t.casefold().find(key) != -1:  # 全部转为小写进行搜索
                # @WAIT 数据返回的格式待定
                # result.append({
                #     'id': self.id,
                #     'box': self.boxes[i],
                #     'txt': t,
                #     'name': self.name,
                #     'ms': self.ms,
                #     'img': self.img
                # })
                boxes.append(self.boxes[i])
                txts.append(self.txts[i])
                # 搜索结果 -> 画ocr
                # @tag
        # @WAIT 还可以有 keyword, 也就是每页中 又大又长的框框
        result = vo.Frame(
            id=self.id,
            img_url=self.img_url,
            img_local_path=self.img_local_path,
            boxes=boxes,
            name=self.name,
            txts=txts,
            ms=self.ms,
            time=utils.msToH_M_S_str(self.ms),
            title=self.getTitles(args.title_num),
        )

        # @WAIT 将画的图片另存为
        if not result.isEmpty():
            vo_process_func and vo_process_func(
                result)  # 保证vo_process_func存在的情况下, 处理vo
        return utils.json_dumps(result) if json_dumps else result

    # def setOutPath(self, out_path):
    #     self.out_path = out_path

    def save(self):
        img_path = utils.unify_path(
            f"{self.outpath}\\{self.name}.{args.img_format}")
        print(f'img_path: {img_path}')
        # @note 中文路径图片保存
        cv.imencode(f".{args.img_format}", self.frame)[1].tofile(img_path)
        # @RISK 图片的读取 : 这里指定的类型为 uint8 为0-255, BRG模式, 如果有其他色域的图片, 将不适用
        # cv.imdecode( np.fromfile(img_path, dtype=np.uint8 ), -1 )
        # 获取 root: vsearch-output  real: C/vsearch-output/
        # self.img_path = img_path
        img_url = utils.local2url(img_path)
        # @modified 为了统一url路径, 而不是文件路径
        # @WAIT 将所有路径统一为 / 而不是window下的 \\
        # img_url = img_url.replace('\\', '/') # @MODIFY 修改为统一的
        print(f"img_url: {img_url}")
        self.img_url = img_url
        self.img_local_path = img_path
        # @RISK 删除属性, 节约持久化需要的内存
        del self.frame
        del self.result

    def getSimScore(self, pre_pf):
        """ "
        两帧之间文本相似度计算
        """
        return TextSimilarity.getSimScoreV1(
            pre_pf.getAllTextStr(), self.getAllTextStr()
        )

    # def _getBlurScore(self, img):
    #     return cv.Laplacian(img, cv.CV_32F).var()
    def getSimScoreV3(self, nt_pf):
        """
        @return {
        'base_pre': base_pre_sim,
        'base_nt': base_nt_sim
        }
        """
        return TextSimilarity.getSimScoreV3(self.getAllTextStr(), nt_pf.getAllTextStr())

    def getSimScoreV4(self, nt_pf):
        """
        @return ret, sim;   ret: -1 0 1
        """
        return TextSimilarity.getSimScoreV4(self.getAllTextStr(), nt_pf.getAllTextStr())


class KeyFrames:
    """
       存储每个视频的关键帧, 提供关键帧的一些操作
       功能: 
        1. 可以for in迭代
        2. 替换尾部元素, 等其它对关键帧列表的增删改查
        3. 帧去重,  @WAIT 但是无法去重 间隔较远的帧, 可以每隔x帧为一个窗口去重, 或者, 保留信息, 因为有些帧的重出现是有必要的在pdf中, 那就可以去重短期的, 不过目前生成的帧已经可以不用去重得到的就是去重后的结果了
        4. 保存帧为图像到本地, 即调用paddleFrame的save方法
    """

    def __init__(self):
        self.frame_list = []  # PaddleFrame List

    # def save(self):
    #     out_path = self
    #     if not os.path.exists( out_path ):
    #         os.mkdir( out_path )
    #     del_list = glob.glob( f'{out_path}*.jpg' )
    #     for path in del_list:
    #         os.remove( path )
    #
    #     for pf in self.frame_list:
    #

    # def searchByKey(self, key):
    #     '''
    #
    #     :param key:
    #     :return: [ [{},{}],[{},{}] ]
    #     '''
    #     result = []
    #     for pf in self.getList():
    #         result.append(pf.searchByKey(key))
    #     return result

    def getList(self):
        return self.frame_list

    def __getitem__(self, index):
        return self.frame_list[index]

    def add(self, pf: PaddleFrame):
        self.frame_list.append(pf)

    def updateTail(self, pf):
        self.update(self._len() - 1, pf)

    def get(self, i):
        self._check_valid(i)
        return self.frame_list[i]

    def getTail(self):
        if self._len() == 0:
            raise IndexError("当前列表为空")
        return self.frame_list[self._len() - 1]

    def update(self, i, pf):
        self._check_valid(i)
        self.frame_list[i] = pf

    def _check_valid(self, i):
        if self._len() == 0 or (i - 1) >= self._len():
            raise IndexError(f"Index out of the max length({self._len()})")

    def _len(self):
        return len(self.frame_list)

    def __getitem__(self, key):
        return self.frame_list[key]

    def setList(self, frame_list):
        self.frame_list = frame_list

    def pop(self, i):
        self._check_valid(i)
        self.frame_list.pop(i)

    def popTail(self):
        if self._len() == 0:
            raise IndexError("当前列表为空")
        self.frame_list.pop(self._len() - 1)

    def remove_duplicate(self):
        """
        图片内容去重
        @WAIT 应该保留图片清晰度较好的| 保留内容文字更多的 | 最后 内容还有 时间节点做更改
        双向相似度
        """
        frame_list = self.frame_list
        for i in range(len(frame_list) - 1, -1, -1):
            cur = frame_list[i]
            nt_i = i - 1
            if nt_i >= 0:
                nt = frame_list[nt_i]

                score = cur.getSimScoreV3(nt)
                cur_score = score["base_pre"]
                nt_score = score["base_nt"]
                max_score = max(cur_score, nt_score)
                if max_score > args.th_sim_score:
                    # 删除, 并且删除信息少的那一个
                    if cur_score < nt_score:
                        frame_list.pop(i)
                    else:  # 交换信息, 删除后一个
                        cur.ms = nt.ms
                        cur.name = nt.name
                        cur.id = nt.id
                        frame_list[nt_i] = cur
                        frame_list.pop(i)
            else:
                break

    def saveKfs(self):
        for kf in self.frame_list:
            kf.save()

    # def _isSim(self, pf1: PaddleFrame, pf2: PaddleFrame):
    #     score = pf1.getSimScoreV3(pf2)
    #     return True if score > 0.85 else False

    def __len__(self):
        return self._len()


class CWPathType(Enum):
    """
        定义生成后的课件返回地址的类型
    """
    LOCAL = 'local_path'  # 返回本地路径
    URL = 'url'  # 返回第三方可以访问的URL


class Video:
    """
    视频相关信息
    功能:
        1. 视频的总帧数
        2. 视频的帧率
        3. 根据帧号获取视频的播放时间, 单位: 毫秒
        4. 将该视频 转换为 图片
        5. 遍历功能, 设置一个插槽, 传入一个处理函数
        @WAIT 加入将视频帧转pdf课件的功能
        6.
    """

    # def saveToPDF(self):
    #     paths =
    #     for pf in self.kfs.getList():
    #         PaddleFrame().img_local_path

    th_min_box_height = ''

    def __init__(self, video_path, output_dir, video_id, chapter_id, name=""):
        """
        ::name 如果没有传入, 默认视频的名称为name默认值
        @WAIT 层级关系的设计后续还需要考虑
        """
        # if not video_path:
        #     raise FileExistsError('Please correct video path!')

        if not name:
            self.name = Path(video_path).stem
        else:
            self.name = name
        self.courseware_path = None
        self.output_dir = output_dir
        # self.kfs_out_put_dir = kfs_output_dir

        self.local_path = video_path
        # self.parent_id = chapter_id
        self.chapter_id = chapter_id
        self.id = video_id
        if chapter_id == -1:
            self.pre_id = video_id
        else:
            self.pre_id = f"{chapter_id}.{self.id}"
        self.kfs = KeyFrames()

        self.cap = cv.VideoCapture(video_path)  # 获取指定路径的视频对象
        self.fps = self.cap.get(cv.CAP_PROP_FPS)
        self.width = self.cap.get(cv.CAP_PROP_FRAME_WIDTH)
        self.height = self.cap.get(cv.CAP_PROP_FRAME_HEIGHT)
        self.frame_counts = self.cap.get(cv.CAP_PROP_FRAME_COUNT)

        Video.th_min_box_height = args.update_th_min_box_height(self.height)
        if args.step == "fps":
            self.step = self.fps * args.speed_x
        else:
            self.step = args.step * args.speed_x
        if self.fps > 0:  # 有些垃圾的视频文件, 没有内容, 导致 除0的报错
            self.total_time_ms = self.frame_counts / self.fps * 1000
            self.old_frame = None
            self._run()  # 运行完成产出关键帧
            self.kfs.saveKfs()  # 将关键帧保存为文件
            del self.old_frame
            # @RISK 保存完成将 kfs: KeyFrame ->  kfs: list, 同时释放内存
        temp = self.kfs
        self.kfs = self.kfs.getList()
        del temp
        del self.cap
        # if run:
        #     self._run()

    def searchByKey(self, key, json_dumps=False):
        """
            视频内容的搜索方法
        """
        kfs = []
        for pf in self.kfs:
            pfvo = pf.searchByKey(key)
            # if args.search_result_dict_mode:
            #     if pfvo['boxes']:
            #         kfs.append( pfvo )
            # else:
            if not pfvo.isEmpty():
                kfs.append(pfvo)

        result = vo.Video(
            id=self.id, kfs=kfs, name=self.name, local_path=self.local_path, chapter_id=self.chapter_id
        )
        return utils.json_dumps(result) if json_dumps else result

    def __generate_courseware(self, path_type: CWPathType) -> str:
        """ 生成课件
        return 课件的本地地址
        """
        if not self.courseware_path:
            # @MODIFY 如果课件不存在就会重新生成, 所以可以随便删除

            imgs = [pf.img_local_path for pf in self.kfs]
            self.courseware_path = utils.imgs2pdf(imgs, file_name=self.name)
        # @RISKED 如果课件存在过期时间, 导致课件被删除怎么办?

        # 因此 @WAIT 需要有一个判断地址是存在课件的方法
        return self.courseware_path if path_type is CWPathType.LOCAL else utils.local2url(self.courseware_path)

    def get_courseware_path(self, return_path_type: CWPathType = CWPathType.LOCAL):
        return self.__generate_courseware(path_type=return_path_type)
    # def getTimeMsByFrameID(self, frame_id):
    #     帧编号 转换为 该视频播放位置的 毫秒数
    #     @return millisecond
    #     return frame_id / self.fps * 1000

    def _iter_func(self, pf: PaddleFrame):
        """
            对__run方法遍历的帧进行相关的处理, 判断是否需要加入关键帧集合
        """
        print("------------------------------")
        print(f"有效帧数: {len( self.kfs )}  当前帧: {pf.id}")
        # cv.imshow('v1', pf.frame)
        # cv.waitKey(1)
        # 增加模糊度, 对比度判断
        # contrast_score = contrastScore(pf.frame)
        if not pf.is_into_iter:
            return
        print(
            f"{pf.name} / {self.frame_counts} \navg_score : {pf.avg_score} \nblur_score: {pf.blur_score}"
        )
        if pf.blur_score < args.th_blur_score:
            self.old_frame = pf
            return
        if pf.avg_score < args.th_avg_score:
            self.old_frame = pf
            return
        if pf.has_txt == False:
            self.old_frame = pf
            return

        origin_pf = cp.deepcopy(pf)
        if self.old_frame == None:
            self.old_frame = pf
            self.kfs.add(pf)
        else:
            # @WAIT 具体的相似度算法可以参考策略模式, 将具体使用哪个相似度算法, 抽象成接口, 或者配置, 可以直接切换, 而不是这里写死
            ret, sim_score1 = pf.getSimScoreV4(self.old_frame)
            sim_score = 0

            # 两步计算相似度, 解决状况:  PPT内容展示有动画, 例如: 内容: a -> 过渡动画 -> ab, 其实还是同一页, 但是如果只计算sim(old, cur), a变模糊, 再到没有a->插入列表->再出现ab
            if len(self.kfs) > 0:
                tail_frame = self.kfs.getTail()
                ret, sim_score2 = pf.getSimScoreV4(tail_frame)
                # 如果分数高的是末尾
                sim_score = max(sim_score1, sim_score2)
            else:
                sim_score = sim_score1
            # 还需要修复 关键点1 -> full, 再来一次 1-> full, 会导致重复的发生
            # @PERFORMANCE 去重的操作如果影响性能, 可以提供用户点击去重效果
            print(f"sim_score: {sim_score}")
            # @WAIT 逆向相似度 > 正向相似度, 说明在减少内容, 是动画

            # 内容增加判断
            if sim_score > args.th_sim_score:  # 判断是否相似
                # 增加内容的比较, 也要和 tail末尾的比较, 不过得相似的前提下
                if pf.getBoxesLen() > self.old_frame.getBoxesLen():  # 内容增加
                    pf.ms = self.old_frame.ms
                    pf.name = pf.name + \
                        f"{args.frame_name_gap}{self.old_frame.id}"
                    if len(self.kfs) > 0:  # 如果关键帧列表不为空
                        self.kfs.updateTail(pf)
                    else:
                        self.kfs.add(pf)
                        print(
                            f"上一帧内容: {self.old_frame.getAllTextArray()}   这一帧率的内容: {pf.getAllTextArray()}")
                        print(f"加入一帧率: {pf.name}  frame_id: {pf.id}")
                    # self.old_frame = origin_pf
                elif pf.getBoxesLen() < self.old_frame.getBoxesLen():  # 内容减少
                    self.old_frame = origin_pf  # 为了保留上一帧的特性
                    pass

                else:  # 图片内容相同, 且内容没有增加了,
                    if len(self.kfs) > 0:
                        tail_frame = self.kfs.getTail()
                        if pf.blur_score > tail_frame.blur_score:  # 保留图片清晰图更好的图像
                            tail_frame.blur_score = pf.blur_score
                            tail_frame.frame = pf.frame
                            self.kfs.updateTail(tail_frame)
                        # self.old_frame = origin_pf
            else:  # 不相似
                print(
                    f"上一帧内容: {self.old_frame.getAllTextArray()}   这一帧率的内容: {pf.getAllTextArray()}")
                print(f"加入一帧率: {pf.name}  frame_id: {pf.id}")
                self.kfs.add(pf)

            # 指定一系列过滤条件
            # 如果 分数大于 0.95, 不保留,
            # 如果没有内容 也不保留
            self.old_frame = origin_pf
        print("------------------------------")

    def _run(self):
        """
            迭代函数, 按配置的帧间隔读取视频帧,
        """
        while True:
            ret, frame = self.cap.read()
            if ret:
                frame_id = int(self.cap.get(cv.CAP_PROP_POS_FRAMES)) - 1
                frame_ms = self.cap.get(cv.CAP_PROP_POS_MSEC)
                print(f'进度: {frame_id}/{self.cap.get(cv.CAP_PROP_FRAME_COUNT)}')
                ### 增加一层, 框框数太多, 为代码也, 框框的高度大小, 代码也
                self._iter_func(
                    PaddleFrame(
                        frame_id, frame, frame_ms, self.output_dir, self.id
                    )
                )
                # print(f'frame_id: {frame_id}, frame_ms: {frame_ms} ')
                self.cap.set(cv.CAP_PROP_POS_FRAMES, frame_id + self.step)

                # if step == 1:
                #     frame_ms = self.cap.get(cv.CAP_PROP_POS_MSEC)
                #     func(PaddleFrame(frame_id, frame, frame_ms, self.id))

                # else:
                #     if frame_id % step == 0:
                #         frame_ms = self.cap.get(cv.CAP_PROP_POS_MSEC)
                #         func(PaddleFrame(frame_id, frame, frame_ms, self.id))
            else:
                break

        # del self.cap
        # delattr(self, 'cap')

    # def saveKfs(self, output_path=None, postfix='jpg'):
    #     if not output_path:
    #         output_path = RootPath.output_frame_dir_fm.format( self.name )
    #     if not os.path.exists( output_path ):
    #         os.mkdir( output_path )
    #     del_list = glob.glob( f'{output_path}*.*' )
    #     for path in del_list:
    #         os.remove( path )
    #
    #     for pf in self.kfs:
    #         pf.save(out_path=output_path, postfix=postfix)


class Chapter:

    def __init__(self, id: int, name: str, course_id: int, videos: List[Video]) -> None:
        self.id = id
        self.name = name
        self.course_id = course_id
        self.videos = videos  # @WAIT 如何保证视频的有序性， 这样才能够保证搜索结果的有序性，（可以根据id排序，实现一次规整化处理）

    def __getitem__(self, index):
        return self.videos[index]

    def searchByKey(self, key, json_dumps=False):
        """
        :param key:
        :return: r[小节号][帧]
        @WAIT 章节搜索内容的返回格式,   1: 不加区分, 直接list  2. dict格式: { chapter1: [内容] }
        3. {course: {
            chapter:
        }}
        3. 优点： 自身就有序，  缺点： 语义不是那么明确， 如果返回给前端， 不是那么容易理解
        r【章节】【小节】【帧】， 因此这里的结果不要简单的叠加
        课程 [
            章节 [
                小节 [
                    帧[

                    ]
                ]
            ]
        ]
        需求:　需要有序的排序
        """
        videos = []
        for v in self.videos:
            video_vo = v.searchByKey(key)
            # if args.search_result_dict_mode:
            #     if video_vo['kfs']:
            #         videos.append( video_vo )
            # else:
            if not video_vo.isEmpty():
                videos.append(video_vo)
        result = vo.Chapter(
            id=self.id, videos=videos, name=self.name, course_id=self.course_id
        )
        return utils.json_dumps(result) if json_dumps else result


class Course:
    """ "
    更好的方案： 直接传入入境， 自顶向下的一起喝成， 而不是自定向下的创建， 所以闯入了不应该是章节， 而是文件的路径
    那么文件路径的结构需要什么样的呢

    是否需要路径对象， 负责管理视频的路径呢：
    当然： 根路径也需要有结构的存放视频，    然后视频的格式， 路径管理器进行自动解析


    """

    def __init__(self, id, name, chapters: List[Chapter] = []) -> None:
        self.id = id
        self.name = name
        self.chapters = chapters

    def __getitem__(self, index):
        return self.chapters[index]

    def searchByKey(self, key, json_dumps=False) -> vo.Course:
        chapters = []
        for c in self.chapters:
            chapter_vo = c.searchByKey(key)
            # if args.search_result_dict_mode:
            #     if chapter_vo['videos']:
            #         chapters.append( chapter_vo )
            # else:
            if not chapter_vo.isEmpty():
                chapters.append(chapter_vo)
        result = vo.Course(id=self.id, chapters=chapters, name=self.name)
        return utils.json_dumps(result) if json_dumps else result


class Assember:
    """
    负责将用户指定的路径（课程，章节， 小节）： 装配出不同的对象（Course， Chapter， Video）
    这样就可以直接使用装配好的对象的方法进行操作
    """
    COURSE = 'course'
    CHAPTER = 'chapter'
    VIDEO = 'video'

    @staticmethod
    def executeCourse(
        course_root_path, output_dir=RootPath.output_courses_dir, course_id="", dir_name=""
    ) -> Course:

        chapter_dirs = glob.glob(f"{course_root_path}\\*")
        # 过滤非目录文件
        chapter_dirs = Assember.__filter_no_dir(chapter_dirs)
        dir_name = dir_name or os.path.basename(course_root_path)  # 获取目录名
        # 初始化 输出目录
        output_dir = output_dir + "\\" + dir_name
        # @modified 修改了路径
        output_dir = Assember._setDir(output_dir)

        chapters = [
            Assember.executeChapter(
                chapter_path=dir_path,
                output_dir=output_dir,
                chapter_id=i + 1,
                chapter_name=os.path.basename(dir_path),
                course_id=course_id,
            )
            for i, dir_path in enumerate(chapter_dirs)
        ]
        return Course(id=course_id, name=dir_name, chapters=chapters)

    @staticmethod
    def executeChapter(
        chapter_path,
        output_dir=RootPath.output_chapters_dir,
        chapter_id="",
        chapter_name="",
        course_id="",
    ) -> Chapter:
        # 获取章节目录下的所有视频的路径
        # @RISK 视频类型的过滤器可能有隐藏的bug
        video_paths = glob.glob(f"{chapter_path}\\*")
        video_paths = Assember.__filter_no_video_file(video_paths)
        chapter_name = chapter_name or os.path.basename(chapter_path)  # 获取目录名
        output_dir = output_dir + "\\" + chapter_name
        # @modified 修改了路径
        output_dir = Assember._setDir(output_dir)
        videos = [
            Assember.executeVideo(
                video_path=v_path,
                output_dir=output_dir,
                video_id=i + 1,
                chapter_id=chapter_id,
            )
            for i, v_path in enumerate(video_paths)
        ]
        return Chapter(
            id=chapter_id, name=chapter_name, course_id=course_id, videos=videos
        )

    @staticmethod
    def executeVideo(
        video_path,
        output_dir=RootPath.output_videos_dir,
        video_id="",
        chapter_id="",
        name="",
    ) -> Video:
        print(f'RootPath.output_videos_dir: {RootPath.output_videos_dir}')
        print(f"output_dir: {output_dir}")
        output_dir = output_dir + (
            name or ("\\" + os.path.basename(video_path).split(".")[0])
        )
        # @modified 修改了路径
        output_dir = Assember._setDir(output_dir)
        return Video(
            video_path=video_path,
            output_dir=output_dir,
            video_id=video_id,
            chapter_id=chapter_id,
            name=name,
        )

    @classmethod
    def execute(cls, _type, resource_root_path, output_dir='', id="", name="", parent_id=""):
        output_object_path = ''
        r = {}
        if _type == cls.COURSE:
            output_dir = output_dir or path.RootPath.output_courses_dir
            output_object_path = path.RootPath.output_course_object_dir
            r = cls.executeCourse(resource_root_path, output_dir, id, name)
        elif _type == cls.CHAPTER:
            output_dir = output_dir or path.RootPath.output_chapters_dir
            output_object_path = path.RootPath.output_chapter_object_dir
            r = cls.executeChapter(
                resource_root_path, output_dir, id, name, parent_id)
        elif _type == cls.VIDEO:
            output_dir = output_dir or path.RootPath.output_videos_dir
            output_object_path = path.RootPath.output_video_object_dir
            r = cls.executeVideo(resource_root_path, output_dir,
                                 video_id=id, chapter_id=parent_id, name=name)
        if r:
            r.name = utils.saveObject(output_object_path, r)
        return r

    @staticmethod
    def set_step(step='fps', speed_x=1):
        args.set_step(step, speed_x)

    @staticmethod
    def __filter_no_dir(paths):
        return list(filter(lambda p: os.path.isdir(p), paths))

    @staticmethod
    def __filter_no_video_file(paths):
        return list(filter(lambda p: os.path.isfile(p) and filetype.is_video(p), paths))

    @staticmethod
    def _setDir(dir_path):
        """
        作用: 设定存放处理结果的目录
        如果目录不存在, 就创建目录; 存在就清空目录下的文件
        :param dir_path:
        :return:
        """
        # @MODIFY 为了可以找到图片的路径
        dir_path = dir_path.replace(" ", args.path_space_fill_char).replace(
            "\t", args.path_space_fill_char)
        if not os.path.exists(dir_path):
            os.makedirs(dir_path, mode=0o777, exist_ok=True)
            # os.mkdir( dir_path )
        else:
            shutil.rmtree(dir_path)
            os.mkdir(dir_path)
        return dir_path
