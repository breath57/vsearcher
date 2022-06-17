


python -m twine upload --repository testpypi dist/*

python -m build

pip install -i https://test.pypi.org/simple/ vsearcher=={version}



python -m twine upload  dist/*

python -m build

pip install -i https://test.pypi.org/simple/ vsearcher=={version}


pipreqs ./ --encoding=utf8 # generate project dependencies