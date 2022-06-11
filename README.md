## 介绍
----

### 主要功能:
1. 视频内容搜索
2. 课件生成


### 其它能力:
1. 生成可序列化的信息: 包括帧的标题,文本内容,播放位置
2. 框选搜索结果
3. 多配置

支持的视频类型: 中文为主, 以PPT作为主体讲授的视频

### 鲁棒性:
* 动画切换
* 内容递增
* 中英文内容
* 人像的讲解
* 无重复

### 使用:
1. 安装 
```
pip install -i https://test.pypi.org/simple/ vsearcher=={version}
```

2. 使用案例
```py
from vsearcher import VSearcher

def test():
    VSearcher.init(static_folder="app/static", output_dir='vs-output') # 设置输出文件夹
    video_path = "./test.mp4" # 视频文件路径
    video = VSearcher.executeVideo(video_file_path=video_path) # 处理视频 生成 注释文件
    courseware = video.cw # 获取生成的课件的路径
    result = VSearcher.search(video, '关键字') # 视频检索
    VSearcher.releaseByOutputDir(video.output_dir) # 清空处理期间产生的文件
    print(f'courseware: {courseware}')
    print(f'search_result: {dict(result)}')

if __name__ == '__main__':
    test()
```
