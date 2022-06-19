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

### 快速使用:
1. 安装

> 步骤 1 安装Paddle框架
选择CPU或GPU其一安装即可

**cpu版:**
```
python3 -m pip install paddlepaddle==2.3.0 -i https://mirror.baidu.com/pypi/simple
```
**GPU版** (通常需要安装CUDA等显卡适配软件)

不同环境的安装方式不同, [点击查看详情](https://www.paddlepaddle.org.cn/)

> 步骤 2
```
pip install -i https://test.pypi.org/simple/ vsearcher=={version}
```
2. 使用案例
```py
from vsearcher import VSearcher

def test():
    VSearcher.init(static_folder="app/static", output_dir='vs-output') # 设置输出文件夹
    video_path = "./test.mp4" # 视频文件路径：请填入真实的文件可访问视频路径
    video = VSearcher.executeVideo(video_file_path=video_path) # 处理视频 生成 注释文件
    courseware = video.cw # 获取生成的课件的路径
    result = VSearcher.search(video, '关键字') # 视频检索
    VSearcher.releaseByOutputDir(video.output_dir) # 清空处理期间产生的文件
    print(f'courseware: {courseware}')
    print(f'search_result: {dict(result)}')

if __name__ == '__main__':
    test()
```

3. 问题

> 3.1 在linux环境下可能出现cv2相关的异常问题

解决方案 1： 安装如下包
```
pip install opencv-contrib-python
pip install opencv-python-headless
pip install openpyxl
```

若执行方案1之后还有报错，则执行如下命令即可
```
pip uninstall opencv-contrib-python
pip uninstall opencv-python-headless
pip uninstall openpyxl

pip install opencv-contrib-python
pip install opencv-python-headless
pip install openpyxl
```


> 3.2 出现如下异常信息
```
_message.Message._CheckCalledFromGeneratedFile()
TypeError: Descriptors cannot not be created directly.
If this call came from a _pb2.py file, your generated code is out of date and must be regenerated with protoc >= 3.19.0.
If you cannot immediately regenerate your protos, some other possible workarounds are:
 1. Downgrade the protobuf package to 3.20.x or lower.
 2. Set PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python (but this will use pure-Python parsing and will be much slower).
```
解决
```
pip3 install protobuf==3.20
```