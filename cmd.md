


python -m twine upload --repository testpypi dist/*

python -m build

pip install -i https://test.pypi.org/simple/ vsearcher=={version}
