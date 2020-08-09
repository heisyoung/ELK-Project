from PyQt5.QtWidgets import *
from PyQt5 import uic
from PyQt5.QtCore import *
from elasticsearch import Elasticsearch
import sys
import winsound
import datetime

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
    # 로그 테이블
    def __init__(self,parent):
        super().__init__(parent)
        uic.loadUi("QTui/log_table.ui",self)
        self.refresh.clicked.connect(self.searchAPI)
        self.combo_box_options = ["Unknown", "False Positive", "Person"]
        self.index=parent.index
        self.es = parent.es
        self.searchAPI()
        self.show()

    def searchAPI(self):
        body = {"query": {"match_all": {}}, "size": 10, "sort": {"@timestamp": "desc"}}
        res= self.es.search(index=self.index,body=body)
        count = res['hits']['total']['value']
        if count >= 10:
            count = 10
        d=[]
        l=[]
        o=[]
        for i in range(count):
            d.append(res['hits']['hits'][i]['_source']['motion_detect'])
            l.append(res['hits']['hits'][i]['_source']['location'])
            o.append(res['hits']['hits'][i]['_source']['object'])

        for index in range(count):
            item1 = QTableWidgetItem(l[index])
            self.tableWidget.setItem(index, 0, item1)
            item2 = QTableWidgetItem(d[index])
            self.tableWidget.setItem(index, 1, item2)
            item3 = QTableWidgetItem(o[index])
            self.tableWidget.setItem(index, 2, item3)
            combo = QComboBox()
            button = QPushButton("Save")
            for list in self.combo_box_options:
                combo.addItem(list)
            self.tableWidget.setCellWidget(index, 3, combo)
            self.tableWidget.setCellWidget(index, 4, button)
            self.tableWidget.resizeColumnsToContents()
            button.clicked.connect(self.updateES)
        now = datetime.datetime.now().strftime("%y-%m-%d %H:%M:%S")
        self.label.setText("UPDATE "+now)

    def updateES(self):
        buttonClicked = self.sender()
        index = self.tableWidget.indexAt(buttonClicked.pos())
        value = self.tableWidget.item(index.row(),1).text()
        body = {"query": {"match": {"motion_detect" : value}}}
        result = self.es.search(index=self.index, body=body)
        docID = result['hits']['hits'][0]['_id']
        widget = self.tableWidget.cellWidget(index.row(), 3)
        current_value = widget.currentText()
        self.es.update(index=self.index, id=docID, body={"doc":{"object" : current_value}})
        self.searchAPI()



################### 메인 클래스 #####################

class alert_main(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi("QTui/alert_main.ui", self)
        self.setFixedSize(314, 218)
        self.timestamp_old = None
        self.timestamp_new = None
        self.ES_SERVER_IP = "127.0.0.1"
        self.ES_SERVER_PORT = "9200"
        self.index ="cctv"
        self.status = False
        self.optionES = menu_option(self)
        self.alert_enable.triggered.connect(self.alertEnable)
        self.alert_disable.triggered.connect(self.alertDisable)
        self.menu_ES_Server.triggered.connect(self.option_ES)
        self.log_table.clicked.connect(self.view)
        self.show()

    def Refresh(self):
        self.refresh = QTimer(self)
        self.refresh.start(5000)
        self.refresh.timeout.connect(self.searchES)

    def option_ES(self):
        self.optionES.exec_()
    def view(self):
        if self.status is True:
            logview(self)
        else:
            QMessageBox.about(self, "정보", "ES 서버상태를 확인해주세요.")

    def alertEnable(self):
        self.ES_SERVER_IP = self.optionES.es_ip
        self.ES_SERVER_PORT = self.optionES.es_port
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
        self.status = False
        self.refresh.stop()

    def searchES(self):
        self.ES_SERVER_IP = self.optionES.es_ip
        self.ES_SERVER_PORT = self.optionES.es_port

        try:
            self.ES_STATUS = self.function.ES_STATUS
        except:
            self.status_es_d.setText("disable")
            QMessageBox.about(self,"ES Server","  연결 실패      ")
            return self.alertDisable()

        self.function = function(self)
        self.function.start()
        self.es = Elasticsearch(hosts=self.ES_SERVER_IP,port=self.ES_SERVER_PORT)
        body = {"query": {"match_all": {}},"size": 1,"sort": {"@timestamp": "desc"}}

        try:
            result = self.es.search(index=self.index, body=body)
            self.status_es_d.setText("enable")
            self.location = result['hits']['hits'][0]['_source']['location']

            if self.timestamp_old is None:
                self.timestamp_old = result['hits']['hits'][0]['_source']['motion_detect']
            self.timestamp_new = result['hits']['hits'][0]['_source']['motion_detect']
            if self.timestamp_old != self.timestamp_new:
                self.timestamp_old = self.timestamp_new
                popup = alert_popup(self)
                popup.exec_()
        except:
            self.status_es_d.setText("disable")
            QMessageBox.about(self, "ES Server", "  연결 실패      ")
            return self.alertDisable()
        self.status = True


if __name__ == "__main__":
    app=QApplication(sys.argv)
    alert=alert_main()
    sys.exit(app.exec_())
