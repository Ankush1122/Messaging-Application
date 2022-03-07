from PyQt5.uic import loadUi
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtWidgets import QDialog, QApplication, QMainWindow, QWidget
import socket
import sys
import pickle
import threading
import random


class MainWindow(QMainWindow):
    def __init__(self):
        super(MainWindow, self).__init__()
        loadUi("mainWindow.ui", self)
        self.children = []
        self.userListWidget.itemClicked.connect(self.requestUser)

    def requestUser(self):
        messageWindow = MessageWindow(self)  # users[index],MesObjList[index])
        messageWindow.show()
        print(len(self.children))
        self.children.append(messageWindow)
        # messageWindow.reqConnection()


class MessageWindow(QMainWindow):
    def __init__(self, parent):  # ,communicationUser,mesObj):
        super(MessageWindow, self).__init__()
        loadUi("messageWindow2.ui", self)
        self.parent = parent
        #self.communicationUser = communicationUser
        #self.mesObj = mesObj

    def closeEvent(self, event):
        print(event)
        self.parent.children.remove(self)
        self.close()


app = QApplication(sys.argv)


mainWindow = MainWindow()
mainWindow.userListWidget.addItem('asdas')
mainWindow.userListWidget.addItem('sdfsdfsdf')
mainWindow.show()


sys.exit(app.exec_())
