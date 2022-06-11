"""
vsearcher
------------------
"""
import setuptools

with open( "README.md", "r", encoding="utf-8" ) as fh:
    long_description = fh.read()

setuptools.setup(
    name="vsearcher",
    version="0.2.6",
    author="breath",
    author_email="1498408920@qq.com",
    maintainer="breath",
    description="支持视频内容检索和课件自动生成的库",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://gitee.com/breath57/vsearch/tree/0.2.6-pypi",
    keywords=["video", "search", "courseware", "ocr"],
    project_urls={
        # "Bug Tracker": "bug连接",
    },
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    package_dir={"": "src"},
    packages=setuptools.find_packages(where="src"),
    python_requires=">=3.9",
    install_requires=[
        "filetype>=1.0.13",
        "img2pdf>=0.4.4",
        "jieba>=0.42.1",
        "numpy>=1.22.4",
        "opencv_python>=4.5.5.64",
        "paddleocr>=2.5",
        "pandas>=1.4.2",
        "Pillow>=9.1.1",
        "setuptools>=62.3.1",
    ]

)

