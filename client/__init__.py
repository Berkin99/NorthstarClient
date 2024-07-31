#QT Designer to Python :

#pyrcc5.exe .\resource.qrc -o .\resource_rc.py
#pyuic5.exe .\northstar.ui -o .\northstar_ui.py

import sys
import os
sys.path.append('./')

from collections import deque
import serial.tools.list_ports
from PyQt5.QtWidgets import QMainWindow, QApplication, QPushButton, QWidget, QAction
from PyQt5.QtCore import Qt, pyqtSlot, QFile, QTextStream

from northstar_ui import Ui_MainWindow
import northlib.ntrp as ntrp

class NorthClient(QMainWindow):
    
    def __init__(self):
        super(NorthClient,self).__init__()
        #UI Setup
        self.ui = Ui_MainWindow()
        self.ui.setupUi(self)
        self.ui.w_page.setCurrentIndex(0)
        self.ui.send.clicked.connect(self.consoleSend)
        self.ui.sendmsg.returnPressed.connect(self.consoleSend)

        # Connecting Menu buttons to related functions 
        self.ui.menuSerial.aboutToShow.connect(self.portSearch)
        self.ui.action9600.triggered.connect(lambda: self.setBaudRate(9600))
        self.ui.action19200.triggered.connect(lambda: self.setBaudRate(19200))
        self.ui.action38400.triggered.connect(lambda: self.setBaudRate(38400))
        self.ui.action57600.triggered.connect(lambda: self.setBaudRate(57600))
        self.ui.action115200.triggered.connect(lambda: self.setBaudRate(115200))
        
        # Client Serial
        self.serialport = None
        self.serialbaud = 0
        self.serialcom  = 'COM0'
        self.setBaudRate(int(self.ui.baudrateLabel.text()))

        # Limit The Console Maximum Line 
        self.ui.console.setMaximumBlockCount(200)
        
    def setBaudRate(self,baudrate):
        self.ui.baudrateLabel.setText(str(baudrate))
        self.serialbaud = baudrate      

    def setComPort(self, com):
        self.ui.comportLabel.setText(com)
        self.serialcom = com
        #Set serial port when "COM" selected
        if self.serialport != None: self.serialport.close()
        self.serialport = serial.Serial(self.serialcom,self.serialbaud)
        self.serialport.open()

    def portSearch(self):
        #Search and add founded COM ports as QAction to QMenu 
        ports = [port.device for port in serial.tools.list_ports.comports()]
        self.ui.menuCOM.clear()
        for port in ports:
            act = QAction(port, self)
            act.text = port
            act.triggered.connect(lambda:self.setComPort(port))
            self.ui.menuCOM.addAction(act)

    def consoleSend(self):
        message = self.ui.sendmsg.text()        # Get the text from text input
        self.ui.sendmsg.clear()                 # Clear text input area
        self.ui.sendmsg.setFocus()              # Focus text input area again

        self.consoleAppend(message+"\r\n")      # Insert the message with <CR><LF>
        # Recognize if it is a Command and return
        # Else transmit to serial port if not none
        if self.serialport != None:
            self.serialport.write(message.encode()) # Transmit

    def consoleAppend(self, data=None):
        if data==None:return #Return if there is no data
        self.ui.console.insertPlainText(data)
        self.ui.console.verticalScrollBar().setValue(self.ui.console.verticalScrollBar().maximum())
        
    def consoleClear(self):
        self.ui.console.clear()

    def closeEvent(self,event):
        # On Close: 
        #"closeEvent()" is predetermined close function by PyQt
        if self.serialport!= None: self.serialport.close()
        event.accept()



if __name__ == '__main__':
    app = QApplication(sys.argv)

    script_dir = os.path.dirname(__file__) #<-- absolute dir the script is in
    style_path = "style.qss"
    abs_file_path = os.path.join(script_dir, style_path)
    with open(abs_file_path,"r") as style_file:
        style_str = style_file.read()

    app.setStyleSheet(style_str)

    window = NorthClient()
    window.show()

    sys.exit(app.exec())

        