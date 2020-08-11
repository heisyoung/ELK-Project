from PyQt5.QtWidgets import *
from PyQt5 import uic
from PyQt5.QtCore import *
from PyQt5.QtGui import *
import cv2, datetime, sys
import numpy as np
import os

os.makedirs('log', exist_ok=True)
os.makedirs('video', exist_ok=True)
form_class = uic.loadUiType("QTui\main.ui")[0]


class setting(QDialog):
    def __init__(self,parent):
        super().__init__()
        uic.loadUi("QTui\setting.ui",self)
        self.setting_lat = ""
        self.setting_lon = ""
        self.setting_location = ""
        self.input_lat.setText(parent.lat)
        self.input_lon.setText(parent.lon)
        self.input_location.setText(parent.location)
        self.test.clicked.connect(self.confirm)

        self.senser.valueChanged.connect(self.getHorizontalInfo)

    def showHorizontalSliderValue(self) :
        self.lbl_horizontal.setText(str(self.senser.value()))

    def getHorizontalInfo(self) :
        print("Now : " + str(self.senser.value()))

    def confirm(self):
        self.setting_location = self.input_location.text()
        self.setting_lat = self.input_lat.text()
        self.setting_lon = self.input_lon.text()
        self.cg_senser = self.senser.value()
        self.close()


class thread1(QThread):
    def __init__(self):
        super().__init__()
    def run(self):
        pass

class MyWindow(QMainWindow, form_class):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.logsav, self.switch, self.rec = False, False, False
        self.video = None
        self.font = cv2.FONT_ITALIC
        self.location = "fds"
        self.lat = "fds"
        self.lon = "fsdf"
        self.cg = setting(self)
        self.senser = 0
        self.count = 600
        self.fps=30
        self.fourcc = cv2.VideoWriter_fourcc(*'mp4v')

        self.action_setting.triggered.connect(self.settingFunction)




    def start(self):
        self.timer = QTimer()
        self.timer.timeout.connect(self.nextframe)
        self.timer.start(1000/self.fps)

        try:
            self.location = self.cg.setting_location
            print(self.location)                        # 값이 안나옴(자료형은 str)
            self.cpt = cv2.VideoCapture(0)
            _,self.img_o = self.cpt.read()
            self.img_o = cv2.cvtColor(self.img_o,cv2.COLOR_RGB2GRAY)
            print("try test")                           # except문으로 안가짐
        except:
            print("try except")
            self.error()



    def error(self):
        self.imgLabel.setPixmap(QPixmap.fromImage(QImage('end.jpg')))
        self.timer.stop()

    def stop(self):
        self.imgLabel.setPixmap(QPixmap.fromImage(QImage('end.jpg')))
        self.timer.stop()

    def nextframe(self):
        _,self.cam = self.cpt.read()
        self.cam = cv2.cvtColor(self.cam,cv2.COLOR_BGR2RGB)
        self.img_p = cv2.cvtColor(self.cam,cv2.COLOR_RGB2GRAY)
        self.compare(self.img_o,self.img_p)
        self.img_o= self.img_p.copy()

        img= QImage(self.cam,self.cam.shape[1],self.cam.shape[0],QImage.Format_RGB888)
        pix=QPixmap.fromImage(img)
        self.imgLabel.setPixmap(pix)

    def settingFunction(self):
        #self.setting = thread1()
        #self.setting.start()
        #popup = setting(self)
        #popup.exec_()
        self.cg.exec_()

    def compare(self,img_o,img_p):
        self.senser = self.cg.cg_senser
        err = np.sum((img_o.astype("float") - img_p.astype("float")) ** 2)
        err /= float(img_o.shape[0] * img_p.shape[1])

        if (err>=self.senser):
            self.mklog()
            self.count = 0
            logdate = datetime.datetime.now().strftime("%y-%m-%d %H:%M:%S")
            print(logdate)
            print("감지")
        if (err<self.senser):
            self.count += 1
            self.logsav  = False
            if (self.count > self.senser):
                self.mklog()
                self.count = 0
            else :
                self.count -= 0

        if (self.count > self.senser):
            self.rec = False
        if self.rec == True:
            self.video.write(self.cam)
        if (self.rec == False) & (self.count > self.senser):
            if self.video != None:
                self.video.release()
                self.video = None
                #센서는 sensor

    def mklog(self):
        date = datetime.datetime.utcnow().isoformat()
        logdate = datetime.datetime.now().strftime("%y-%m-%d_%H%M%S")

        self.lat = self.cg.setting_lat
        self.lon = self.cg.setting_lon

        print(self.lat)

        if (self.logsav == False) & (self.count > self.senser):
            print("Test")
            self.logsav, self.switch, self.rec = True, True, True
            self.video = cv2.VideoWriter("video\Video_" + logdate + ".mp4", self.fourcc, 20,
                                         (self.cam.shape[1], self.cam.shape[0]))

            log = open('log\detect.log', 'a')

            log.write(self.location + " " + self.lat + " " + self.lon + " " + date + "-\n")

            log.close()
            print("움직임 감지 : 로그 저장")


if __name__ == "__main__":
    app = QApplication(sys.argv)
    myWindow = MyWindow()
    myWindow.show()
    #app.exec_()
    sys.exit(app.exec_())