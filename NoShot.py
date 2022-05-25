#!/usr/bin/env python3
import argparse
from cmath import log
import subprocess
import requests
import tailer
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
        continuousCapture(self, shot)


def continuousCapture(self, shot):
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
            time.sleep(5)
        except KeyboardInterrupt:
            print(noShotArt)
            if cmdArgs.run == 'report':
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
            pil_img, timeout=5, lang='eng', config='-c tessedit_char_whitelist=0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ --psm 11'
        ).strip()
    except RuntimeError as error:
        print(f"ERROR: An error occurred when trying to process the image: {error}")
        return
    if result:
        result = result.replace('\n',',')
        result = result.replace(',,',',')
        result = result.replace(' ','')
        result = f'{eeSystem},{result}'
        print(f'INFO : {result}')
        #write to log file     
        with open(logFile, "a+") as log:
            log.write(f'{result}\n')
        return result
    #if not result returned from OCR print such
    else:
        result = 'illegible'
        print(f"ERROR : Stats illegible")
        return result


#function to post 
def PostDiscordMessage(channelWebHook, logEvent):
    #set message content
    jsonData = {'content' : '{}'.format(logEvent)}
    #create discord message post request
    discordResponse = requests.post(channelWebHook, json=jsonData)
    #get status code of post request
    responseCode = int((discordResponse.status_code))
    # if response code = 204 (success) print success msg to console
    if responseCode == 204:
        print(f'Success Posting Message: {logEvent}')
    #else print failure msg to console
    else:
        print(f'Failure Posting Message: {logEvent}')


#function to watch log
def watch_log(logFile):
    print('Starting Reporting Service\n')
    #initialize last log var
    lastLogEvent = "null,0,0,0"
    logCount = 0
    #for each line in log file - note this begins with NEW data sent AFTER program is started
    for logEvent in tailer.follow(open(logFile)):
        if logCount != 0:
            try:
                #calls Post Discord Msg function with the channel's webhook and the log file's line
                if str(logEvent) != str(lastLogEvent):
                    logEventSplit = str(logEvent).split(',')
                    lastLogEventSplit = str(lastLogEvent).split(',')
                    try:
                        #if hostile or neutral increase greater than or equal to alert threshold
                        if (abs(int(logEventSplit[2]) - int(lastLogEventSplit[2])) >= int(alertThreshold)) or (abs(int(logEventSplit[3]) - int(lastLogEventSplit[3])) >= int(alertThreshold)):
                            logMessage = (f'ALERT: System: {logEventSplit[0]} | Hostile: {logEventSplit[2]} | Neutral: {logEventSplit[3]} | Criminal: {logEventSplit[1]}\n{alertPingGroup}')
                            print(logMessage)
                            PostDiscordMessage(channelWebHook, f'{logMessage}')
                        #else if hostile or neutral increase greater than or equal to warning threshold    
                        elif (abs(int(logEventSplit[2]) - int(lastLogEventSplit[2])) >= int(basicThreshold)) or (abs(int(logEventSplit[3]) - int(lastLogEventSplit[3])) >= int(basicThreshold)):
                            logMessage = (f'WARNING: System: {logEventSplit[0]} | Hostile: {logEventSplit[2]} | Neutral: {logEventSplit[3]} | Criminal: {logEventSplit[1]}\n{basicPingGroup}')
                            print(logMessage)
                            PostDiscordMessage(channelWebHook, f'{logMessage}')
                        #otherwise 
                        else:
                            logMessage = (f'NONE: System: {logEventSplit[0]} | Hostile: {logEventSplit[2]} | Neutral: {logEventSplit[3]} | Criminal: {logEventSplit[1]}\nLAST: System: {lastLogEventSplit[0]} | Hostile: {lastLogEventSplit[2]} | Neutral: {lastLogEventSplit[3]} | Criminal: {lastLogEventSplit[1]}')
                            print(logMessage)
                    except IndexError:
                        continue
                    lastLogEvent = logEvent  
                    logCount += 1  
                    #set the current log to last log
            #clean exit on Ctrl + C
            except KeyboardInterrupt:
                print('TERMINATING: NoShot Discord Services')
                exit()
        else:
            logCount += 1
            lastLogEvent = logEvent    


def createLogs(eeSystem):
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
        return logFile


def clearShell():
    # for windows
    if name == 'nt':
        _ = system('cls')
    # for mac and linux(here, os.name is 'posix')
    else:
        _ = system('clear')


if __name__ == "__main__":
    argParser = argparse.ArgumentParser(
        description="This program monitors a Star System's population and optionally reports to discord"
    )
    argParser.add_argument('-r', '--run', metavar='run', required=True, choices={'log','report', 'service'}, help='The mode to run in. log == log to PC ONLY | report == report to discord')
    argParser.add_argument('-svc', '--service', metavar='service', choices={'discord'})
    argParser.add_argument('-s', '--system', metavar='system', help='System being monitored')
    argParser.add_argument('-c', '--channel', metavar='channel', help='Discord Channel Web Hook to report too (i.e https://discord.com/channel/webookhook).')
    argParser.add_argument('-bt', '--basicthreshold', metavar='basicthreshold', help='Population Change to report WARNING on to discord (i.e population change of one == 1', type=int)
    argParser.add_argument('-bg', '--basicgroup', metavar='basicgroup', help='Group to PING on WARNING at discord (i.e none, @here, @everyone, etc')
    argParser.add_argument('-at', '--alertthreshold', metavar='alertthreshold', help='Population Change to report ALERT on to discord (i.e population change of two == 3', type=int)
    argParser.add_argument('-ag', '--alertgroup', metavar='alertgroup', help='Group to PING on ALERT at discord (i.e none, @here, @everyone, etc')
    cmdArgs = argParser.parse_args()

    if cmdArgs.service == "discord":
        eeSystem = cmdArgs.system
        channelWebHook = cmdArgs.channel
        basicThreshold = cmdArgs.basicthreshold
        basicPingGroup = cmdArgs.basicgroup
        alertThreshold = cmdArgs.alertthreshold
        alertPingGroup = cmdArgs.alertgroup
        logFile = createLogs(str(eeSystem))
        watch_log(logFile)
    else:   
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
        logFile = createLogs(eeSystem)
        if cmdArgs.run == 'report':
            channelWebHook = input("Paste in (right click) discord channel webhook... : ")
            basicThreshold = input("What threshold should WARNING Discord messasge post at (change in neut/hostile population, i.e 1)? : ")
            basicPingGroup = input("Which group should be pinged at WARNING threshold (i.e none, @here, etc)? : ")
            alertThreshold = input("What threshold should ALERT Discord message post at (change in neut/hostile population, i.e 3)? : ")
            alertPingGroup = input("Which group should be pinged at ALERT threshold (i.e none, @here, etc)? : ")
            #start monitor process
            monitorProc = subprocess.Popen(r'py .\NoShot.py ' + f'-r service -svc discord -s {eeSystem} -c {channelWebHook} -bt {basicThreshold} -bg {basicPingGroup} -at {alertThreshold} -ag {alertPingGroup}', shell=True)
        clearShell()
        print(noShotArt)
        print(f'Click on the terminal/shell and press "Ctrl + C" to stop at anytime')
        print(f'Starting Monitor : System - "{eeSystem}"')
        if cmdArgs.run == 'report':
            print(f'REPORTING: Warning Threshold/Group: "{basicThreshold} / {basicPingGroup}" | ALERT Threshold/Group: "{alertThreshold} / {alertPingGroup}"')
        print(f"Logging to: {logFile}")
        print("\n")
        print("Using the left mouse btn, click and drag a rectangle over the population stats on the EE window")
        time.sleep(2)
        print("\n")
        #set capture log
        window = QtWidgets.QMainWindow()
        snipper = Snipper(window)
        snipped = snipper.show()
        #prep exit   
        sys.exit(app.exec_())