from PyQt5.QtWidgets import *
from PyQt5 import uic
from PyQt5.QtCore import *
from elasticsearch import Elasticsearch
import sys
import winsound

class alert_popup(QDialog):
    # 경고창
    def __init__(self,parent):
        super().__init__()
        uic.loadUi("QTui/alert_popup.ui",self)
        alert_text = "위치 : {} , 탐지 시간 : {}".format(parent.location,parent.timestamp_new)
        self.textBrowser.setPlainText(alert_text)
        winsound.Beep(2000,1000)

class function(QThread):
    # ES 상태 확인
    def __init__(self,parent):
        super().__init__()
        self.es = Elasticsearch(hosts=parent.ES_SERVER_IP, port=parent.ES_SERVER_PORT)
    def run(self):
        self.ES_STATUS = self.es.ping()

class menu_option(QDialog):
    # 메뉴-옵션창
    def __init__(self,parent):
        super().__init__()
        uic.loadUi("QTui/alert_option.ui", self)
        self.setFixedSize(310, 105)
        self.es_ip = None
        self.es_port = None
        self.input_id.setText(parent.ES_SERVER_IP)
        self.input_port.setText(parent.ES_SERVER_PORT)
        self.pushButton.clicked.connect(self.confirm)
    def confirm(self):
        self.es_ip = self.input_id.text()
        self.es_port = self.input_port.text()
        self.close()

class menu_help(QDialog):
    # 메뉴-도움말
    pass
class menu_about(QDialog):
    # 메뉴-정보창
    pass

class logview(QDialog):
    def __init__(self,parent):
        super().__init__(parent)
        uic.loadUi("table.ui",self)
        self.show()

################### 메인 클래스 #####################

class alert_main(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi("QTui/alert_main.ui", self)
        self.setFixedSize(400, 280)
        self.timestamp_old = None
        self.timestamp_new = None
        self.ES_SERVER_IP = "127.0.0.1"
        self.ES_SERVER_PORT = "9200"
        self.test = menu_option(self)

        self.alert_enable.triggered.connect(self.alertEnable)
        self.alert_disable.triggered.connect(self.alertDisable)
        self.menu_ES_Server.triggered.connect(self.option_ES)
        self.pushButton.clicked.connect(self.view)
        self.show()

    def Refresh(self):
        self.refresh = QTimer(self)
        self.refresh.start(5000)
        self.refresh.timeout.connect(self.searchES)

    def option_ES(self):
        self.test.exec_()
    def view(self):
        logview(self)

    def alertEnable(self):
        self.ES_SERVER_IP = self.test.es_ip
        self.ES_SERVER_PORT = self.test.es_port
        self.status_alert_d.setText("enable")
        self.alert_enable.setEnabled(False)
        self.alert_disable.setEnabled(True)

        self.function = function(self)
        self.function.start()
        self.Refresh()

    def alertDisable(self):
        self.status_alert_d.setText("disable")
        self.alert_enable.setEnabled(True)
        self.alert_disable.setEnabled(False)
        self.refresh.stop()

    def searchES(self):
        self.ES_SERVER_IP = self.test.es_ip
        self.ES_SERVER_PORT = self.test.es_port
        print(self.ES_SERVER_IP)
        print(self.ES_SERVER_PORT)
        try:
            self.ES_STATUS = self.function.ES_STATUS
        except:
            self.status_es_d.setText("disable")
            QMessageBox.about(self,"ES Server","  연결 실패      ")
            return self.alertDisable()

        self.function = function(self)
        self.function.start()
        self.es = Elasticsearch(hosts=self.ES_SERVER_IP,port=self.ES_SERVER_PORT)
        index = "cctv*"
        body = {"query": {"match_all": {}},"size": 1,"sort": {"@timestamp": "desc"}}

        try:
            res = self.es.search(index=index, body=body)
            self.status_es_d.setText("enable")
            self.location = res['hits']['hits'][0]['_source']['location']

            if self.timestamp_old is None:
                self.timestamp_old = res['hits']['hits'][0]['_source']['motion_detect']
            self.timestamp_new = res['hits']['hits'][0]['_source']['motion_detect']

            if self.timestamp_old != self.timestamp_new:
                self.timestamp_old = self.timestamp_new
                popup = alert_popup(self)
                popup.exec_()
        except:
            self.status_es_d.setText("disable")
            QMessageBox.about(self, "ES Server", "  연결 실패      ")
            return self.alertDisable()


if __name__ == "__main__":
    app=QApplication(sys.argv)
    alert=alert_main()
    sys.exit(app.exec_())
