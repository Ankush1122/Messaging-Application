import socket
import pickle
import sys
import threading
import time

HOST =  "0.0.0.0"
PORT = 12345
HEADERSIZE = 10

connObjList = []
userListeningAddressList = []
userNameList = []
useridList = []


def startCheckThread():
    try:
        checkThread = CheckIfUserAlive()
        checkThread.setDaemon(True)
        checkThread.start()
    except Exception as e:
        print("ERROR CREATING THREAD : " + str(e))
        sys.exit(1)


def send(mesObj, connObj):
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


class Communication():
    def __init__(self):
        print("SERVER PROGRAM")
        print("PORT NUMBER : " , PORT)
        try:
            self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.s.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.s.bind((HOST, PORT))
        except Exception as e:
            print("SOCKET ERROR : " + str(e))
            sys.exit(1)

    def waitForUser(self):
        try:
            self.s.listen(3)
        except Exception as e:
            print("ERROR LISTENING FOR USER : " + str(e))
            sys.exit(1)

        while True:
            try:
                connectionObj, userAddress = self.s.accept()
                data = recvMes(connectionObj)
                userName = data["name"]
                userListeningPort = data["listeningPort"]
                userid = data["userid"]
                userListeningAddress = (userAddress[0], userListeningPort)
            except KeyboardInterrupt:
                print("DO YOU REALLY WANT TO CLOSE SERVER ?")
                confirm = input("ENTER 0 TO CLOSE 1 TO STAY : ")
                if(confirm):
                    sys.exit(1)
            except Exception as e:
                print("ERROR ACCEPTING CONNECTION OBJECT AND CLIENT ADDRESS : " + str(e))
                sys.exit(1)

            self.informNewUser(connectionObj)
            self.informOldUsers(userListeningAddress, userName, userid)
            self.addUser(connectionObj, userListeningAddress, userName, userid)

    def addUser(self, connectionObj, userListeningAddress, userName, userid):
        print(userName, " connected")
        connObjList.append(connectionObj)
        userListeningAddressList.append(userListeningAddress)
        userNameList.append(userName)
        useridList.append(userid)

    def informNewUser(self, connObj):
        addMes = {
            "ListeningAddressList": userListeningAddressList,
            "NameList": userNameList,
            "idList": useridList,
            "type": "addUser"
        }

        send(addMes, connObj)

    def informOldUsers(self, Address, Name, userid):
        userListeningAddress = [Address]
        userName = [Name]
        userid = [userid]
        addMes = {
            "ListeningAddressList": userListeningAddress,
            "NameList": userName,
            "idList": userid,
            "type": "addUser"
        }
        for connObj in connObjList:
            send(addMes, connObj)

    def __del__(self):
        self.s.close()


class CheckIfUserAlive(threading.Thread):
    def __init__(self):
        threading.Thread.__init__(self)

    def run(self):
        checkMes = {"mes": "check", "type": "checkMes"}
        while True:
            try:
                count = 0
                length = len(connObjList)
                while count < length:
                    send(checkMes, connObjList[count])
                    count += 1
            except:
                self.removeUser(count)
            time.sleep(1)

    def removeUser(self, count):
        removeMes = {
            "id": useridList[count], "Name": userNameList[count], "type": "removeUser"}
        userListeningAddressList.pop(count)
        userNameList.pop(count)
        useridList.pop(count)
        connObjList.pop(count)
        for user in connObjList:
            send(removeMes, user)


mainThread = Communication()
startCheckThread()
mainThread.waitForUser()


"""
removeUser : 1)id 2)Name 3)Type
addUser :   "ListeningAddressList": userListeningAddress,
            "NameList": userName,
            "idList": userid,
            "type": "addUser"


"""
