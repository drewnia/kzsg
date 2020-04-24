from os import mkdir,listdir
from os.path import exists,isfile, join, isdir
from shutil import rmtree
import numpy as np
import cv2

sleeper_length = 50  # примерное расстояние между рельсами в пикселях (длина шпалы) в нижней части изображения
min_car_length = 7  # минимальная длина вагона с учетом погрешности расстояний

def getListOfFiles(dirName):
    # create a list of file and sub directories
    # names in the given directory
    listOfFile = listdir(dirName)
    allFiles = list()
    # Iterate over all the entries
    for entry in listOfFile:
        # Create full path
        fullPath = join(dirName, entry)
        # If entry is a directory then get the list of files in this directory
        if isdir(fullPath):
            allFiles = allFiles + getListOfFiles(fullPath)
        else:
            allFiles.append(fullPath)

    return allFiles


def get_jpg_filenames(path, recursively: bool = False, find_png: bool = False):

    if find_png:
        extension = "png"
    else:
        extension = "jpg"

    if recursively:
        return [f for f in getListOfFiles(path) if isfile(f) and f.split(".")[-1] == extension]
    else:
        return [join(path, f) for f in listdir(path) if isfile(join(path, f)) and f.split(".")[-1] == extension]


def get_folders_traindata(path):
    return [join(path, f) for f in listdir(path) if isdir(join(path, f)) and f.split("(")[0].split("_")[0] == "traindata"]


def check_sector_num(sector_num: int):
    hr, ud = False, False#horizontal rails, up_to_down
    if int(sector_num) not in (2, 4, 5, 7, 8, 9, 10, 11, 12):#Если не вертикальный сектор
        hr = True
    if int(sector_num) in [3]:#Если рельсы направлены сверху вниз
        ud = True
    return hr, ud


def rotate_img(img, sector_num: int):
    hr,ud = check_sector_num(sector_num)
    if hr:
        img = cv2.rotate(img, cv2.ROTATE_90_COUNTERCLOCKWISE)
    if ud:
        img = cv2.rotate(img, cv2.ROTATE_180)
    return img



def euclid_dist(x1,y1,x2,y2):
    return np.sqrt(np.power((x1 - x2), 2) + np.power((y1 - y2), 2))

def rm_mk_dirs(dirs):
    max_trials = 5
    for path in dirs:
        for i in range(0,max_trials):
            try:
                if exists(path):
                    rmtree(path)
                mkdir(path)
                break
            except Exception as e:
                if i == max_trials-1:
                    raise e
                pass


def get_line(rho,theta,w,h):
    max_add=50 #чтобы отрезки приравнять к линиям
    a = np.cos(theta)
    b = np.sin(theta)
    x0 = a * rho
    y0 = b * rho
    x1 = int(x0 + max_add * (-b))
    y1 = int(y0 + max_add * (a))
    x2 = int(x0 - max_add * (-b))
    y2 = int(y0 - max_add * (a))

#найдем пересечения с краем кадра (пересечения с двумя из четырех краев)
    x_up, y_up = get_intersection(x1,x2,0,w,y1,y2,0,0)
    x_right, y_right = get_intersection(x1, x2, w, w, y1, y2, 0,h)
    x_down, y_down = get_intersection(x1, x2, 0,w, y1, y2, h, h)
    x_left, y_left = get_intersection(x1, x2, 0, 0, y1, y2, 0,h)
    x_chosen = []
    y_chosen = []
    for x, y in [x_down,y_down],[x_right,y_right],[x_left,y_left],[x_up,y_up]:
        if 0 <= x <= w and 0 <= y <= h:
            x_chosen.append(x)
            y_chosen.append(y)
    try:
        return int(x_chosen[0]), int(y_chosen[0]), int(x_chosen[1]), int(y_chosen[1])
        # return 0,0,0,0
    except:
        return 0,0,0,0





#вычисление точки пересечения отрезков [x1 y1]:[x2 y2] и [x3 y3]:[x4 y4]
def get_intersection(x1 : int,x2 : int,x3 : int,x4 : int,y1 : int,y2 : int,y3 : int,y4 : int):
    x1 = int(x1)
    x2 = int(x2)
    x3 = int(x3)
    x4 = int(x4)
    y1 = int(y1)
    y2 = int(y2)
    y3 = int(y3)
    y4 = int(y4)
    try:
        u = ((x4 - x3) * (y1 - y3) - (y4 - y3) * (x1 - x3)) / ((y4 - y3) * (x2 - x1) - (x4 - x3) * (y2 - y1))
        x = x1 + u * (x2 - x1)
        y = y1 + u * (y2 - y1)
    except ZeroDivisionError:
        x = -1
        y = -1
    return x, y


def from_real_to_warped(x,y, M):
    pts = np.array([[x, y]], dtype="float32")
    pts = np.array([pts])
    x,y = cv2.perspectiveTransform(pts, M)[0][0]
    return int(x), int(y)


def from_warped_to_real(x,y,M):
    pts = np.array([[x, y]], dtype="float32")
    pts = np.array([pts])
    M_inv = np.linalg.pinv(M)
    x,y = cv2.perspectiveTransform(pts, M_inv )[0][0]
    return int(x), int(y)


def show_and_destroy_img(name,img):
    cv2.namedWindow(name, cv2.WINDOW_NORMAL)
    cv2.resizeWindow(name, 300, 300)
    cv2.imshow(name, img)
    cv2.waitKey()
    cv2.destroyWindow(name)
