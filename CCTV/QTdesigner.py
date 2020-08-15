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


class CCTVsetting(QDialog):
    def __init__(self,parent):
        super().__init__()
        uic.loadUi("QTui\setting.ui",self)
        self.setting_lat = ""
        self.setting_lon = ""
        self.setting_location = None
        self.input_lat.setText(parent.lat)
        self.input_lon.setText(parent.lon)
        self.input_location.setText(parent.location)
        self.test.clicked.connect(self.confirm)
        self.senser.valueChanged.connect(self.getHorizontalInfo)


    def getHorizontalInfo(self) :
        print("Now : " + str(self.senser.value()))

    def confirm(self):
        self.setting_location = self.input_location.text()
        self.setting_lat = self.input_lat.text()
        self.setting_lon = self.input_lon.text()
        self.setting_senser = self.senser.value()
        self.close()

class CCTVMain(QMainWindow, form_class):
    def __init__(self):
        super().__init__()
        self.setupUi(self)
        self.logsav, self.switch, self.rec = False, False, False
        self.video = None
        self.location = "default"
        self.lat = "0"
        self.lon = "0"
        self.CCTVsetting = CCTVsetting(self)
        self.senser = 0
        self.count = 600
        self.fps=30
        self.fourcc = cv2.VideoWriter_fourcc(*'mp4v')

        self.action_setting.triggered.connect(self.settingFunction)

    def start(self):

        self.location = self.CCTVsetting.setting_location
        if self.location is None:
            QMessageBox.about(self, "정보", "위치를 입력해주세요.")
            return self.settingFunction()
        print("1")

        try:
            self.cpt = cv2.VideoCapture(0)
            _, self.img_o = self.cpt.read()
            self.img_o = cv2.cvtColor(self.img_o, cv2.COLOR_RGB2GRAY)
        except:
            QMessageBox.about(self, "정보", "카메라를 확인해주세요.")
            return
        self.timer = QTimer()
        self.timer.timeout.connect(self.nextframe)
        self.timer.start(1000 / self.fps)
        self.wait = True
        self.record = True
        self.record2 = True
        self.logswitch = True
        print("됨")

    def stop(self):
        self.mainvideo.release()
        self.video.release()
        self.imgLabel.setPixmap(QPixmap.fromImage(QImage()))
        self.timer.stop()
        self.comparetimer.stop()

    def nextframe(self):
        _,self.cam = self.cpt.read()
        self.cam = cv2.cvtColor(self.cam,cv2.COLOR_BGR2RGB)
        self.img_p = cv2.cvtColor(self.cam,cv2.COLOR_RGB2GRAY)
        self.compare(self.img_o,self.img_p)
        self.img_o= self.img_p.copy()

        img= QImage(self.cam,self.cam.shape[1],self.cam.shape[0],QImage.Format_RGB888)
        pix=QPixmap.fromImage(img)
        self.imgLabel.setPixmap(pix)

        if self.record2 == True :
            self.record2 = False
            logdate = datetime.datetime.now().strftime("%y-%m-%d_%H%M%S")
            self.mainvideo = cv2.VideoWriter("video\MainVideo_" + logdate + ".mp4", self.fourcc, 20,
                                         (self.cam.shape[1], self.cam.shape[0]))
        self.cam = cv2.cvtColor(self.cam,cv2.COLOR_BGR2RGB)
        if self.record == False :
            self.video.write(self.cam)
        self.mainvideo.write(self.cam)
    def settingFunction(self):
        self.CCTVsetting.exec_()

    def compare(self,img_o,img_p):

        self.senser = self.CCTVsetting.setting_senser
        err = np.sum((img_o.astype("float") - img_p.astype("float")) ** 2)
        err /= float(img_o.shape[0] * img_p.shape[1])
        if (err>=self.senser):
            self.moveing = True
            self.mklog()
            logdate = datetime.datetime.now().strftime("%y-%m-%d %H:%M:%S")
            print(logdate)
            print("감지")

        if (err<self.senser):
            self.moveing = False
            if self.wait == True :
                self.wait = False
                self.logsav = False
                self.comparetimer = QTimer()
                self.comparetimer.timeout.connect(self.mklog)
                self.comparetimer.start(1000*3)

    def mklog(self):
        print("3초마다")
        self.wait = True
        date = datetime.datetime.utcnow().isoformat()
        self.lat = self.CCTVsetting.setting_lat
        self.lon = self.CCTVsetting.setting_lon
        print(self.lat)
        if (self.logsav == False) & (self.count > self.senser):
            self.logsav, self.rec = True, True
            if self.logswitch == True :
                self.logswitch = False
                log = open('log\detect.log', 'a')
                log.write(self.location + " " + self.lat + " " + self.lon + " " + date + "-\n")
                log.close()
                self.switchtimer = QTimer()
                self.switchtimer.timeout.connect(self.logswich)
                self.switchtimer.start(1000 * 3)


            if self.moveing == True :
                self.writevideo()

    def logswich(self):
        if self.logswitch == False:
            self.logswitch = True
            self.mklog()
    def writevideo(self):
        if self.record == True :
            self.record = False
            logdate = datetime.datetime.now().strftime("%y-%m-%d_%H%M%S")
            self.video = cv2.VideoWriter("video\Video_" + logdate + ".mp4", self.fourcc, 20,
                                         (self.cam.shape[1], self.cam.shape[0]))
            self.videotimer = QTimer()
            self.videotimer.timeout.connect(self.stopvideos)
            self.videotimer.start(1000*3)


    def stopvideos(self):
        self.record = True
        if self.record == True :
            self.video.release()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    CCTVMain = CCTVMain()
    CCTVMain.show()
    sys.exit(app.exec_())