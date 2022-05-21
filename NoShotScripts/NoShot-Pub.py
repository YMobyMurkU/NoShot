#!/usr/bin/env python3
import subprocess
import io
from os import system,name
import sys
from pathlib import Path
import time
import pytesseract
from PIL import Image, ImageChops
from PyQt5 import QtCore, QtGui, QtWidgets
from PyQt5.QtCore import Qt


noShotArt = """
  _   _            _____   _               _                                        
 | \ | |          / ____| | |             | |      
 |  \| |   ___   | (___   | |__     ___   | |_    
 | . ` |  / _ \   \___ \  | '_ \   / _ \  | __|  
 | |\  | | (_) |  ____) | | | | | | (_) | | |_   
 |_| \_|  \___/  |_____/  |_| |_|  \___/   \__|                                  
                                                                                                                                
"""

class Snipper(QtWidgets.QWidget):
    def __init__(self, parent=None, flags=Qt.WindowFlags()):
        super().__init__(parent=parent, flags=flags)

        self.setWindowTitle("TextShot")
        self.setWindowFlags(
            Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Dialog
        )
        windowGeometry = QtWidgets.QApplication.desktop().geometry()
        self.setGeometry(windowGeometry)
        self.screen = QtWidgets.QApplication.screens()[0].grabWindow(0, *windowGeometry.getRect())
        palette = QtGui.QPalette()
        palette.setBrush(self.backgroundRole(), QtGui.QBrush(self.screen))
        self.setPalette(palette)
        QtWidgets.QApplication.setOverrideCursor(QtGui.QCursor(QtCore.Qt.CrossCursor))
        self.start, self.end = QtCore.QPoint(), QtCore.QPoint()


    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            QtWidgets.QApplication.quit()

        return super().keyPressEvent(event)


    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.setPen(Qt.NoPen)
        painter.setBrush(QtGui.QColor(0, 0, 0, 100))
        painter.drawRect(0, 0, self.width(), self.height())
        if self.start == self.end:
            return super().paintEvent(event)
        painter.setPen(QtGui.QPen(QtGui.QColor(255, 255, 255), 3))
        painter.setBrush(painter.background())
        painter.drawRect(QtCore.QRect(self.start, self.end))
        return super().paintEvent(event)


    def mousePressEvent(self, event):
        self.start = self.end = event.pos()
        self.update()
        return super().mousePressEvent(event)


    def mouseMoveEvent(self, event):
        self.end = event.pos()
        self.update()
        return super().mousePressEvent(event)


    def mouseReleaseEvent(self, event):
        if self.start == self.end:
            return super().mouseReleaseEvent(event)
        self.hide()
        QtWidgets.QApplication.processEvents()
        shot = self.screen.copy(
            min(self.start.x(), self.end.x()),
            min(self.start.y(), self.end.y()),
            abs(self.start.x() - self.end.x()),
            abs(self.start.y() - self.end.y()),
        )
        runStatus = 1
        while runStatus > 0:
            try:
                windowGeometry = QtWidgets.QApplication.desktop().geometry()
                self.setGeometry(windowGeometry)
                self.screen = QtWidgets.QApplication.screens()[0].grabWindow(0, *windowGeometry.getRect())
                shot = self.screen.copy(
                    min(self.start.x(), self.end.x()),
                    min(self.start.y(), self.end.y()),
                    abs(self.start.x() - self.end.x()),
                    abs(self.start.y() - self.end.y()),
                )            
                processImage(shot)
                time.sleep(4)
                #QtWidgets.QApplication.quit()
            except KeyboardInterrupt:
                print(noShotArt)
                monitorProc.kill()
                sys.exit()

def processImage(img):
    buffer = QtCore.QBuffer()
    buffer.open(QtCore.QBuffer.ReadWrite)
    img.save(buffer, "PNG")
    pil_img = Image.open(io.BytesIO(buffer.data()))
    pil_img = ImageChops.invert(pil_img)
    buffer.close()
    try:
        result = pytesseract.image_to_string(
            pil_img, timeout=5, lang='eng', config='-c tessedit_char_whitelist=0123456789 --psm 11'
        ).strip()
    except RuntimeError as error:
        print(f"ERROR: An error occurred when trying to process the image: {error}")
        return
    if result:
        result = result.replace('\n',',')
        result = result.replace(',,',',')
        result = result.replace(' ','')
        print(f'Log : {eeSystem},{result}')
        #write to log file     
        with open(logFile, "a+") as log:
            log.write(f'{eeSystem},{result}\n')
    #if not result returned from OCR print such
    else:
        print(f"Log: Stat illegible")


def clearShell():
    # for windows
    if name == 'nt':
        _ = system('cls')
    # for mac and linux(here, os.name is 'posix')
    else:
        _ = system('clear')


if __name__ == "__main__":
    QtCore.QCoreApplication.setAttribute(Qt.AA_DisableHighDpiScaling)
    app = QtWidgets.QApplication(sys.argv)
    try:
        pytesseract.get_tesseract_version()
    except EnvironmentError:
        print(
            "ERROR: Tesseract is either not installed or cannot be reached.\n"
            "Have you installed it to C:\Program Files and ran the NoShot-AdminSetup.bat?"
        )
        sys.exit()
    clearShell()
    #get inputs
    print(noShotArt)
    eeSystem = input("Input system being monitored. : ")
    channelWebHook = input("Paste in (right click) discord channel webhook... : ")
    basicThreshold = input("What threshold should WARNING Discord messasge post at (change in neut/hostile population, i.e 1)? : ")
    basicPingGroup = input("Which group should be pinged at WARNING threshold (i.e none, @here, etc)? : ")
    alertThreshold = input("What threshold should ALERT Discord message post at (change in neut/hostile population, i.e 3)? : ")
    alertPingGroup = input("Which group should be pinged at ALERT threshold (i.e none, @here, etc)? : ")
    clearShell()
    print(noShotArt)
    #set path to log file folder
    logFileFolder = "./SystemLogs"
    #set log file name
    logFileName = str(f"{eeSystem}.log")
    #'universify' path
    Path(f'{logFileFolder}').mkdir(parents=True, exist_ok=True)
    #set log file
    logFile = Path(f'{logFileFolder}/{logFileName}')
    #create log file if doesn't exist
    logFile.touch(exist_ok=True)
    #start monitor process
    print(f'Click on the terminal/shell and press "Ctrl + C" to stop at anytime')
    print(f'Starting Monitor : System - "{eeSystem}" | Warning Threshold/Group: "{basicThreshold} / {basicPingGroup}" | ALERT Threshold/Group: "{alertThreshold} / {alertPingGroup}"')
    print(f"Logging to: {logFileName}")
    print("\n")
    print("Using the left mouse btn, click and drag a rectangle over the population stats on the EE window")
    time.sleep(2)
    print("\n")
    monitorProc = subprocess.Popen(r'py .\NoShotScripts\NoShot_Discord_Pub.py ' + f'{logFile} {channelWebHook} {basicThreshold} {basicPingGroup} {alertThreshold} {alertPingGroup}', shell=False)
    #set capture log
    window = QtWidgets.QMainWindow()
    snipper = Snipper(window)
    snipper.show()
    #prep exit   
    sys.exit(app.exec_())