from vsearcher import VSearcher


def case1_base_use():
    """ 对视频进行检索，并获取视频对应的课件 """
    from pprint import pprint
    video_path = './test.mp4'  # 视频文件路径
    executed_video = VSearcher.executeVideo(
        video_file_path=video_path, speed_x=20)  # 对视频进行处理, 并返回处理结果
    search_key = "学习"  # 搜索关键词
    search_result = executed_video.search(key=search_key)  # 返回搜索结果
    print('=================courseware_path================')
    pprint(executed_video.cw_local)  # 获取课件路径
    print('=================executed_video================')
    pprint(executed_video.json().encode('utf-8').decode('unicode-escape'))
    print('=================search_results================')
    pprint(search_result.json().encode('utf-8').decode('unicode-escape'))
    print('=================release================')
    # executed_video.release()  # 资源释放


if __name__ == '__main__':
    case1_base_use()
