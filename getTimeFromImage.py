import cv2
import math
import os
from compare import compare_images

img = cv2.imread('images/full.png')  # resize to 1920x1080?
min1 = cv2.resize(img[53:53+52, 1273:1273+52], (32, 32))
min2 = cv2.resize(img[53:53+52, 1273+44:1273+52+44], (32, 32))
sec1 = cv2.resize(img[53:53+52, 1382:1382+52], (32, 32))
sec2 = cv2.resize(img[53:53+52, 1382+44:1382+52+44], (32, 32))
ms1 = cv2.resize(img[53:53+52, 1490:1490+52], (32, 32))
ms2 = cv2.resize(img[53:53+52, 1490+44:1490+52+44], (32, 32))
ms3 = cv2.resize(img[53:53+52, 1490+44+44:1490+52+44+44], (32, 32))

p2_min1 = cv2.resize(img[976:976+52, 1273:1273+52], (32, 32))
p2_min2 = cv2.resize(img[976:976+52, 1273+44:1273+52+44], (32, 32))
p2_sec1 = cv2.resize(img[976:976+52, 1382:1382+52], (32, 32))
p2_sec2 = cv2.resize(img[976:976+52, 1382+44:1382+52+44], (32, 32))
p2_ms1 = cv2.resize(img[976:976+52, 1490:1490+52], (32, 32))
p2_ms2 = cv2.resize(img[976:976+52, 1490+44:1490+52+44], (32, 32))
p2_ms3 = cv2.resize(img[976:976+52, 1490+44+44:1490+52+44+44], (32, 32))

times = []
for digit in [min1, min2, sec1, sec2, ms1, ms2, ms3, p2_min1, p2_min2, p2_sec1, p2_sec2, p2_ms1, p2_ms2, p2_ms3]:
    digit = cv2.threshold(
        cv2.cvtColor(digit, cv2.COLOR_BGR2GRAY), 130, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)[1]
    closestMse = math.inf
    closestSsim = 0
    closestNum = ''

    directory = 'images/numbers'
    for filename in os.listdir(directory):
        f = os.path.join(directory, filename)
        number = cv2.imread(f)
        number = cv2.cvtColor(number, cv2.COLOR_BGR2GRAY)
        # cv2.imshow("Image", number)
        # cv2.waitKey(0)
        (m, s) = compare_images(digit, number)
        # print(f)
        # print((m, s))
        if m < closestMse:
            closestMse = m
        if s > closestSsim:
            closestSsim = s
            closestNum = filename

    times.append(closestNum[-5:-4])
    # print(closestNum)
    # print(closestMse)
    # print(closestSsim)
print(times)
