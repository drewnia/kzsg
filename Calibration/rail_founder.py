import cv2
import numpy as np
import set_areas
import os, sys
sys.path.append("../")
from kzsg_utils import *

###Для отладки
SAVE_CANNY_IMG = True # сохранить изображение Canny
SHOW_HOUGH_LINES = False #Показать окно с линиями Хафа
CROPED = False #Если фотки были обрезаны от первоначального размера
SELECT_LINES_OF_RAILS = True # для сохранения областей по каждому пути
###


###Основные параметры, которые критичны для алгоритма



# для параллельных линий - 11 и 101, для остальных 21 и 21
blur_w = 21 #чем больше рельсы ПАРАЛЛЕЛЬНЫ вертикали/горизонтали, тем МЕНЬШЕ значение
blur_h = 21 #чем больше рельсы ПАРАЛЛЕЛЬНЫ вертикали/горизонтали, тем больше значение

sleeper_length = 50 # примерное расстояние между рельсами в пикселях (длина шпалы) в нижней части изображения
num_of_sector = 8
## Стандартно определяются через номер сектора
# HORIZONTAL_RAILS = False # направление рельсов горизонатольное или вертикальное
# UP_TO_DOWN = False #Направление рельсов сверху внизу (или справа налево)
# HORIZONTAL_RAILS, UP_TO_DOWN = check_sector_num(num_of_sector)
##

path = "/home/andrey/work/Projects/VideoKZP/svn/kzsg/imgs/free_ways/day/"
###


path_to_file = path + "day_" + str(num_of_sector)
if CROPED:
    path_to_file += "_croped"

path_to_file += ".jpg"

orig_img = cv2.imread(path_to_file)
orig_img = rotate_img(orig_img, num_of_sector)


img = orig_img.copy()
w = img.shape[1]
h = img.shape[0]

gray = cv2.cvtColor(img,cv2.COLOR_BGR2GRAY)
gray = cv2.GaussianBlur(gray, (blur_w, blur_h), 0)
if True: ## use only canny
    edges = cv2.Canny(gray,10,50)
else:
    gray = cv2.medianBlur(gray, 21)
    adapt_type = cv2.ADAPTIVE_THRESH_GAUSSIAN_C
    thresh_type = cv2.THRESH_BINARY_INV
    edges = cv2.adaptiveThreshold(gray, 255, adapt_type, thresh_type, 21, 2)


if SAVE_CANNY_IMG:
    path_to_canny = os.path.splitext(path_to_file)[0] + "_canny.jpg"
    cv2.imwrite(path_to_canny, edges)


lines = cv2.HoughLines(edges,1,np.pi/180,200)

###выделим координаты и найдем максимальную длину линии
real_lines = []
max_dist = 0
for i in range(0, len(lines)):
    for rho1, theta1 in lines[i]:
        real_lines.append(get_line(rho1, theta1, w, h))
        x1, y1, x2, y2 = real_lines[-1]
        if max_dist < euclid_dist(x1,y1,x2,y2):
            max_dist = euclid_dist(x1,y1,x2,y2)
###
###расположим элементы слева направо
for i in range(0, len(lines)):
    for j in range(len(lines)-1, i, -1):
        x1, y1, x2, y2 = real_lines[i]
        x3, y3, x4, y4 = real_lines[j]
        # выделим нижние абсциссы линий (где рельсы пошире)
        if y1 > y2:
            minx1 = x1
        else:
            minx1 = x2
        if y3 > y4:
            minx2 = x3
        else:
            minx2 = x4
        if minx1 > minx2:
            real_lines_j = real_lines[j]
            real_lines[j] = real_lines[i]
            real_lines[i] = real_lines_j
###
###удалим мнимые линии в начале
while True:
    x1, y1, x2, y2 = real_lines[0]
    if [x1, y1, x2, y2] == [0,0,0,0]:
        real_lines = np.delete(real_lines, 0, axis=0)
    else:
        break
###
###удалим лишние отрезки
for i in range(0, len(real_lines)):
    for j in range(len(real_lines)-1, i, -1):
        x1, y1, x2, y2 = real_lines[i]
        x3, y3, x4, y4 = real_lines[j]
        #выделим нижние абсциссы линий (где рельсы пошире)
        if y1 > y2:
            minx1 = x1
        else:
            minx1 = x2
        if y3 > y4:
            minx2 = x3
        else:
            minx2 = x4
        x,y = get_intersection(x1,x2,x3,x4,y1,y2,y3,y4)
#если отрезки пересекаются или расположены близко друг к другу (или мнимые), то удаляем
        if (0 <= x <= w and 0 <= y <= h) or \
                (abs(minx1 - minx2) < sleeper_length) or \
                [x3, y3, x4, y4] == [0,0,0,0]:

            real_lines = np.delete(real_lines, j, axis=0)
###

#удалим короткие линии
for i in range(len(real_lines)-1, -1, -1):
    x1, y1, x2, y2 = real_lines[i]
    dist = euclid_dist(x1,y1,x2,y2)
    if dist < 3*max_dist / 4:
        real_lines = np.delete(real_lines, i, axis = 0)


###нарисуем линии
for line in real_lines:
    x1, y1, x2, y2 = line
    cv2.line(img,(x1,y1),(x2,y2),(0,0,255),2)
    if SHOW_HOUGH_LINES:
        cv2.imshow("img",img)
        cv2.waitKey()
###

###warping - изменение перспективы (приведение к 2D виду)

x_down_left, y_down_left, x_up_left, y_up_left = real_lines[0]
x_down_right, y_down_right, x_up_right, y_up_right = real_lines[-1]
###


###сдвинем левый край на длину шпалы
if x_down_left < sleeper_length:
    addition_left = x_down_left
elif x_up_left < sleeper_length:
    addition_left = x_up_left
else:
    addition_left = sleeper_length
x_down_left -= addition_left
x_up_left -= addition_left
###

###сдвинем правый край на длину шпалы
if x_down_right + sleeper_length > w:
    addition_right = w - x_down_right
elif x_up_right + sleeper_length > w:
    addition_right = w - x_up_right
else:
    addition_right = sleeper_length
x_down_right += addition_right
x_up_right += addition_right
###



for x in [x_down_left, x_up_left]:
    x -= sleeper_length
    x = max(0, x)

for x in [x_down_right, x_up_right]:
    x += sleeper_length
    x = min(w, x)

pts1 = np.float32([[x_down_left, y_down_left], [x_up_left, y_up_left], [x_up_right, y_up_right], [x_down_right, y_down_right]])
pts2 = np.float32([[0, h], [0, 0], [w, 0], [w, h]])

M = cv2.getPerspectiveTransform(pts1, pts2)

warped = cv2.warpPerspective(orig_img, M, (w, h))

#нарисуем и сохраним области для каждого пути
if (SELECT_LINES_OF_RAILS):
    set_areas.Drawer().run(num_of_sector=num_of_sector, image=warped)



###


path_to_hough = os.path.splitext(path_to_file)[0] + "_hough.jpg"
path_to_warped = os.path.splitext(path_to_file)[0] + "_warped.jpg"


cv2.imwrite(path_to_hough,img)
cv2.imwrite(path_to_warped,warped)

warping_points_file = "warping_coefs_"+str(num_of_sector)
np.savetxt(warping_points_file, pts1, delimiter=',')