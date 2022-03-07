import socket
import threading
import sys
import os
import json

class listen(threading.Thread):
    def __init__(self, s):
        threading.Thread.__init__(self)
        self.s = s

    def run(self):
        while True:
            try:
                data = self.s.recv(1024).decode()
                check = '{ "controlType": "isServerAlive" }'
                self.s.send(check.encode())  #to generate exception if server is down
            except Exception as e:
                if (str(e) == "[Errno 32] Broken pipe"):
                    print("SERVER IS DOWN")
                else:
                    print("ERROR LISTENING DATA : " + str(e))
                self.s.close()
                os._exit(1)
            print(data)


class Client:
    def __init__(self):
        try:
            self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        except Exception as e:
            print("ERROR CREATING SOCKET : " + str(e))
            sys.exit(1)
        print("CLIENT PROGRAM")

    def communication(self, host, port, clientName):
        try:
            self.s.connect((host, port))
            print(self.s)

        except ConnectionRefusedError as e:
            print("CONNECTION REFUSED ERROR : " + str(e))
            sys.exit(1)
        except Exception as e:
            print("ERROR CONNECTING TO SERVER : " + str(e))
            sys.exit(1)

        self.startNewThread()

        data = {
            "name": clientName,
            "mesType": "broadcast",
            "controlType": "joinMes",
            "mes": clientName + " ( " + host + " , " + str(port) + " ) " + " JOINED OUR NETWORK"
        }
        data = json.dumps(data)
        self.s.send(data.encode())

        while True:
            try:
                mes = input()
                data = {
                    "name": clientName,
                    "mesType": "broadcast",
                    "controlType": "regularMes",
                    "mes": mes
                }
                data = json.dumps(data)
                self.s.send(data.encode())

            except KeyboardInterrupt:
                print("DO YOU REALLY WANT TO EXIT ?")
                confirm = input(
                    "ENTER 0 TO CLOSE 1 TO STAY : ")
                if (confirm):
                    data = {
                        "name": clientName,
                        "mesType": "broadcast",
                        "controlType": "exitMes",
                        "mes":  clientName + " ( " + host + " , " + str(port) + " ) " + " EXITS OUR NETWORK"
                    }
                    data = json.dumps(data)
                    self.s.send(data.encode())
                    sys.exit(1)
            except Exception as e:
                print("ERROR SENDING DATA : " + str(e))
                sys.exit(1)

    def startNewThread(self):
        try:
            threadObj = listen(self.s)
            threadObj.setDaemon(True)
            threadObj.start()
        except Exception as e:
            print("ERROR OCCURED WHILE CREATING THREAD : " + str(e))
            sys.exit(1)

    def __del__(self):
        self.s.close()


def inputForClient():
    host = input("ENTER IP ADDRESS OF SERVER : ")
    port = int(input("ENTER PORT NUMBER OF SERVER : "))
    clientName = input("ENTER YOUR NAME : ")
    return [host, port, clientName]


def main():
    obj = Client()
    [host, port, clientName] = inputForClient()
    obj.communication(host, port, clientName)


if __name__ == "__main__":
    main()
