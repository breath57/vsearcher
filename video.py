
import copy as cp
import glob
import os
import cv2 as cv
import numpy as np
from paddleocr import PaddleOCR
# import paddle

from . import utils
from .config import args
from .sim_v1 import TextSimilarity
from .config.path import RootPath

from .vo import vo

# paddle.set_device('gpu:0')

"""
PaddleFrame遍历完后, 自动去除cap对象,
图片保存后自动删除self.frame对象
args.speed_x
del self.cap self.result 将 paddleOCR置出 节约持久化
"""
# @risk 环境迁移之后没有cuda可能会报错
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





# @wait Video内容的遍历，有开关控制是否延时加载，还是立即生成， 还有那个apply函数， 目前可以内嵌了， 作为初始化
# @wait 每种对象都需要可以支持传入输出路径，当然最终肯行是需要配置的，所以都是需要装配的
# @wait video图片保存的目录需要保存到配置目录
# @requirement 不管是单个视频，还是章节， 还是课程， 都需要支持导出的功能，

paddleOCR = PaddleOCR(
    det_model_dir=RootPath.det_model_dir,
    rec_model_dir=RootPath.rec_model_dir
)

class PaddleFrame():
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
        @wait 具体的id形式, 具体再确定
        """
        self.id = id
        self.outpath = img_outpath
        self.video_id = video_id
        self.ms = ms
        self.name = f'{video_id}#{self.id}'
        self.frame = frame
        self.blur_score = cv.Laplacian(frame, cv.CV_32F).var()
        """
        @wait 返回的结果是否需要去除 停用词
        @performance 把np.array去除, 因为只有txts使用到np.array方法
        """
        self.result = np.array(paddleOCR.ocr(frame, cls=False))
        if len(self.result) == 0:
            self.has_txt = False
            self.boxes = np.array([])
            self.txts = np.array([])
            self.scores = np.array([])
            self.avg_score = 0
        else:
            self.has_txt = True
            self.boxes = np.array(self.result[:, 0])
            self.txts = np.array(list(map(lambda x: x[0], self.result[:, 1])))
            self.scores = np.array(
                list(map(lambda x: x[1], self.result[:, 1])))
            self.avg_score = np.mean(self.scores)
            # self._save() # 有结果, 图片才需要保存

    def getTitles(self, nums=1):
        """
        获取最有可能是标题的文本内容
        @wait 获取标题, 或者说是该帧内的代表性文本列表
        @risk 获取的title可能会有错误的概率
        """
        # 框框按照 y轴距离, 排序, 获取排序后的索引
        # 过滤掉 标点符号, 之类的内容, 就是除了中文和英文之外的内容
        # 内容长度不能小于几个字, 或者说字数和字体的大小, 都需要占据比重,
        # 因为有写 PPT的LOGO, 很大, 大过标题
        # 标题的位置, 一定是位于上半屏幕的
        # 是否: 去除连续好多页都出现的标题作为搜索关键词?, 不用去除, 还是当作PPT来应用
        # @waitValidate
        # print(self.txts)
        h_weights = [self._getHeightWeight(
            index) for index in range(self.boxes.shape[0])]
        h_indexs = np.argsort(h_weights)[:nums+4]

        lu_weights = [self._getLeftUpWeight(
            index) for index in h_indexs]

        dicts = {}
        for i, w in enumerate(lu_weights):
            dicts.update({w: h_indexs[i]})

        lu_weights_top = np.sort(lu_weights)[:nums]
        indexs = []
        for i, w in enumerate(lu_weights_top):
            indexs.append(dicts.get(w))
        return self.txts[indexs]

    def getBoxesLen(self):
        return len(self.boxes)

    def _getLeftUpWeight(self, index):
        """
        说明: 权重值越小, 则越重要
        """
        box = self.boxes[index]
        # box[0]代表左上方的坐标, box[0][0] + box[0][1]越小, 说明越在左上方
        return box[0][0] + box[0][1]

    def _getHeightWeight(self, index):
        """
        说明: 为了减少一次argsort的排序, 权重值越小, 则越重要
        具体的权重计算还需要验证
        @wait
        """
        # txt = self.txts[index]
        box = self.boxes[index]
        # @waitValidate
        box_height = box[3][1] - box[0][1]
        # txt_width = box[1][0] - box[0][0]
        txt_height = box_height
        # txt_len = len(txt)

        # return txt_height * 0.7 + txt_len * 0.3
        return -(txt_height)

    def getAllTextArray(self):
        return self.txts

    def getAllTextStr(self):
        return "".join(self.txts)


    # @wait 将搜索的方法外置
    def searchByKey(self, key, json_dumps=False):
        """
        :return [{box1相关信息}, {}, {}  ]= 关键帧的box位置的相关信息
            @wait返回True 还是, 返回在具体某个boxes的坐标, 有利于框出来
            @wait @performance好的搜索算法, 或者搜索这一步, 可以放到全局, 而不是每一个帧都搜索一次
            @improvement 将key进行分词 -> 逐搜索 -> 去重 -> 返回结果
            @improvement 支持语义: embedding为词向量 -> 余弦相似度搜索
        """
        # result = []
        key = key.casefold()
        boxes = []
        txts = []
        for i, t in enumerate(self.txts):
            if t.casefold().find(key) != -1:
                #@wait 数据返回的格式待定
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
        # @wait 还可以有 keyword, 也就是每页中 又大又长的框框

        result = vo.Frame( self.id, self.img, boxes, self.name, txts, title=self.getTitles(args.title_num) )
        return utils.json_dumps(result) if json_dumps else result

    # def setOutPath(self, out_path):
    #     self.out_path = out_path


    def save(self):
        img_path = f'{self.outpath}\\{self.name}.{args.img_format}'

        # @note 中文路径图片保存
        cv.imencode( f'.{args.img_format}', self.frame)[1].tofile( img_path )
        # @risk 图片的读取 : 这里指定的类型为 uint8 为0-255, BRG模式, 如果有其他色域的图片, 将不适用
        # cv.imdecode( np.fromfile(img_path, dtype=np.uint8 ), -1 )
        self.img = img_path

        # @risk 删除属性, 节约持久化需要的内存
        del self.frame
        del self.result

        # delattr( self, 'frame' )



    # def save(self, out_path, name=None, postfix='jpg'):
    #     if not name:
    #         name = self.name
    #     img_path = f'{out_path}\\{name}.{postfix}'
    #     cv.imwrite(img_path, self.frame)
    #     self.img = img_path


    # def save(self):
    #     if not self.out_path:
    #         raise RuntimeError('请先调用 setOutPath() 方法!')
    #     cv.imwrite(f'{self.out_path}/{self.name}.jpg', self.frame)
    def getSimScore(self, pre_pf):
        """"
        两帧之间文本相似度计算
        """
        return TextSimilarity.getSimScoreV1(pre_pf.getAllTextStr(), self.getAllTextStr())

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

    def __init__(self):
        self.frame_list = []

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
        self.update(self._len()-1, pf)

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
        if self._len() == 0 or (i-1) >= self._len():
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
        @wait 应该保留图片清晰度较好的| 保留内容文字更多的 | 最后 内容还有 时间节点做更改
        双向相似度
        """
        frame_list = self.frame_list
        for i in range(len(frame_list)-1, -1, -1):
            cur = frame_list[i]
            nt_i = i-1
            if nt_i >= 0:
                nt = frame_list[nt_i]

                score = cur.getSimScoreV3(nt)
                cur_score = score['base_pre']
                nt_score = score['base_nt']
                max_score = max(cur_score, nt_score)
                if max_score > args.th_sim_score:
                    #删除, 并且删除信息少的那一个
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

class Video:
    """
    视频相关信息
    功能:
        1. 视频的总帧数
        2. 视频的帧率
        3. 根据帧号获取视频的播放时间, 单位: 毫秒
        4. 将该视频 转换为 图片
        5. 遍历功能, 设置一个插槽, 传入一个处理函数
    """

    def __init__(self, video_path, output_dir, video_id, chapter_id, name=""):
        """
        ::name 如果没有传入, 默认视频的名称为name默认值
        @wait 层级关系的设计后续还需要考虑
        """
        # if not video_path:
        #     raise FileExistsError('Please correct video path!')
        if not name:
            self.name = video_path.split('\\')[-1].split('.')[0]
        else:
            self.name = name
        self.output_dir = output_dir
        # self.kfs_out_put_dir = kfs_output_dir

        self.path = video_path
        # self.parent_id = chapter_id
        self.chapter_id = chapter_id
        self.id = video_id
        if chapter_id == -1:
            self.pre_id = video_id
        else:
            self.pre_id = f'{chapter_id}.{self.id}'
        self.kfs = KeyFrames()

        self.cap = cv.VideoCapture(video_path)
        self.fps = self.cap.get(cv.CAP_PROP_FPS)
        self.width = self.cap.get(cv.CAP_PROP_FRAME_WIDTH)
        self.height = self.cap.get(cv.CAP_PROP_FRAME_HEIGHT)
        self.frame_counts = self.cap.get(cv.CAP_PROP_FRAME_COUNT)

        if args.step == 'fps':
            self.step = self.fps * args.speed_x
        else:
            self.step = args.step * args.speed_x
        if self.fps > 0: # 有些垃圾的视频文件, 没有内容, 导致 除0的报错
            self.total_time_ms = self.frame_counts / self.fps * 1000
            self.old_frame = None
            self._run() #运行完成产出关键帧
            self.kfs.saveKfs() # 将关键帧保存为文件
            del self.old_frame
            # @risk 保存完成将 kfs: KeyFrame ->  kfs: list, 同时释放内存
        temp = self.kfs
        self.kfs = self.kfs.getList()
        del temp
        del self.cap

        # if run:
        #     self._run()

    def searchByKey(self, key, json_dumps=False):
        kfs = []
        for pf in self.kfs:
            pfvo = pf.searchByKey( key )
            # if args.search_result_dict_mode:
            #     if pfvo['boxes']:
            #         kfs.append( pfvo )
            # else:
            if not pfvo.isEmpty():
                kfs.append(pfvo)

        result =  vo.Video( self.id, kfs, self.name, self.chapter_id )
        return utils.json_dumps(result) if json_dumps else result

    def getTimeMsByFrameID(self, frame_id):
        """
        帧编号 转换为 该视频播放位置的 毫秒数
        @return millisecond
        """
        return frame_id/self.fps * 1000

    def _iter_func(self, pf):
        print( '------------------------------' )
        print( f'有效帧数: {len( self.kfs )}' )
        # cv.imshow('v1', pf.frame)
        # cv.waitKey(1)
        # 增加模糊度, 对比度判断
        # contrast_score = contrastScore(pf.frame)

        print( f'{pf.name} / {self.frame_counts} \navg_score : {pf.avg_score} \nblur_score: {pf.blur_score}'
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

        origin_pf = cp.deepcopy( pf )
        if self.old_frame == None:
            self.old_frame = pf
            self.kfs.add( pf )
        else:
            ret, sim_score1 = pf.getSimScoreV4( self.old_frame )
            sim_score = 0

            # 两步计算相似度, 解决状况:  PPT内容展示有动画, 例如: 内容: a -> 过渡动画 -> ab, 其实还是同一页, 但是如果只计算sim(old, cur), a变模糊, 再到没有a->插入列表->再出现ab
            if len( self.kfs ) > 0:
                tail_frame = self.kfs.getTail()
                ret, sim_score2 = pf.getSimScoreV4( tail_frame )
                # 如果分数高的是末尾
                sim_score = max( sim_score1, sim_score2 )
            else:
                sim_score = sim_score1
            # 还需要修复 关键点1 -> full, 再来一次 1-> full, 会导致重复的发生
            # @performance 去重的操作如果影响性能, 可以提供用户点击去重效果
            print( f'sim_score: {sim_score}' )
            # @wait 逆向相似度 > 正向相似度, 说明在减少内容, 是动画
            # 内容增加判断
            if sim_score > args.th_sim_score:  # 判断是否相似
                # 增加内容的比较, 也要和 tail末尾的比较, 不过得相似的前提下
                if pf.getBoxesLen() > self.old_frame.getBoxesLen():  # 判断内容是否增加
                    pf.ms = self.old_frame.ms
                    pf.name = pf.name + f"#{self.old_frame.id}"
                    if len( self.kfs ) > 0:
                        self.kfs.updateTail( pf )
                    else:
                        self.kfs.add( pf )
                    # self.old_frame = origin_pf
                elif pf.getBoxesLen() < self.old_frame.getBoxesLen():
                    self.old_frame = origin_pf
                    pass

                else:  # 图片内容相同, 且内容没有增加了,
                    if len( self.kfs ) > 0:
                        tail_frame = self.kfs.getTail()
                        if pf.blur_score > tail_frame.blur_score:  # 保留图片清晰图更好的图像
                            tail_frame.blur_score = pf.blur_score
                            tail_frame.frame = pf.frame
                            self.kfs.updateTail( tail_frame )
                        # self.old_frame = origin_pf
            else:
                self.kfs.add( pf )

            # 指定一系列过滤条件
            # 如果 分数大于 0.95, 不保留,
            # 如果没有内容 也不保留
            self.old_frame = origin_pf
        print( '------------------------------' )

    def _run(self):
        while True:
            ret, frame = self.cap.read()
            if ret:
                frame_id = int(self.cap.get(cv.CAP_PROP_POS_FRAMES)) - 1
                frame_ms = self.cap.get(cv.CAP_PROP_POS_MSEC)
                self._iter_func( PaddleFrame( frame_id, frame, frame_ms, self.output_dir, video_id=self.id ) )
                # print(f'frame_id: {frame_id}, frame_ms: {frame_ms} ')
                self.cap.set(cv.CAP_PROP_POS_FRAMES,
                             frame_id + self.step)

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

class Chapter():

    def __init__(self, id, name, course_id, videos: list ) -> None:
        self.id = id
        self.name = name
        self.course_id = course_id
        self.videos = videos #@wait 如何保证视频的有序性， 这样才能够保证搜索结果的有序性，（可以根据id排序，实现一次规整化处理）

    def __getitem__(self, index):
        return self.videos[index]


    def searchByKey(self, key, json_dumps = False):
        """
        :param key:
        :return: r[小节号][帧]
        @wait 章节搜索内容的返回格式,   1: 不加区分, 直接list  2. dict格式: { chapter1: [内容] }
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
        result =  vo.Chapter(self.id, videos, self.name, self.course_id)
        return utils.json_dumps(result) if json_dumps else result

class Course():
    """"
    更好的方案： 直接传入入境， 自顶向下的一起喝成， 而不是自定向下的创建， 所以闯入了不应该是章节， 而是文件的路径
    那么文件路径的结构需要什么样的呢

    是否需要路径对象， 负责管理视频的路径呢：
    当然： 根路径也需要有结构的存放视频，    然后视频的格式， 路径管理器进行自动解析


    """

    def __init__(self, id, name, chapters: list = []) -> None:
        self.id = id
        self.name = name
        self.chapters = chapters

    def __getitem__(self, index):
        return self.chapters[index]

    def searchByKey(self, key, json_dumps=False):
        chapters = []
        for c in self.chapters:
            chapter_vo = c.searchByKey(key)
            # if args.search_result_dict_mode:
            #     if chapter_vo['videos']:
            #         chapters.append( chapter_vo )
            # else:
            if not chapter_vo.isEmpty():
                chapters.append(chapter_vo)
        result =  vo.Course(self.id, chapters, self.name)
        return utils.json_dumps(result) if json_dumps else result



import shutil
import filetype
class Assember():
    """
    负责将用户指定的路径（课程，章节， 小节）： 装配出不同的对象（Course， Chapter， Video）
    """
    @staticmethod
    def executeCourse(course_root_path, course_id, output_dir=RootPath.output_courses_dir , name="") -> Course:
        chapter_dirs = glob.glob(f'{course_root_path}\\*')
        #过滤非目录文件
        chapter_dirs = Assember.__filter_no_dir(chapter_dirs)
        name = name or course_root_path.split('\\')[-1]
        # 初始化 输出目录
        output_dir = output_dir + "\\" + name
        Assember._setDir( output_dir )

        chapters = [Assember.executeChapter(
            chapter_path=dir_path, output_dir=output_dir, chapter_id=i + 1,
            chapter_name=dir_path.split('\\')[-1] , course_id=course_id )
            for i, dir_path in enumerate( chapter_dirs )]
        return Course(id = course_id, name=name, chapters=chapters)

    @staticmethod
    def executeChapter(chapter_path, output_dir=RootPath.output_chapters_dir, chapter_id="", chapter_name="", course_id="") -> Chapter:
        # 获取章节目录下的所有视频的路径
        # @risk 视频类型的过滤器可能有隐藏的bug
        video_paths = glob.glob(f'{chapter_path}\\*')
        video_paths = Assember.__filter_no_video_file( video_paths )
        chapter_name = chapter_name or chapter_path.split('\\')[-1]
        output_dir = output_dir + "\\" + chapter_name
        Assember._setDir( output_dir )
        videos = [Assember.executeVideo(
            video_path=v_path, output_dir=output_dir, video_id=i + 1,chapter_id=chapter_id )
            for i, v_path in enumerate( video_paths )]
        return Chapter( id=chapter_id, name=chapter_name, course_id= course_id, videos = videos )


    @staticmethod
    def executeVideo(video_path, output_dir=RootPath.output_videos_dir, video_id="", chapter_id="", name="") -> Video:
        print(f'output_dir: {output_dir}')
        output_dir = output_dir + (name or ("\\" + video_path.split('\\')[-1].split('.')[0]))
        Assember._setDir( output_dir )
        return Video( video_path=video_path, output_dir=output_dir, video_id= video_id,
                      chapter_id=chapter_id, name=name )

    @staticmethod
    def __filter_no_dir(paths):
        return list(filter(lambda p: os.path.isdir(p), paths))

    @staticmethod
    def __filter_no_video_file(paths):
        return list(filter(lambda p: os.path.isfile(p) and filetype.is_video(p), paths))

    @staticmethod
    def _setDir(dir_path):
        """
        如果目录不存在, 就创建目录; 存在就清空目录下的文件
        :param dir_path:
        :return:
        """
        if not os.path.exists( dir_path ):
            os.makedirs(dir_path, mode=0o777, exist_ok=True)
            # os.mkdir( dir_path )
        else:
            shutil.rmtree(dir_path)
            os.mkdir( dir_path )
            # os.mkdir(dir_path)
            # del_list = glob.glob( f'{dir_path}\\*' )
            # for d_path in del_list:
            #     if os.path.isfile(d_path):
            #         os.remove( d_path )
            #     else:
            #         os.rmdir(d_path)

# class ResultBO:
#     """
#     PaddleFrame搜索结果对象
#     """
#
#     def __init__(self, frame_id, box, txt, frame) -> None:
#         self.frame_id = frame_id
#         self.box = box
#         self.txt = txt



