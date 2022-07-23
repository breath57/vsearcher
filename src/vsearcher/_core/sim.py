# -*- encoding: utf-8 -*-
'''
@description: Algorithms related to similarity 
@author: breath57
@email: breath57@163.com
'''
import warnings
from collections import Counter

# from functools import cached_property
import jieba
import numpy as np

from .._config import args

#  字符串还是文本列表, 或者OCR已经算分词了吗
# 该版本 输入: 为list  或者 str都可以

# f_path = f'{path.RootPath.step_word_path}\\{args.stop_word_file}'
# result = pd.read_csv(f_path, sep='\n\r', names=['word'], encoding='gbk')
# stop_word_set = set(result['word'].values)
stop_word_set = args.stop_word_set


class TextSimilarity(object):

    @staticmethod
    def getSimScoreByCosine(list_or_str_1, list_or_str_2):
        # if len(list_or_str_1) == 0 or len(list_or_str_2):
        #     return 0.0
        input_type, input_type2 = type(list_or_str_1), type(list_or_str_2)
        word_list_1, word_list_2 = [], []
        if input_type is not input_type2:
            raise TypeError('Please confirm type of inputs are equal!')
        if input_type == str:
            word_list_1, word_list_2 = TextSimilarity.__lcut_str(
                list_or_str_1, list_or_str_2)
        elif input_type == list or input_type == np.ndarray:
            '''
                @author breath
                @note: 具体使用哪种方式性能好, 效果好, 还需要后续验证, 暂定方式二
            '''
            # 方式一: 归并为一个长字符串, 并以此为拆分单位
            # str1, str2 = TextSimilarity.__array2str(
            #     list_or_str_1), TextSimilarity.__array2str(list_or_str_2)
            # word_list_1, word_list_2 = TextSimilarity.__lcut_str(str1, str2)
            # 方式二: 数组中的多个字符为拆分单位
            word_list_1, word_list_2 = TextSimilarity.__lcut_arr(
                list_or_str_1, list_or_str_2)
        else:
            raise TypeError(
                'Please confirm type of inputs are ndarray, list or str!')

        # print(f'word_list_1: {word_list_1},\n word_list_2: {word_list_2}')
        return TextSimilarity.__cos_sim(word_list_1, word_list_2)

    @staticmethod
    def __array2str(_array):
        _str = ""
        for s in _array:
            _str += s
        return _str

    @staticmethod
    def __lcut_str(str1, str2):
        word_list_1 = jieba.lcut(str1)
        word_list_2 = jieba.lcut(str2)
        return word_list_1, word_list_2

    @staticmethod
    def __lcut_arr(list1, list2):
        word_list_1 = []
        for text in list1:
            word_list_1 += jieba.lcut(text)
        word_list_2 = []
        for text in list2:
            word_list_2 += jieba.lcut(text)
        return word_list_1, word_list_2

    @staticmethod
    def __cos_sim(word_list_1, word_list_2):        # word_list_1 是分词后的标签列表
        co_str1 = (Counter(word_list_1))
        co_str2 = (Counter(word_list_2))
        p_str1 = []
        p_str2 = []
        for temp in set(word_list_1 + word_list_2):
            p_str1.append(co_str1[temp])
            p_str2.append(co_str2[temp])
        p_str1 = np.array(p_str1)
        p_str2 = np.array(p_str2)
        return p_str1.dot(p_str2) / (np.sqrt(p_str1.dot(p_str1)) * np.sqrt(p_str2.dot(p_str2)))

    @staticmethod
    def getSimScoreV1(str_pre, str_next):
        """计算前一个字符集合, 在后一个字符集合出现的比重

        返回值 0~1, 1代表str_pre是str_next字符的重复率很高
        """
        sp, sn = set(str_pre), set(str_next)
        IN = sp & sn
        return 0 if len(IN) == 0 else len(IN)/len(sp)

    @staticmethod
    def getSimScoreV2(str_pre: str, str_next: str):
        """ 计算前一个字符集合, 在后一个字符集合出现的比重

            返回值 0~1, 1代表str_pre是str_next字符的重复率很高
        """
        return max(TextSimilarity.getSimScoreByCosine(str_pre, str_next),
                   TextSimilarity.getSimScoreV1(str_pre, str_next))

    @staticmethod
    def getSimScoreV3(str_pre, str_next, filter_stop_word=False) -> dict:
        """ 双向相似度

        计算前一个字符集合, 在后一个字符集合出现的比重

        返回值 0~1, 1代表str_pre是str_next字符的重复率很高
        @return {
            'base_pre': base_pre_sim,
            'base_nt': base_nt_sim
        }
        """
        sp, sn = set(str_pre), set(str_next)
        if filter_stop_word:
            sp, sn = sp - stop_word_set, sn - stop_word_set
        IN = sp & sn
        base_pre_sim, base_nt_sim = 0, 0
        if len(IN) != 0:
            base_pre_sim = len(IN)/len(sp)
            base_nt_sim = len(IN)/len(sn)
        return {
            'base_pre': base_pre_sim,
            'base_nt': base_nt_sim
        }

    @staticmethod
    def _getSimScoreV4(str_pre, str_next, filter_stop_word=True) -> dict:
        """

        @return ret, sim
        返回双向相似度最大值, 并返回 两个方向相似度的大小关系
        越大内容越少
        0: 相同 |  1：(后面内容多)前比后大 | -1： （前面内容多）后比前大
        """
        score = TextSimilarity.getSimScoreV3(
            str_pre, str_next, filter_stop_word=filter_stop_word)
        base_pre = score['base_pre']
        base_nt = score['base_nt']
        sim = max(base_pre, base_nt)
        ret = 0
        if base_nt == base_pre:
            if base_nt == 1:
                ret = 0
            else:  # 应对 0.88 == 0.88 == 0.88 奇葩情况
                ret = -1 if len(str_pre) > len(str_next) else 1
        elif base_pre > base_nt:
            ret = 1
        else:
            ret = -1
        return ret, sim

    @staticmethod
    def getSimScore(str_pre: str, str_next: str) -> tuple:
        """ 选择使用的算法 """
        return TextSimilarity._getSimScoreV4(str_pre, str_next)

    @staticmethod
    def box_sim(pre_boxes, next_boxes):
        """ 待定(结构相似度，也就是框框的相似度) """
        warnings.warn("box sim don't use!", DeprecationWarning)
