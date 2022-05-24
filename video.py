from PIL import Image
import random
from concurrent import futures
from pathlib import Path
import time
from typing import List
import filetype
import shutil
import glob
import cv2 as cv
import numpy as np
from paddleocr import PaddleOCR, draw_ocr
import os
from prometheus_client import Enum
# import paddle

from . import utils, vo
from .config import args
from .sim_v2 import TextSimilarity
from .config.path import RootPath

from vsearch.config import path

if args.Performance.use_gpu:
    print('启用GPU............')
    import paddle

    os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

    # @RISK 判断设备是否存在 再设置
    if paddle.get_device() != 'cpu':
        paddle.set_device(args.Performance.gpu_name)
    print(f'current use device: {args.Performance.gpu_name}')
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


from threading import Semaphore


class ThreadManager:

    @staticmethod
    def getPoolsExecutor(max_workers=None, mode=None):
        '''
            推荐设置: 不设置, 使用系统自动设置
        '''
        if max_workers is None:
            max_workers = None if args.Performance.th_process_nums is 'auto' else args.Performance.th_process_nums
        # @RISK 线程和进程的上限是多少合适, 好像系统会自动弄

        if mode is None:
            mode = args.Performance.process_mode

        if mode == 'thread':
            return futures.ThreadPoolExecutor(max_workers=max_workers)
        elif mode == 'process':
            return futures.ProcessPoolExecutor(max_workers=max_workers)
        else:
            return futures.ThreadPoolExecutor(max_workers=1)
        # return futures.ProcessPoolExecutor()


class OCR:
    paddle_ocr_init_args = {
        "det_model_dir": RootPath.det_model_dir,
        "rec_model_dir": RootPath.rec_model_dir,
        "cpu_threads": args.Performance.cpu_threads,
        "enable_mkldnn": args.enable_mkldnn,
        "det_db_box_thresh": args.det_db_box_thresh,
        "det_db_unclip_ratio": args.det_db_unclip_ratio,
        "show_log": False,
        "use_angle_cls": False
    }
    '''
        可以根据情况动态增加线程
    '''

    def __init__(self, ocr_num=args.Performance.ocr_num, ocr_load=args.Performance.ocr_load):
        '''
        ocr_num: 创建的OCR对象的个数
        ocr_load: 每个OCR对象, 同时处理的线程的最大数量
        '''
        self.ocr_num = ocr_num
        self.ocrs = [PaddleOCR(**self.paddle_ocr_init_args)
                     for i in range(ocr_num)]
        self.locks = [Semaphore(ocr_load) for i in range(ocr_num)]

    def ocr(self):
        pass

    def ocr_save(self, **kwargs):
        i = random.randint(0, self.ocr_num - 1)
        self.locks[i].acquire()
        result = self.ocrs[i].ocr(**kwargs)
        self.locks[i].release()
        return result


# from threading import S
# 现在考虑如何让一个线程并发两个线程, 幸好两


# @RISK 每次导入都会执行一次
my_ocr = OCR()


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
        # print( '需要读取的图片路径' )
        # http://127.0.0.1:5000/static/vsearch-output/videos/pattern_pure_ppt/-0.png'
        file_path = utils.url2local(pf.img_url)  # url路径转本地路径
        frame = utils.cvimread(file_path)
        frame = cv.cvtColor(frame, cv.COLOR_BGR2RGB)  # 修正色域为Image读取正常
        frame = draw_ocr( frame, pf.boxes )  # 圈出搜索结果
        im_show = Image.fromarray(frame)
        # im_show shape h,w,c

        # 图片的输出目录 定义
        output_dir = path.RootPath.output_search_result_dir
        output_dir = f'{output_dir}\\{cls.search_timestamp}'  # 构建输出目录
        output_dir = Searcher.__setDir(output_dir)

        # 用时间标识每次产出的图片的唯一性, 符合url的唯一定位特点
        file_path = f'{output_dir}\\_{int( time.time_ns() ) % 100000000}_.{args.img_format}'
        # print( f"处理过的图片保存路径: {file_path}" )
        im_show.save(file_path)  # 结果图片保存在代码同级文件夹中, (output_dir下更准确)
        img_url = utils.local2url(file_path)
        pf.img_url = img_url  # 此时的 pf中的img_url为框出搜索结果的图片url
        # print( f"图片url: {img_url}" )
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
        name = utils.unify_file_name(name)
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
# paddleOCR = PaddleOCR(
#     det_model_dir=RootPath.det_model_dir, rec_model_dir=RootPath.rec_model_dir,
#     cpu_threads=args.cpu_threads,
#     enable_mkldnn=args.enable_mkldnn,
#     det_db_box_thresh=args.det_db_box_thresh,
#     det_db_unclip_ratio=args.det_db_unclip_ratio,
#     show_log=False
# )


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

    def __init__(self, id, frame, ms, img_outpath, video_id="", section_id=None, ocr=my_ocr):
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
        self.section_id = section_id

        self.start_id = id  # 开始播放的帧

        self.frame = frame
        self.is_into_iter = self.__is_into_iter()  # @IMPROVEMENT 算是性能优化, 可以让下面的代码不需要执行
        if not self.is_into_iter:
            return

        self.outpath = img_outpath
        self.video_id = video_id
        self.ms = ms
        self.blur_score = cv.Laplacian(frame, cv.CV_32F).var()  # 拉普拉斯计算模糊度
        self.contrast = self.frame_std = self.frame.std()  # 用图像标准差近似等同于对比度
        """
        @WAIT 返回的结果是否需要去除 停用词
        @PERFORMANCE 把np.array去除, 因为只有txts使用到np.array方法
        """

        self.result = np.array(ocr.ocr_save(img=frame, cls=False))  # 提取帧中的内容
        if len(self.result) == 0:  # 如果帧中没有内容
            self.has_txt = False
            self.boxes = np.array([])
            self.txts = np.array([])
            self.scores = np.array([])
            self.avg_score = 0
            return
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
        # self.name = self.get_name()

    def get_name(self):
        """ 新增： 该获取帧的名字
        """
        name = f"{self.video_id}{args.img_name_gap}{self.id}" if self.video_id != "" else f"{self.id}"
        if self.id != self.start_id:
            name = f"{name}{args.frame_name_gap}{self.start_id}"
        if self.section_id is not None:
            name = f'{self.section_id}{args.img_name_gap}{name}'
        return name

    def __is_into_iter(self):
        """
           作用: 设定一系列条件, 判断当前帧是否需要,进行迭代的处理, 还是直接废弃
        """
        return True  # 关闭下方的过滤器
        # 无内容过滤
        boxes = paddleOCR.text_detector(self.frame)[0]
        boxes_num = len(boxes)
        # print(f'boxes_num: {boxes_num}')
        if boxes_num == 0:
            return False

        th_min_box_height = Video.th_min_box_height  # @RISK 和视频的分辨率有关
        print(f'th_min_box_height: {th_min_box_height}')

        # 代码行数过滤
        # @WAIT 可以训练一个代码识别器, 直接判断是否是代码页
        # @RISK 不是代码框的也会被识别成代码框过滤
        max_codeline_num = list(
            filter(lambda box: (box[2][1] - box[0][1]) < th_min_box_height and (
                box[1][0] - box[0][0]) > th_min_box_height * args.height_multiple_x,
                boxes)).__len__()  # 根据候选框的框高 和 框的长度过滤, 计算过滤后的代码框的数量
        print(f'min_codeline_num: {max_codeline_num}')
        if max_codeline_num > args.th_max_codeline_num:
            return False

        # # 框数过滤
        # print(f'boxes_num: {boxes_num}')
        # if boxes_num > args.th_max_boxes_num:
        #     return False

        # 最小框数量过滤
        min_boxes_num = list(
            filter(lambda box: (box[2][1] - box[0][1]) < th_min_box_height, boxes)).__len__()
        print(f'min_boxes_num {min_boxes_num}')
        if min_boxes_num > args.th_min_boxes_num:
            return False

        # 最小框比例过滤
        min_boxes_rate = min_boxes_num / boxes_num
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

    def getAllTextArray(self):
        """
            功能: 数据的形式返回所有文本
        """
        return self.txts

    def getAllTextStr(self, ignore_case=True, join_char='。') -> str:
        """
            功能: 将所有的文本变成字符串统一返回
            @RISK 没有任何分隔符号进行拼接
        """
        return join_char.join(self.txts).casefold() if ignore_case else join_char.join(self.txts)

    def getAllTextLen(self):
        """
            统计该页面中含有的词的数量
        """
        return sum([len(s) for s in self.txts])

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
            name=self.get_name(),
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
            f"{self.outpath}\\{self.get_name()}.{args.img_format}")
        # print( f'img_path: {img_path}' )
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
        # print( f"img_url: {img_url}" )
        self.img_url = img_url
        self.img_local_path = img_path
        # @RISK 删除属性, 节约持久化需要的内存
        del self.frame
        del self.result

    def getSimScoreV1(self, pre_pf):
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

    def getSimScore(self, nt_pf):
        """ 最终选择的策略 """
        return TextSimilarity.getSimScore(self.getAllTextStr(), nt_pf.getAllTextStr())

    def getSimScoreV4(self, nt_pf):
        """
            @return ret, sim; （字符级别对比相似）
            ret: 0: 相同 1：前比后大 -1： 后比前大
        """
        return TextSimilarity.getSimScoreV4(self.getAllTextStr(), nt_pf.getAllTextStr())

    def getSimScoreV4_2(self, nt_pf):
        """
            @return ret, sim; (jieba分词，去停用词)
            ret: 0: 相同 1：前比后大 -1： 后比前大
        """
        return TextSimilarity.getSimScoreV4_2(self.getAllTextStr(), nt_pf.getAllTextStr())


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

    def getList(self) -> List[PaddleFrame]:
        return self.frame_list

    def __getitem__(self, index) -> PaddleFrame:
        return self.frame_list[index]

    def add(self, pf: PaddleFrame):
        self.frame_list.append(pf)

    def updateTail(self, pf):
        self.update(self._len() - 1, pf)

    def get(self, i) -> PaddleFrame:
        self._check_valid(i)
        return self.frame_list[i]

    def getHead(self) -> PaddleFrame:
        return self.get(0)

    def getTail(self) -> PaddleFrame:
        if self._len() == 0:
            raise IndexError("当前列表为空")
        return self.get(self._len() - 1)

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

    def setList(self, frame_list: List[PaddleFrame]):
        self.frame_list = frame_list

    def pop(self, i) -> PaddleFrame:
        self._check_valid(i)
        return self.frame_list.pop(i)

    def popHead(self) -> PaddleFrame:
        return self.pop(0)

    def popTail(self) -> PaddleFrame:
        if self._len() == 0:
            raise IndexError("当前列表为空")
        return self.frame_list.pop(self._len() - 1)

    def remove_duplicate_v2(self) -> List[PaddleFrame]:
        """
        图片内容去重
        @WAIT 保留内容文字更多的 | 内容还有 时间节点做更改
        使用双向相似度
        """
        print(f'去重前： {self._len()}')
        frame_list = self.frame_list
        if self._len() <= 1:  # 两个才需要去重
            return self.frame_list
        i = 1
        pre_pf = frame_list[0]
        while i < self._len():  # i还在范围内容
            next_pf = frame_list[i]
            ret, sim = pre_pf.getSimScore(next_pf)
            if sim < args.th_sim_score:
                pre_pf = next_pf
                i += 1
                continue
            # 符合条件
            if ret > 1:  # next_pf内容多
                next_pf.start_id = pre_pf.start_id
                next_pf.ms = pre_pf.ms

                pre_pf = next_pf
                self.frame_list.pop(i - 1)  # 去除 pre
            else:  # pre_pf内容多
                self.frame_list.pop(i)  # 去除后面一帧
        print(f'去重后： {self._len()} ')
        return self.frame_list

    def remove_duplicate(self) -> List[PaddleFrame]:
        """
        图片内容去重
        @WAIT 应该保留图片清晰度较好的| 保留内容文字更多的 | 最后 内容还有 时间节点做更改
        双向相似度
        """
        print(f'去重前： {self._len()}')
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
                    if cur_score > nt_score:
                        frame_list.pop(i)
                    else:  # 交换信息, 删除后一个
                        cur.ms = nt.ms
                        cur.start_id = nt.start_id
                        # @MODIFY cur.get_name() = nt.get_name()
                        cur.id = nt.id
                        frame_list[nt_i] = cur
                        frame_list.pop(i)
            else:
                break
        print(f'去重后： {self._len()} ')
        return self.frame_list

    def saveKfs(self):
        for kf in self.frame_list:
            kf.save()

    # def _isSim(self, pf1: PaddleFrame, pf2: PaddleFrame):
    #     score = pf1.getSimScoreV3(pf2)
    #     return True if score > 0.85 else False

    def __len__(self):
        return self._len()

    def is_empty(self):
        return self._len() == 0


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
    #     for pf in self.sections_kfs[section_id].getList():
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

        # 初始化Opencv相关对象
        self.cap = cv.VideoCapture(video_path)  # 获取指定路径的视频对象
        self.fps = int(self.cap.get(cv.CAP_PROP_FPS))
        self.width = self.cap.get(cv.CAP_PROP_FRAME_WIDTH)
        self.height = self.cap.get(cv.CAP_PROP_FRAME_HEIGHT)
        self.frame_counts = int(self.cap.get(cv.CAP_PROP_FRAME_COUNT))
        del self.cap

        Video.th_min_box_height = args.update_th_min_box_height(self.height)

        # 初始化帧间隔
        if args.step == "fps":
            self.step = self.fps * args.speed_x
        else:
            self.step = args.step * args.speed_x

        self._init_section()  # 初始化 分区
        self.sections_kfs = [KeyFrames()
                             for i in range(self.section_nums)]  # 初始化每个分区的kfs
        self.caps = [cv.VideoCapture(video_path) for i in range(
            self.section_nums)]  # 每个分区一个cap不冲突

        print('多分区PaddleOCR 初始化完成 ! ')

        if self.fps > 0:  # 有些垃圾的视频文件, 没有内容, 导致 除0的报错
            self.total_time_ms = self.frame_counts / self.fps * 1000

            self.old_frames = [None] * self.section_nums
            self._run()  # 运行完成产出关键帧
            del self.old_frames

            # @RISK 保存完成将 kfs: KeyFrame ->  kfs: list, 同时释放内存

        # 进行数据整合
        # self.sections_kfs[section_id] = []  # 所有关键帧存放的地方，
        # for kfs in self.sections_kfs:
        #     self.sections_kfs[section_id] += kfs.getList()
        # self.sections_kfs  # 还可以用在搜索里进行并发
        del self.caps  # 释放
        # if run:
        #     self._run()

    def _getPoolsExecutor(self):
        return ThreadManager.getPoolsExecutor(mode=args.Performance.video_process_mode,
                                              max_workers=args.Performance.th_video_multiple_nums)

    def _fastProcess(self, func, args) -> list:
        with self._getPoolsExecutor() as executor:
            return list(executor.map(func, args))

    def _init_section(self):
        '''
            一个完整的视频切分为n个区间，使用多线程处理
            结果：获取 sections = [ [0, 400], []  ], 其中[0, 400] 代表第一个区间，0帧的开始编号, 400代表帧的结束编号
        '''
        self.process_frame_sum_counts = self.frame_counts // self.step  # 一个视频需要处理的视频帧

        self.section_nums = self.thread_nums = self.process_frame_sum_counts // args.Performance.th_mul_thread_on_frame_counts  # 区间大小， 每个线程处理的任务量

        self.gap = args.Performance.th_mul_thread_on_frame_counts * self.step
        if self.section_nums == 0:
            self.thread_nums = self.section_nums = 1  # 代表使用多线程
        print(f'v: {self.name} 需要遍历的帧为： {self.process_frame_sum_counts}')
        print(f'分区数量（线程数量）：{self.section_nums}')
        # @WAIT 帧id的取值是从0开始的吗, 是的话需要　self.frame_counts - 1
        self.sections = [
            [i * self.gap, self.frame_counts -
             1] if i == (self.section_nums - 1) else [i * self.gap, (i + 1) * self.gap]
            for i in range(self.section_nums)
        ]  # sections = [ [0, 400], []  ]

    def getKfs(self):
        return [kf for s_kfs in self.sections_kfs for kf in s_kfs]

    def searchByKey(self, key, json_dumps=False):
        """
            视频内容的搜索方法: 可以并发搜索
            @RISKED 如果每个分片的内容比较少，并发反而增加时间，但是在配置文件中，已经设置了阈值，也就是最小任务量了，所以不需要担忧
        """
        kfs = []

        def unit(s_kfs: KeyFrames):
            """
                多线程 搜索 单元
            """
            search_kfs = []
            for pf in s_kfs:
                pfvo = pf.searchByKey(key)
                if not pfvo.isEmpty():
                    search_kfs.append(pfvo)
            return search_kfs

        results = self._fastProcess(unit, self.sections_kfs)
        for result in results:
            kfs += result

        result = vo.Video(
            id=self.id, kfs=kfs, name=self.name, local_path=self.local_path, chapter_id=self.chapter_id, url=utils.local2url(self.local_path)
        )
        return utils.json_dumps(result) if json_dumps else result

    def __generate_courseware(self, path_type: CWPathType) -> str:
        """ 生成课件
        return 课件的本地地址
        """
        if not self.courseware_path:
            # @MODIFY 如果课件不存在就会重新生成, 所以可以随便删除
            imgs = [
                pf.img_local_path for kfs in self.sections_kfs for pf in kfs]
            if len(imgs) == 0:
                return "不存在课件？"  # @RISK 就算什么东西也没有，也最好返回一个封面吧
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
    def _section_iter_func(self, pf: PaddleFrame, section_id):
        """
            对__run方法遍历的帧进行相关的处理, 判断是否需要加入关键帧集合
        """
        print("------------------------------")
        # print(f"有效帧数: {self.processed_kfs_count}  当前帧: {pf.id}")
        print(
            f'{pf.get_name()}\ncontent: {pf.getAllTextArray()}\n第 {section_id} 区， 有效帧数为： {len( self.sections_kfs[section_id] )} ')
        cur_kfs = self.sections_kfs[section_id]
        old_pf = self.old_frames[section_id]

        def link_up(pf: PaddleFrame, old_pf: PaddleFrame = self.old_frames[section_id]):
            """ 进行帧之间的衔接操作 """
            pf.start_id = old_pf.start_id
            pf.ms = old_pf.ms

        def set_old_frame(pf: PaddleFrame):
            self.old_frames[section_id] = pf

        def kfs_update(pf: PaddleFrame):
            """
                需要保证加入的帧为关键帧
            """
            # def decision(pf: PaddleFrame, other_pf: PaddleFrame):
            #     d = [900, 990]
            #     np.abs( (d[0] - d[1]) / sum( d ) )

            kfs = self.sections_kfs[section_id]
            if kfs.is_empty():
                kfs.add(pf)
            else:  # 直接加入？需要保证为关键帧
                # link_up(pf) # 衔接
                ret, sim = kfs.getTail().getSimScore(pf)
                if sim > args.th_sim_score:  # 相似
                    if ret == 1:  # pf内容多
                        link_up(pf, kfs.getTail())
                        kfs.updateTail(pf)
                    elif ret == 0:  # @RISK 通过相似度判断内容增加减少, 有局限性, 带有英文的, 单词会被压缩成字母, abc 和 abccccc 没有区别, 会判断为内容相同
                        pf_len, tail_len = pf.getAllTextLen(), kfs.getTail().getAllTextLen()
                        if pf_len > tail_len:  # 修复局限性, 对比内容的长度
                            link_up(pf, kfs.getTail())
                            kfs.updateTail(pf)

                        elif pf_len == tail_len:  # 长度相同, 选择更清晰的 @RISK @HYPOTHESIS 假设paddle ocr 的 文本框检测的分数得分, 代表文本清晰度, 因为越清晰越容易被检测到
                            '''
                                1. 远近切换，选择近处的，也就是大屏幕优先： 其实就是字体大的优先，也就是框框长度总和更长的优先 | 
                                2. 对比度大的优先
                                3. 更清晰的优先
                                我感觉 大屏幕的 优先级别最高把

                                TODO： 大屏幕兼容， 英文PPT的兼容处理 
                            '''
                            # pf.boxes # 格式是什么样的呢 需要print一下
                            if pf.contrast > kfs.getTail().contrast:
                                link_up(pf, kfs.getTail())
                                kfs.updateTail(pf)
                            # if pf.blur_score > kfs.getTail().blur_score: # pf.avg_score > kfs.getTail().avg_score or
                            #     link_up( pf, kfs.getTail() )
                            #     kfs.updateTail( pf )
                        else:  # 内容是真的没变化
                            return
                    else:  # 内容减少, 丢掉就好了
                        return
                else:  # 不相似
                    kfs.add(pf)

        if (not pf.is_into_iter) or (pf.blur_score < args.th_blur_score) or (pf.avg_score < args.th_avg_score) or (
                not pf.has_txt):
            # print( f"{pf.get_name()}过滤了" )
            # 过滤
            set_old_frame(pf)  # 动画过渡, 其实可以做成, with语句
            return
        if old_pf is None:
            # @NOTING为什么要加？ 因为，上面的所有条件符合，说明它是课件帧， 说明可以进入后续的循环处理，但是kfs没东西，直接加入课件帧列表就好了
            if cur_kfs.is_empty():
                kfs_update(pf)
            set_old_frame(pf)
            return

        # if cur_kfs.is_empty():
        #     print( '=======================================' )
        #     print( '=======================================' )
        #     print( '=======================================' )
        #     print( '=======================================' )

        # def kfs_add(pf: PaddleFrame):
        #     kfs = self.sections_kfs[section_id]
        #     if not kfs.is_empty():
        #         ret, sim = kfs.getTail().getSimScore(pf)
        #         if sim > args.th_sim_score:
        #             if ret == 1: # pf内容多
        #                 kfs.updateTail(pf)
        #             elif ret == 0:
        #                 if pf.blur_score > kfs.getTail().blur_score:
        #                     kfs.updateTail(pf)
        #             else: # 内容减少, 丢掉就好了
        #                 return
        #         else:
        #             kfs.add(pf)
        #     else:
        #         kfs.add(pf)
        # @WAIT 具体的相似度算法可以参考策略模式, 将具体使用哪个相似度算法, 抽象成接口, 或者配置, 可以直接切换, 而不是这里写死
        ret_old, sim_score_old = pf.getSimScore(old_pf)
        # ret_kfs_tail, sim_score_kfs_tail = pf.getSimScore(cur_kfs.getTail())
        # sim_score = max(sim_score_old, sim_score_kfs_tail)

        if sim_score_old > args.th_sim_score:  # 前后帧相似 | 不进行帧的添加, 动画过渡
            # link_up( pf, old_pf )
            if ret_old == -1:  # 内容增加
                kfs_update(pf)
                set_old_frame(pf)

            elif ret_old == 1:  # 内容减少, 不理睬
                # link_up( pf )
                set_old_frame(pf)

            else:  # 内容不变
                if pf.blur_score > old_pf.blur_score:  # 更清晰
                    # link_up( pf )
                    kfs_update(pf)
                set_old_frame(pf)

        else:  # 前后帧区别很大 | 对比kfs
            # link_up( pf )
            kfs_update(pf)
            set_old_frame(pf)

        # 两步计算相似度, 解决状况:  PPT内容展示有动画, 例如: 内容: a -> 过渡动画 -> ab, 其实还是同一页, 但是如果只计算sim(old, cur), a变模糊, 再到没有a->插入列表->再出现ab
        # if self.sections_kfs[section_id].is_empty():
        #     sim_score = sim_score_old
        # else:
        #     tail_frame = self.sections_kfs[section_id].getTail()
        #     ret, sim_score_kfs_tail = pf.getSimScore(tail_frame)
        #     # 如果分数高的是末尾
        #     sim_score = max(sim_score_old, sim_score_kfs_tail)
        # 还需要修复 关键点1 -> full, 再来一次 1-> full, 会导致重复的发生
        # @PERFORMANCE 去重的操作如果影响性能, 可以提供用户点击去重效果
        # print(f"sim_score: {sim_score}")
        # # @WAIT 逆向相似度 > 正向相似度, 说明在减少内容, 是动画
        #
        # # 内容增加判断
        # if sim_score > args.th_sim_score:  # 判断是否相似
        #     # 增加内容的比较, 也要和 tail末尾的比较, 不过得相似的前提下
        #     # 内容增加
        #     # @RISK 用字符串判别也行
        #     if pf.getAllTextLen() > self.old_frames[section_id].getAllTextLen():
        #
        #         # pf.name = pf.name + \
        #         #     f"{args.frame_name_gap}{self.old_frames[section_id].id}"
        #         if self.sections_kfs[section_id].is_empty():  # 如果关键帧列表为空
        #             link_up(pf, self.old_frames[section_id])
        #             self.sections_kfs[section_id].add(pf)
        #             # print(
        #             #     f"上一帧内容: {self.old_frames[section_id].getAllTextArray()}   这一帧率的内容: {pf.getAllTextArray()}")
        #             print(f"（第一帧）加入一帧: {pf.get_name()}")
        #             print(
        #                 f"上一帧内容: {self.old_frames[section_id].getAllTextArray()}  \n这一帧率的内容: {pf.getAllTextArray()}")
        #             set_old_frame(pf)
        #         else:
        #             tail_frame = self.sections_kfs[section_id].getTail()
        #             link_up(pf, self.old_frames[section_id])
        #             self.sections_kfs[section_id].updateTail(pf)
        #             print(
        #                 f"(内容增加)当前帧: {pf.get_name()}  被替换帧: {tail_frame.get_name()}")
        #             print(
        #                 f"当前帧内容: {pf.getAllTextArray()} \n kfs被替换内容: {tail_frame.getAllTextArray()}")
        #             set_old_frame(pf)
        #
        #     # 内容减少
        #     elif pf.getAllTextLen() < self.old_frames[section_id].getAllTextLen():
        #         # 保留内容多的一帧, 就是oldframe不能变,这个意思
        #         link_up(pf, self.old_frames[section_id])
        #         set_old_frame(pf)  # 为了保留上一帧的特性
        #
        #     else:  # 图片内容相同, 且内容没有增加了,
        #         if not self.sections_kfs[section_id].is_empty():
        #             tail_frame = self.sections_kfs[section_id].getTail()
        #             if pf.blur_score > tail_frame.blur_score:  # 保留图片清晰图更好的图像
        #                 # tail_frame.blur_score = pf.blur_score
        #                 # tail_frame.frame = pf.frame
        #                 link_up(pf, self.old_frames[section_id])
        #                 self.sections_kfs[section_id].updateTail(
        #                     pf)
        #                 print(
        #                     f"(内容不变)当前帧: {pf.get_name()}  kfs——tail: {tail_frame.get_name()}")
        #                 print(
        #                     f"当前帧内容: {pf.getAllTextArray()} \n 被替换内容: {tail_frame.getAllTextArray()}")
        #         set_old_frame(pf)
        #         # self.old_frames[section_id] = origin_pf
        # else:  # 不相似
        #     # print(
        #     #     f"上一帧内容: {self.old_frames[section_id].getAllTextArray()}   这一帧率的内容: {pf.getAllTextArray()}")
        #     # link_up(pf, self.old_frames[section_id])
        #     tail_frame = self.sections_kfs[section_id].getTail()
        #     print(
        #         f"相似度低: {sim_score}  加入一帧: {pf.get_name()}  上一关键帧: {tail_frame.get_name()}")
        #     print(
        #         f"当前帧: {pf.getAllTextArray()}  \n 上一kfs帧: {tail_frame.getAllTextArray()}")
        #     self.sections_kfs[section_id].add(pf)
        #     set_old_frame(pf)
        #
        # # 指定一系列过滤条件
        # # 如果 分数大于 0.95, 不保留,
        # # 如果没有内容 也不保留
        # # self.old_frames[section_id] = origin_pf # 到了最后还是变了啊
        # print("------------------------------")

    def _run(self):
        '''' 分配任务
            n: 切分成的任务数量
        '''
        """
            分配方法： 
                1. 等分n个区间, 有序的n个任务
                2. 将n个任务的结果，添加为关键帧，合并结果
                3. 合并完成后，同步结果，进行后续的操作

            区间切分方法：
                1. gap = total // n
                2. section 1 = [0, gap], section 2 = [gap, 2gap], ... , section n = [n-1gap, total]

            区间执行方法：
                1. 设置开始遍历的帧位置，即set start frame id = section start id
                2. 临时存储关键帧
                3. when current frame id out of the section range, then pause
                4. return keyframes

            所有任务进行合并：
                1. 边界帧进行去重
                2. 顺序整合所有帧

            边界帧去重方法：
                1. 获取section k的最后一帧作为a帧， 和section k+1的第一帧作为b帧
                2. 按照预定的方法计算相似度
                3. 若符合相似条件，则保留b帧;否则，同时保留；

                @RISKED：什么情况下，两帧都不要了呢？当然是两帧都没有内容的情况下，但是该情况已经被考虑过了，所以忽略。即按照预定方法，能留下来的帧都是有用的帧。因此不存在该情况。
        """
        # args = (self.sections, list( range( self.section_nums ) ))
        # for arg in zip(*args):
        #     print(arg)
        # arg：section, section_id:  [0, 400], 1
        with self._getPoolsExecutor() as executor:  # 应该在这里传入各种各样的需要阐述才对, 比如KFS,OCR等资源, 而不是通过ID号来获取
            args = (self.sections, list(range(self.section_nums)))
            executor.map(self._process_section, *args)

        # 打印 帧列表名字
        # print( '===================================' )
        old_frame = [None]

        # def print_pf_content(pf: PaddleFrame):
        #     print( '------------------' )
        #     if old_frame[0] is None:
        #         print( f'{pf.get_name()}\ncontent: {pf.getAllTextStr()}' )
        #     else:
        #         print( f'{pf.get_name()}\ncontent: {pf.getAllTextStr()}' )
        #         print(
        #             f'{old_frame[0].get_name()}\ncontent: {old_frame[0].getAllTextStr()}' )
        #         print( f'{pf.getSimScore( old_frame[0] )}' )
        #     old_frame[0] = pf

        # [print_pf_content( pf ) for kfs in self.sections_kfs for pf in kfs] # 打印去重之前的所有图片名
        # print( '===================================' )
        # utils.saveObject(path.getProjectRootPath(), self.sections_kfs, 'test6_sections_kfs')
        self._duplicateSectionKfs()  # 边界去重
        with self._getPoolsExecutor() as executor:  # 保存图片，利于后续保存可见你
            executor.map(lambda kfs: kfs.saveKfs(), self.sections_kfs)

    def _duplicateSectionKfs(self):
        # self.all_kfs = []
        deleted_pf = KeyFrames()
        # 在加一个关键帧区间的去重
        deleted_pre_count = sum([len(kfs) for kfs in self.sections_kfs])

        if self.section_nums > 1:
            pre_kfs = self.sections_kfs[0]
            i = 1
            while i < self.section_nums:
                """
                @RISK 遇到空的区间就没了
                1. 完全去重
                2. 并发去重
                3. 重写代码, 解决区间为空的状况
                """
                # for i in range(1, self.section_nums):
                next_kfs = self.sections_kfs[i]
                if pre_kfs.is_empty():  # 一个为空, 右移
                    self.sections_kfs.pop(i - 1)  # 空了就没必要留着
                    self.section_nums = self.thread_nums = self.section_nums - 1
                    pre_kfs = next_kfs
                    continue
                elif next_kfs.is_empty():  # 后面为空
                    self.sections_kfs.pop(i)
                    self.section_nums = self.thread_nums = self.section_nums - 1
                    continue
                else:
                    pre_pf = pre_kfs.getTail()
                    next_pf = next_kfs.getHead()
                    ret, sim = pre_pf.getSimScore(next_pf)
                    # ret: 0: 相同 1：前比后大 -1： 后比前大
                    if sim > args.th_sim_score:  # 需要进行比较, 至少去除一个, 那么去除后需要重新比较, 所以i不变
                        # 删除, 并且删除信息少的那一个 | 哪个信息少，前/后 分数高，则后内容多
                        if ret > 0:  # -1 后面的信息多，保后， 去前
                            next_pf.ms = pre_pf.ms
                            next_pf.start_id = pre_pf.start_id
                            pre_kfs.popTail()
                            pre_pf.start_id = f'{pre_pf.start_id}$'
                            deleted_pf.add(pre_pf)
                        else:  # 0 1 前面的信息多， 保前去后
                            pre_pf.id = next_pf.id  # 衔接
                            next_kfs.popHead()
                            next_pf.start_id = f'{next_pf.start_id}$'
                            deleted_pf.add(next_pf)
                    else:  # 不需要改动, 进行右移
                        pre_kfs = next_kfs  # 区域右移动
                        i += 1  # 区域右移动
                        # else: # 信息一样多，保留更清晰的
                        #     if pre_pf.avg_score > next_pf.avg_score:
        print(
            f'课件帧的数量\n去重前： {deleted_pre_count}\n去重后: {sum( [len( kfs ) for kfs in self.sections_kfs] )}')
        deleted_pf.saveKfs()

    def get_section_kfs_size(self, section_id):
        return len(self.sections_kfs[section_id])

    def get_all_section_kfs_size(self):
        return sum([len(kfs) for kfs in self.sections_kfs])

    def _process_section(self, section: tuple, section_id: int):
        """ 
        功能： 处理一个section中的内容 | 区间去重
         """
        print(
            f"current section: {section}, section_id: {section_id}")

        low_pos, hight_pos = section
        print(f'low_pos: {low_pos} hight_pos: {hight_pos}')
        # 开始处理视频
        # 初始化
        # @WAIT 初始化第一个oldframe
        # self.old_frames[section_id] = PaddleFrame(
        #     frame_id, frame, frame_ms, self.output_dir, self.id
        # )
        # 设置初始位置
        self.caps[section_id].set(cv.CAP_PROP_POS_FRAMES, low_pos)

        # is_out_of_index = False  # 是否已经越界
        # 开始正式的处理
        while True:
            current_pos = self.caps[section_id].get(cv.CAP_PROP_POS_FRAMES)
            if current_pos > hight_pos - 1:  # 大于就置顶
                # self.caps[section_id].set( cv.CAP_PROP_POS_FRAMES, hight_pos )
                # is_out_of_index = True
                return
            ret, frame = self.caps[section_id].read()
            if ret:
                # 当前位置id帧编号, base-0开始编号， @NOTING　为什么　这里需要　－１　呢， 回退到上一帧吗？
                frame_id = int(current_pos)
                frame_ms = self.caps[section_id].get(cv.CAP_PROP_POS_MSEC)
                print(
                    f'第 {section_id} 区 {section}: 进度: {frame_id - low_pos}/{hight_pos - low_pos}')
                # 增加一层, 框框数太多, 为代码也, 框框的高度大小, 代码也
                self._section_iter_func(
                    pf=PaddleFrame(
                        frame_id, frame, frame_ms, self.output_dir, self.id, section_id=section_id,
                        ocr=my_ocr
                    ),
                    section_id=section_id
                )
                self.caps[section_id].set(
                    cv.CAP_PROP_POS_FRAMES, frame_id + self.step)
            else:
                break

        # 去重 @RISK 正常情况下不需要去重
        # self.sections_kfs[section_id].remove_duplicate_v2()
        print('------------------------------------------')
        print(f'section {section_id} 处理完毕 ! ')
        print(f'当前分区有效帧为:  {self.get_section_kfs_size( section_id )}')
        print(f'总有效帧为:  {self.get_all_section_kfs_size()}')
        print('-------------------------------------------')


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
        # videos = []

        with ThreadManager.getPoolsExecutor() as executor:
            args = (self.videos, [key] * len(self.videos))
            video_vos = list(executor.map(
                lambda v, key: v.searchByKey(key), *args))
            # WAIT 去空集合, 其实也不一定有必要去, 去了之后目录结构没那么完整
            videos = [v for v in video_vos if not v.isEmpty()]
            # for v in self.videos:
            #     video_vo = v.searchByKey( key )
            #     # if args.search_result_dict_mode:
            #     #     if video_vo['kfs']:
            #     #         videos.append( video_vo )
            #     # else:
            #     if not video_vo.isEmpty():
            #         videos.append( video_vo )
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
        with ThreadManager.getPoolsExecutor() as executor:
            args = (self.chapters, [key] * len(self.chapters))
            cos = list(executor.map(lambda chapter,
                       key: chapter.searchByKey(key), *args))
            cos = [c for c in cos if not c.isEmpty()]
            # chapters = []
            #
            # for c in self.chapters:
            #     chapter_vo = c.searchByKey( key )
            #     # if args.search_result_dict_mode:
            #     #     if chapter_vo['videos']:
            #     #         chapters.append( chapter_vo )
            #     # else:
            #     if not chapter_vo.isEmpty():
            #         chapters.append( chapter_vo )
            result = vo.Course( id=self.id, chapters=cos, name=self.name )
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
        with ThreadManager.getPoolsExecutor(mode=args.Performance.course_process_mode,
                                            max_workers=args.Performance.th_course_multiple_nums) as executor:
            chapters = list(executor.map(lambda arg: Assember.executeChapter(
                chapter_path=arg[1],
                output_dir=output_dir,
                chapter_id=arg[0] + 1,
                chapter_name=os.path.basename(arg[1]),
                course_id=course_id,
            ), enumerate(chapter_dirs)))
            # chapters = [
            #     Assember.executeChapter(
            #         chapter_path=dir_path,
            #         output_dir=output_dir,
            #         chapter_id=i + 1,
            #         chapter_name=os.path.basename( dir_path ),
            #         course_id=course_id,
            #     )
            #     for i, dir_path in enumerate( chapter_dirs )
            # ]
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

        with ThreadManager.getPoolsExecutor(mode=args.Performance.chapter_process_mode,
                                            max_workers=args.Performance.th_chapter_multiple_nums) as executor:
            videos = list(
                executor.map(lambda arg: Assember.executeVideo(
                    video_path=arg[1],
                    output_dir=output_dir,
                    video_id=arg[0] + 1,
                    chapter_id=chapter_id,
                ),  enumerate(video_paths))
            )
            # videos = [
            #     Assember.executeVideo(
            #         video_path=v_path,
            #         output_dir=output_dir,
            #         video_id=i + 1,
            #         chapter_id=chapter_id,
            #     )
            #     for i, v_path in enumerate( video_paths )
            # ]
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
            save=False
    ) -> Video:
        # print( f'RootPath.output_videos_dir: {RootPath.output_videos_dir}' )
        # print( f"output_dir: {output_dir}" )
        output_dir = output_dir + (
            name or ("\\" + os.path.basename(video_path).split(".")[0])
        )
        # @modified 修改了路径
        output_dir = Assember._setDir(output_dir)
        v = Video(
            video_path=video_path,
            output_dir=output_dir,
            video_id=video_id,
            chapter_id=chapter_id,
            name=name,
        )
        if save:
            utils.saveObject(path.RootPath.output_video_object_dir, v)
        return v

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
