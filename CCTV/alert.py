import sys
import datetime
import winsound
from PyQt5.QtWidgets import *
from PyQt5 import uic
from PyQt5.QtCore import *
from elasticsearch import Elasticsearch


class Alert(QDialog):
    # 경고창
    def __init__(self,parent):
        super().__init__()
        uic.loadUi("QTui/alert_popup.ui",self)
        alert_text = "위치 : {} , 탐지 시간 : {}".format(parent.location,parent.timestamp_new)
        self.textBrowser.setPlainText(alert_text)
        winsound.Beep(2000,1000)

class ESping(QThread):
    # ES 상태 확인
    def __init__(self,parent):
        super().__init__()
        self.es = Elasticsearch(hosts=parent.ES_SERVER_IP, port=parent.ES_SERVER_PORT)

    def run(self):
        self.ES_STATUS = self.es.ping()


class OptionMenu(QDialog):
    # 메뉴-옵션창
    def __init__(self,parent):
        super().__init__()
        uic.loadUi("QTui/alert_option.ui", self)
        self.setFixedSize(310, 153)
        self.ES_IP = parent.ES_SERVER_IP
        self.ES_PORT = parent.ES_SERVER_PORT
        self.input_ip.setText(parent.ES_SERVER_IP)
        self.input_port.setText(parent.ES_SERVER_PORT)
        self.okbtn.clicked.connect(self.confirm)

    def confirm(self):
        self.ES_IP = self.input_ip.text()
        self.ES_PORT = self.input_port.text()
        self.es_id = self.input_id.text()
        self.es_pw = self.input_pw.text()
        self.close()

class HelpMenu(QDialog):
    # 메뉴-도움말
    pass

class AboutMenu(QDialog):
    # 메뉴-정보창
    pass

class LogTable(QDialog):
    # 로그 테이블
    def __init__(self,parent):
        super().__init__(parent)
        uic.loadUi("QTui/log_table.ui",self)
        self.refresh.clicked.connect(self.search_es)
        self.combo_box_options = ["Unknown", "False Positive", "Person"]
        self.index=parent.index
        self.es = parent.es
        self.search_es()
        self.show()

    def search_es(self):
        body = {"query": {"match_all": {}}, "size": 10, "sort": {"@timestamp": "desc"}}
        res= self.es.search(index=self.index,body=body)
        count = res['hits']['total']['value']
        if count >= 10:
            count = 10
        timestamp=[]
        location=[]
        objects=[]
        for i in range(count):
            timestamp.append(res['hits']['hits'][i]['_source']['detect_motion'])
            location.append(res['hits']['hits'][i]['_source']['location'])
            objects.append(res['hits']['hits'][i]['_source']['object'])

        for index in range(count):
            item1 = QTableWidgetItem(location[index])
            self.tableWidget.setItem(index, 0, item1)
            item2 = QTableWidgetItem(timestamp[index])
            self.tableWidget.setItem(index, 1, item2)
            item3 = QTableWidgetItem(objects[index])
            self.tableWidget.setItem(index, 2, item3)
            combo = QComboBox()
            button = QPushButton("Save")
            for list in self.combo_box_options:
                combo.addItem(list)
            self.tableWidget.setCellWidget(index, 3, combo)
            self.tableWidget.setCellWidget(index, 4, button)
            self.tableWidget.resizeColumnsToContents()
            button.clicked.connect(self.update_es)
        now = datetime.datetime.now().strftime("%y-%m-%d %H:%M:%S")
        self.update_time.setText("UPDATE "+now)

    def update_es(self):
        buttonClicked = self.sender()
        index = self.tableWidget.indexAt(buttonClicked.pos())
        value = self.tableWidget.item(index.row(),1).text()
        body = {"query": {"match": {"motion_detect" : value}}}
        result = self.es.search(index=self.index, body=body)
        docID = result['hits']['hits'][0]['_id']
        widget = self.tableWidget.cellWidget(index.row(), 3)
        current_value = widget.currentText()
        self.es.update(index=self.index, id=docID, body={"doc":{"object" : current_value}})
        self.search_es()



################### 메인 클래스 #####################

class Main(QMainWindow):
    def __init__(self):
        super().__init__()
        uic.loadUi("QTui/alert_main.ui", self)
        self.setFixedSize(314, 218)
        self.timestamp_old = None
        self.timestamp_new = None
        self.es_server_id = None
        self.es_server_pw = None
        self.ES_SERVER_IP = "127.0.0.1"
        self.ES_SERVER_PORT = "9200"
        self.index ="cctv"
        self.status = False
        self.option_es = OptionMenu(self)
        self.alert_enable.triggered.connect(self.Alert_Enable)
        self.alert_disable.triggered.connect(self.Alert_Disable)
        self.menu_es_server.triggered.connect(self.exec_option)
        self.log_table.clicked.connect(self.view)
        self.show()

    def refresh(self):
        self.timer = QTimer(self)
        self.timer.start(5000)
        self.timer.timeout.connect(self.search_es)

    def exec_option(self):
        self.option_es.exec_()


    def view(self):
        if self.status:
            LogTable(self)
        else:
            QMessageBox.about(self, "정보", "ES 서버상태를 확인해주세요.")

    def Alert_Enable(self):
        self.ES_SERVER_IP = self.option_es.ES_IP
        self.ES_SERVER_PORT = self.option_es.ES_PORT
        self.status_alert_d.setText("enable")
        self.alert_enable.setEnabled(False)
        self.alert_disable.setEnabled(True)

        self.es_ping = ESping(self)
        self.es_ping.start()
        self.refresh()

    def Alert_Disable(self):
        self.status_alert_d.setText("disable")
        self.status_es_d.setText("disable")
        self.alert_enable.setEnabled(True)
        self.alert_disable.setEnabled(False)
        self.status = False
        self.timer.stop()

    def search_es(self):
        self.ES_SERVER_IP = self.option_es.ES_IP
        self.ES_SERVER_PORT = self.option_es.ES_PORT
        self.es_server_id = self.option_es.es_id
        self.es_server_pw = self.option_es.es_pw

        try:
            self.ES_STATUS = self.es_ping.ES_STATUS
        except:
            self.status_es_d.setText("disable")
            QMessageBox.about(self,"ES Server","  연결 실패[1]      ")
            return self.Alert_Disable()

        self.es_ping = ESping(self)
        self.es_ping.start()
        self.es = Elasticsearch(hosts=self.ES_SERVER_IP,port=self.ES_SERVER_PORT,http_auth=(self.es_server_id, self.es_server_pw))
        body = {"query": {"match_all": {}},"size": 1,"sort": {"@timestamp": "desc"}}

        try:
            result = self.es.search(index=self.index, body=body)
            self.status_es_d.setText("enable")
            self.location = result['hits']['hits'][0]['_source']['location']

            if self.timestamp_old is None:
                self.timestamp_old = result['hits']['hits'][0]['_source']['detect_motion']
            self.timestamp_new = result['hits']['hits'][0]['_source']['detect_motion']
            if self.timestamp_old != self.timestamp_new:
                self.timestamp_old = self.timestamp_new
                alert = Alert(self)
                alert.exec_()
        except:
            self.status_es_d.setText("disable")
            QMessageBox.about(self, "ES Server", "  연결 실패[2]      ")
            return self.Alert_Disable()
        self.status = True

if __name__ == "__main__":
    app=QApplication(sys.argv)
    main=Main()
    sys.exit(app.exec_())
