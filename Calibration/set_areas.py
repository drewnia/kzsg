import cv2 as cv
import numpy as np



class Drawer():
    __doc__ = "left mouse - left grid of area, right mouse - right grid of area, middle mouse - delete line"
    x_left = []
    x_right = []
    clear_img = None
    img = None
    h = 0
    path_to_lines = "lines_"

    def run(self,num_of_sector,image):
        print(self.__doc__)
        self.clear_img = image.copy()
        self.path_to_lines += str(num_of_sector)
        h = image.shape[0]

        cv.namedWindow('input')
        cv.setMouseCallback('input', self.onmouse)
        while True:
            self.img = self.clear_img.copy()

            for item in self.x_left:
                cv.line(self.img,(item,0),(item,h),(0,0,255), 6)
            for item in self.x_right:
                cv.line(self.img,(item,0),(item,h),(0,255,0), 6)

            cv.imshow('input', self.img)
            k = cv.waitKey(1)

            # key bindings
            if k == 27 or k == ord('s'):  # save image:  # esc to exit
                if len(self.x_left) != len(self.x_right):
                    self.x_left.clear()
                    self.x_right.clear()
                    continue
                cv.destroyWindow("input")
                self.x_left.sort()
                self.x_right.sort()
                ways = []
                items = zip(self.x_left, self.x_right)
                for item1,item2 in items:
                    self.img = self.clear_img.copy()
                    print("Choose way number as XX:")
                    cv.line(self.img, (item1, 0), (item1, h), (0, 0, 255), 6)
                    cv.line(self.img, (item2, 0), (item2, h), (0, 255, 0), 6)
                    cv.imshow("Close and input way number:", self.img)
                    cv.waitKey(0)
                    cv.destroyWindow("Close and input way number:")
                    b = input()
                    way = int(b)

                    ways.append(way)


                pts_np = np.column_stack([ways,self.x_left,self.x_right])
                np.savetxt(self.path_to_lines, pts_np, delimiter=',')
                break


    def onmouse(self, event, x, y, flags, param):

        if event == cv.EVENT_MBUTTONDOWN:
            for item in self.x_left:
                if abs(item - x) < 10:
                    self.x_left.remove(item)
            for item in self.x_right:
                if abs(item - x) < 10:
                    self.x_right.remove(item)
        elif event == cv.EVENT_LBUTTONDOWN:
            self.x_left.append(x)
        elif event == cv.EVENT_RBUTTONDOWN:
            self.x_right.append(x)

