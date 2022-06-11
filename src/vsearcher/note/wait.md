# 已经做了内存优化, 支持大视频 # 对的
# 该功能还没有引入
th_min_boxsize = 2 # 设置最小文本框的大小， 可以过滤掉代码， 可以提升解析速度

# 分词功能做一些考虑，当他是英文的时候， 可以判别是否是单词
# 先测试一张含有代码的图片
# 搜索结果的图片，需要 画出关键字位置



# 图片路径含有中文， 并且内容含有空格 -> 去空格

# test-course 循环


# 如果搜索关键词相同， 返回优化过程

# 全局统一路径为 \\  -> /

# 目录 切分， 分治 多线程, 异步处理
```py
from threading import Thread
from time import sleep
tasks = []
win_size = 5
while True:
    completed_count = 0

    for i in range(win_size):
        Thread.run()
    
    while True:
        if completed_count == win_size:
            break
        else:
            sleep(100)
```

队列

文件服务器

每个文件夹下： 保存一个视频

专门写一个 文件管理系统

数据库

多进程 | 英文PPT的针对


其实一两秒就跳过的PPT， 说明不重要， 所以可以不需要

加载模式， 先大范围跳跃PPT， 有课件帧加入之后，再减缓搜索的速度

# 视频的拷贝 属于懒加载, 确实如此 边播放, 边加载

@RISK 多进程还没有进行测试
@RISK　课程的内容的提取还没有测试

@RISK 不支持不线程版本的课件BUG还没有修复

flask 版本的测试