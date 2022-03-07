from PyQt5.uic import loadUi
from PyQt5 import QtWidgets, QtCore
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QDialog, QApplication, QMainWindow, QWidget
import socket
import sys
import pickle
import threading
import random
import time

HEADERSIZE = 10
MesObjList = []
HOST = "127.0.0.1"
PORT = 12000
users = []


def sendMes(mesObj, connObj):

    msg = pickle.dumps(mesObj)
    x = HEADERSIZE - len(msg) % 10
    msg = msg + bytes(f"{'':<{x}}", 'utf-8')
    msg = bytes(f"{len(msg):<{HEADERSIZE}}", 'utf-8')+msg
    connObj.send(msg)


def recvMes(connObj):

    full_msg = b""
    new_msg = True

    while True:
        msg = connObj.recv(HEADERSIZE)
        if new_msg:
            msglen = int(msg)
            new_msg = False

        else:
            full_msg += msg

        if len(full_msg) == msglen:
            full_msg = pickle.loads(full_msg)
            return full_msg


def generatePortForListening():

    global PORT
    PORT = random.randint(12000, 13000)
    print(PORT)


def generateUserId():

    userid = random.randint(1, 2000)
    return userid


def startMesListeningThread(connectionObj, userid):
    try:
        threadObj = listenForUserMessages(connectionObj, userid)
        threadObj.setDaemon(True)
        threadObj.start()
    except Exception as e:
        print("ERROR CREATING THREAD : " + str(e))
        sys.exit(1)


def startConnListeningThread():
    try:
        threadObj = listenForConnReq()
        threadObj.setDaemon(True)
        threadObj.start()
    except Exception as e:
        print("ERROR CREATING THREAD : " + str(e))
        sys.exit(1)


def startServerThread(host, port, userName):
    try:
        threadObj = ListenToServer(host, port, userName)
        threadObj.setDaemon(True)
        threadObj.start()
    except Exception as e:
        print("ERROR CREATING THREAD : " + str(e))
        sys.exit(1)


class Signals(QWidget):

    signal1 = pyqtSignal(object, object, object)
    signal2 = pyqtSignal()
    guiTitle = pyqtSignal(str)
    signal3 = pyqtSignal()
    closeThreadSignal = pyqtSignal()
    addUserSignal = pyqtSignal(str)
    removeUserSignal = pyqtSignal(int)


class User():
    def __init__(self, userName, userid, userListeningAddress):
        self.userName = userName
        self.userid = userid
        self.userListeningAddress = userListeningAddress


class Messages():
    def __init__(self, userid):
        self.message = []
        self.userid = userid  # userAddress(ip,port) used as userID


class OpeningWindow(QDialog):
    def __init__(self):

        super(OpeningWindow, self).__init__()
        loadUi(".\openingDialog.ui", self)
        self.submitButton.clicked.connect(self.submitButtonClicked)

    def submitButtonClicked(self):
        # input
        [host, port, userName] = self.input()
        # start new thread for server communication
        startServerThread(host, port, userName)
        # opening mainwindow
        self.openMainWindow()

    def input(self):

        userName = self.nameLineEdit.text()
        host = self.ipLineEdit.text()
        port = self.portLineEdit.text()
        return [host, port, userName]

    def openMainWindow(self):

        widget.addWidget(mainWindow)
        widget.setCurrentIndex(widget.currentIndex() + 1)
        widget.setGeometry(350, 130, 700, 650)


class MainWindow(QMainWindow):

    def __init__(self):

        super(MainWindow, self).__init__()
        loadUi(".\mainWindow.ui", self)
        self.children = []

        self.userListWidget.itemClicked.connect(self.requestUser)
        signals.guiTitle.connect(self.setUserName)
        signals.signal1.connect(self.incomingConn)
        signals.addUserSignal.connect(self.addUser)
        signals.removeUserSignal.connect(self.removeUser)

    def requestUser(self, userName):

        index = self.userListWidget.currentRow()
        messageWindow = MessageWindow(self, users[index], MesObjList[index])
        messageWindow.show()

        self.children.append(messageWindow)
        messageWindow.reqConnection()

    def incomingConn(self, user, mesObj, connectionObj):

        messageWindow = MessageWindow(self, user, mesObj)
        messageWindow.show()

        self.children.append(messageWindow)

        messageWindow.acceptConnection(connectionObj)
        messageWindow.communication()

    def setUserName(self, userName):

        self.userName.setText(userName)

    def addUser(self, userName):

        self.userListWidget.addItem(userName)

    def removeUser(self, index):

        self.userListWidget.takeItem(index)


class MessageWindow(QMainWindow):
    def __init__(self, parent, communicationUser, mesObj):

        super(MessageWindow, self).__init__()
        loadUi(".\messageWindow.ui", self)
        self.parent = parent
        self.communicationUser = communicationUser
        self.mesObj = mesObj

        self.userName.setText(communicationUser.userName)

        signals.signal2.connect(self.printMessage)
        signals.signal3.connect(self.closeIfUserClosed)

        self.flag = True

    def reqConnection(self):

        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.connect(self.communicationUser.userListeningAddress)
        self.connObj = self.s

        mes = recvMes(self.connObj)

        self.sendUserId()
        self.connType = "Request"

        if(mes["type"] == "accepted"):
            self.communication()
        if(mes["type"] == "rejected"):
            print("Connection rejected")
            self.s.close()

    def acceptConnection(self, connObj):

        self.connObj = connObj
        self.connType = "Accept"

    def communication(self):
        startMesListeningThread(self.connObj, self.mesObj)
        self.sendButton.clicked.connect(self.sendMessage)

    def sendUserId(self):

        message = {"userId": selfUserId}
        sendMes(message, self.s)

    def sendMessage(self):

        mes = self.messageLineEdit.text()
        self.messageLineEdit.clear()

        message = self.setMessageType(mes)
        self.mesObj.message.append(message)
        self.printMessage()
        sendMes(message, self.connObj)

    def setMessageType(self, mes):

        message = {"message": mes, "type": "send"}
        return message

    def printMessage(self):
        self.userMessageListWidget.clear()
        self.yourMessageListWidget.clear()

        for mes in self.mesObj.message:
            if(mes["type"] == "send"):
                self.userMessageListWidget.addItem("")
                self.yourMessageListWidget.addItem(mes["message"])
            if(mes["type"] == "recieve"):
                self.yourMessageListWidget.addItem("")
                self.userMessageListWidget.addItem(mes["message"])

    def closeEvent(self, event):
        self.parent.children.remove(self)
        signals.closeThreadSignal.emit()
        try:
            sendMes({"type": "closeConn"}, self.connObj)
        except:
            pass  # if socket is already closed form other user
        if self.connType == "Request":
            self.s.close()
        if self.flag:
            self.close()

    def closeIfUserClosed(self):
        self.flag = False
        self.close()


class listenForUserMessages(threading.Thread):
    def __init__(self, connObj, mesObj):
        threading.Thread.__init__(self)
        self.connObj = connObj
        self.mesObj = mesObj
        self.isAlive = True
        signals.closeThreadSignal.connect(self.closeThread)

    def run(self):
        while self.isAlive:
            try:
                mes = recvMes(self.connObj)
            except:
                break
            if(mes["type"] == "closeConn"):
                sendMes({"type": "unblock"}, self.connObj)
                signals.signal3.emit()
                time.sleep(0.5)
            if(mes["type"] == "send"):
                message = self.invertMesType(mes)
                message["con"] = self.connObj
                signals.signal2.emit()
                self.mesObj.message.append(message)

    def invertMesType(self, mes):
        currentType = mes["type"]
        if(currentType == "send"):
            currentType = "recieve"
            message = {"message": mes["message"], "type": currentType}
            return message

    def closeThread(self):
        print("Thread closed")
        self.isAlive = False

class ListenToServer(threading.Thread):
    def __init__(self, host, port, userName):

        threading.Thread.__init__(self)

        self.host = "127.0.0.1"  # host
        self.port = 12345  # int(port)
        self.userName = userName
        self.userid = selfUserId

        try:
            self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        except Exception as e:
            print("ERROR CREATING SOCKET : " + e)

    def sendUserName(self):

        data = {"name": self.userName,
                "listeningPort": PORT, "userid": self.userid}
        sendMes(data, self.s)

    def checkIfServerAlive(self):
        try:
            check = {"type": "isServerAlive"}
            # to generate exception if server is down
            sendMes(check, self.s)

        except Exception as e:
            if (str(e) == "[Errno 32] Broken pipe"):
                print("SERVER IS DOWN")  # popup
            else:
                print("SERVER ERROR: " + str(e))  # popup
            sys.exit(1)

    def run(self):

        signals.guiTitle.emit(self.userName)
        # connect to sever
        try:
            self.s.connect((self.host, self.port))
        except ConnectionRefusedError as e:
            print("CONNECTION REFUSED ERROR : " + str(e))
            sys.exit(1)
        except Exception as e:
            print("ERROR CONNECTING TO SERVER : " + str(e))
            sys.exit(1)

        self.sendUserName()

        # listen to sever for new users
        while True:
            try:
                data = recvMes(self.s)
            except:
                print("ERROR RECIEVING DATA FROM SERVER")
                sys.exit(1)

            if(data["type"] == "addUser"):
                self.addUser(data)
            if(data["type"] == "removeUser"):
                self.removeUser(data)

            self.checkIfServerAlive()

    def addUser(self, data):
        userNameList = data["NameList"]
        userListeningAddressList = data["ListeningAddressList"]
        useridList = data["idList"]
        count = 0

        length = len(userNameList)
        while count < length:
            userName = userNameList[count]
            userListeningAddress = userListeningAddressList[count]
            userid = useridList[count]
            users.append(User(userName, userid, userListeningAddress))
            signals.addUserSignal.emit(userName)
            MesObjList.append(Messages(userid))
            count += 1

    def removeUser(self, data):
        userName = data["Name"]
        userid = data["id"]
        index = 0
        for user in users:
            if(user.userid == userid):
                signals.removeUserSignal.emit(index)
                users.remove(user)
                MesObjList.pop(index)
                index += 1

    def __del__(self):
        self.s.close()


class listenForConnReq(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.bind((HOST, PORT))

    def run(self):
        self.s.listen()
        while True:
            connectionObj, userAddress = self.s.accept()

            self.sendAcceptedMessage(connectionObj)
            userId = self.recvUserId(connectionObj)
            user = self.findUser(userId)
            mesObj = self.findMessageObj(userId)

            signals.signal1.emit(user, mesObj, connectionObj)

    def findUser(self, userId):
        for user in users:
            if(user.userid == userId):
                return user

    def findMessageObj(self, userId):
        for mesObj in MesObjList:
            if(mesObj.userid == userId):
                return mesObj

    def sendAcceptedMessage(self, connectionObj):
        mes = {"type": "accepted"}
        sendMes(mes, connectionObj)

    def recvUserId(self, connectionObj):
        mes = recvMes(connectionObj)
        userId = mes["userId"]
        return userId


app = QApplication(sys.argv)

widget = QtWidgets.QStackedWidget()

generatePortForListening()
selfUserId = generateUserId()

signals = Signals()
openingWindow = OpeningWindow()
mainWindow = MainWindow()

widget.addWidget(openingWindow)
widget.setGeometry(500, 250, 400, 400)
widget.show()

startConnListeningThread()

sys.exit(app.exec_())
