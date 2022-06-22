


# 上传到测试的pypi
python -m twine upload --repository testpypi dist/*

# 构建pypi的dist文件
python -m build

# 安装命令
pip install -i https://test.pypi.org/simple/ vsearcher=={version}


# 构建pypi的dist文件
python -m build

# 上传到正式的pypi
python -m twine upload  dist/*

pip install -i https://test.pypi.org/simple/ vsearcher=={version}

# 生成项目的依赖库
pipreqs ./ --encoding=utf8 # generate project dependencies