import os
import sys
import threading
import datetime
import numpy as np
import cv2
from PyQt5.QtWidgets import *
from PyQt5 import uic
from PyQt5.QtCore import *
from PyQt5.QtGui import *
from flask_opencv_streamer.streamer import Streamer
from flask import request,Flask

os.makedirs('log', exist_ok=True)
os.makedirs('video/event', exist_ok=True)

class CCTVOption(QDialog):
    def __init__(self,parent):
        super().__init__()
        uic.loadUi("QTui\cctv_option.ui",self)
        self.set_lat = None
        self.set_lon = None
        self.set_location = None
        self.input_lat.setText(parent.lat)
        self.input_lon.setText(parent.lon)
        self.input_location.setText(parent.location)
        self.save.clicked.connect(self.confirm)

        self.sensor.valueChanged.connect(self.getHorizontalInfo)


    def getHorizontalInfo(self) :
        self.sensor_value.setText(str(self.sensor.value()))

    def confirm(self):
        self.set_location = self.input_location.text()
        self.set_lat = self.input_lat.text()
        self.set_lon = self.input_lon.text()
        self.set_sensor = self.sensor.value()
        self.close()


class CCTVMain(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi("QTui\cctv_main.ui",self)
        self.video = None
        self.location = "CCTV 위치"
        self.lat = None
        self.lon = None
        self.CCTVOption = CCTVOption(self)
        self.sensor = 10
        self.fps = 60
        self.count = 0
        self.fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        self.action_setting.triggered.connect(self.exec_setting)

    def start(self):
        self.location = self.CCTVOption.set_location
        if self.location is None:
            QMessageBox.about(self, "정보", "위치를 입력해주세요.")
            return self.exec_setting()

        try:
            self.setCamera = cv2.VideoCapture('https://192.168.0.120:4343/video')
            _, self.img_o = self.setCamera.read()
            self.img_o = cv2.cvtColor(self.img_o, cv2.COLOR_RGB2GRAY)
        except:
            QMessageBox.about(self, "정보", "카메라를 확인해주세요.")
            return

        self.main_record = True
        self.event_record = False
        self.event_switch = False
        self.event_status = False

        self.timer = QTimer()
        self.timer.timeout.connect(self.nextframe)
        self.timer.start(1000 / self.fps)

        port = 3030
        require_login = False
        self.streamer = Streamer(port, require_login)

    def stop(self):
        self.main_video.release()
        self.setCamera.release()
        self.imgLabel.setPixmap(QPixmap.fromImage(QImage()))
        self.timer.stop()

    def nextframe(self):
        _,self.cam = self.setCamera.read()
        self.streamer.update_frame(self.cam)
        if not self.streamer.is_streaming:
            self.streamer.start_streaming()
        self.cam = cv2.cvtColor(self.cam,cv2.COLOR_BGR2RGB)
        self.img_p = cv2.cvtColor(self.cam,cv2.COLOR_RGB2GRAY)

        self.write_main()
        self.compare()
        self.img_o= self.img_p.copy()
        img= QImage(self.cam,self.cam.shape[1],self.cam.shape[0],QImage.Format_RGB888)
        pix=QPixmap.fromImage(img)
        self.imgLabel.setPixmap(pix)

    def write_main(self):
        cam = cv2.cvtColor(self.cam, cv2.COLOR_BGR2RGB)
        if self.main_record == True:
            self.main_record = False
            logdate = datetime.datetime.now().strftime("%y-%m-%d_%H%M%S")
            self.main_video = cv2.VideoWriter("video\MainVideo_" + logdate + ".mp4", self.fourcc, 20,
                                         (self.cam.shape[1], self.cam.shape[0]))
        if self.main_record == False:
            self.main_video.write(cam)

    def write_event(self):
        self.cam_rec = cv2.cvtColor(self.cam, cv2.COLOR_BGR2RGB)
        if (self.event_record == True) & (self.event_switch == False):
            self.event_record = False
            self.event_switch = True
            self.event_status = True
            logdate = datetime.datetime.now().strftime("%y-%m-%d_%H%M%S")
            self.write_log()
            self.event_video = cv2.VideoWriter("video\event\EventVideo_" + logdate + ".mp4", self.fourcc, 20,
                                         (self.cam.shape[1], self.cam.shape[0]))
        if self.event_switch == True:
            self.event_video.write(self.cam_rec)

    def write_log(self):
        date = datetime.datetime.utcnow().isoformat()
        self.lat = self.CCTVOption.set_lat
        self.lon = self.CCTVOption.set_lon
        log = open('log\detect.log', 'a')
        log.write(self.location + " " + self.lat + " " + self.lon + " " + date + " -\n")
        log.close()

    def compare(self):
        self.sensor = self.CCTVOption.set_sensor
        value = np.sum((self.img_o.astype("float") - self.img_p.astype("float")) ** 2)
        value /= float(self.img_o.shape[0] * self.img_p.shape[1])
        if (value>=self.sensor):
            self.event_record = True
            self.count = 0
        if (value<self.sensor):
            self.event_record = False
            if self.event_status == True:
                self.event_status = False
                self.event_timer()
        self.write_event()

    def event_timer(self):
        timer = threading.Timer(1, self.event_timer)
        timer.start()
        self.count += 1
        if self.count > 9:
            timer.cancel()
            self.event_video.release()
            self.event_switch = False

    def exec_setting(self):
        self.CCTVOption.exec_()

if __name__ == "__main__":

    app = QApplication(sys.argv)
    CCTVMain = CCTVMain()
    CCTVMain.show()
    sys.exit(app.exec_())