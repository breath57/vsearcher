

import cv2 as cv
from ..core.video import PaddleFrame
import sys
sys.path.append('../')
# 你么


img1 = 'F:\Document\VSCode\Projects\\flask-test\static\\vsearch-output\\test6\\2#2575-2500.png'
img2 = 'F:\Document\VSCode\Projects\\flask-test\static\\vsearch-output\\test6\\2#2625-2600.png'

frame1 = cv.imread(img1)
frame2 = cv.imread(img2)
pf1 = PaddleFrame(2, frame1, 0, '', 2)
pf2 = PaddleFrame(2, frame2, 0, '', 2)
