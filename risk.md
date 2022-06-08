
1. 不能删除某个章节下的视频，不能同步，因为搜索使用的是最高层的pickle对象。
场景：删除Course 1 -> Chapter 1 -> Video 1

思路1：
    1. 删除数据库中的 Video 1 对象
    2. 更新Course和Chapter下的Pickle文件，怎么更新又是需要修改VSearch库（不推荐）

思路2（推荐）：
    1. 更改搜索方法，只生成VideoPickle，无需Chapter Pickle（优点：节约存储空间，更灵活）
    2. 通过数据库查找该资源下的所有视频，按级查找（缺点：搜索速度慢）
    3. 就可以废弃VSearch中的Course和Chapter的搜索方法

2. opencv读取视频（好像有）阻塞问题
解决思路：降低cap同时开启的数量，设置阈值