import socket
import threading
import json
import sys
import PyQt5

HOST = "0.0.0.0"
PORT = 12345


class Communication(threading.Thread):
    def __init__(self, connectionObj, clientAddress, connObjList):
        threading.Thread.__init__(self)
        self.connectionObj = connectionObj
        self.connObjList = connObjList
        self.ipAdd, self.portNo = clientAddress
        self.portNo = str(self.portNo)

    def run(self):
        try:
            data = self.connectionObj.recv(1024).decode()
        except Exception as e:
            print("ERROR RECIEVING DATA : " + str(e))
            sys.exit(1)
        data = json.loads(data)
        self.clientName = data["name"]
        self.broadCast(data["mes"], self.connObjList)             #Join Message
        while True:
            try:
                data = self.connectionObj.recv(1024).decode()
            except Exception as e:
                print("ERROR RECIEVING DATA : " + str(e))
                sys.exit(1)
            data = json.loads(data)
            if (data["controlType"] == "regularMes"):
                self.broadCast(self.clientName + " : " +
                               data["mes"], self.connObjList)
            if (data["controlType"] == "exitMes"):
                self.broadCast(data["mes"], self.connObjList)
                break
        self.removeClient()

    def removeClient(self):
        self.connObjList.remove(self.connectionObj)

    def broadCast(self, mes, list):
        count = 0
        if list is None:
            length = 0
        else:
            length = len(list)
        while count < length:
            if list[count] is not self.connectionObj:
                self.sendMessage(mes, list[count])
            count += 1

    def sendMessage(self, mes, connectionObj):
        try:
            connectionObj.send(mes.encode())
        except Exception as e:
            print("ERROR SENDING DATA : " + str(e))
            sys.exit(1)


class Server:
    def __init__(self):
        print("SERVER PROGRAM")
        try:
            self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.s.bind((HOST, PORT))
        except Exception as e:
            print("SOCKET ERROR : " + str(e))
            sys.exit(1)
        self.connObjList = []

    def waitForClient(self):
        try:
            self.s.listen()
        except Exception as e:
            print("ERROR LISTENING FOR CLIENT : " + str(e))
            sys.exit(1)

        while True:
            try:
                connectionObj, clientAddress = self.s.accept()
            except KeyboardInterrupt:
                print("DO YOU REALLY WANT TO CLOSE SERVER ?")
                confirm = input("ENTER 0 TO CLOSE 1 TO STAY : ")
                if(confirm):
                    sys.exit(1)
            except Exception as e:
                print("ERROR ACCEPTING CONNECTION OBJECT AND CLIENT ADDRESS : " + str(e))
                sys.exit(1)
            self.addClient(connectionObj)
            self.startNewThread(connectionObj, clientAddress)

    def addClient(self, connectionObj):
        self.connObjList.append(connectionObj)

    def startNewThread(self, connectionObj, clientAddress):
        try:
            threadObj = Communication(
                connectionObj, clientAddress, self.connObjList)
            threadObj.setDaemon(True)
            threadObj.start()
        except Exception as e:
            print("ERROR CREATING THREAD : " + str(e))
            sys.exit(1)

    def __del__(self):
        self.s.close()


def main():
    mainThread = Server()
    mainThread.waitForClient()


if __name__ == "__main__":
    main()
