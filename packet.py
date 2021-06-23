import socket
import string
import random

class Packet:
    def __init__(self):
        self.payload = []
        self.payload_length = 0

    def toList(self):
        l = []
        for p in self.payload:
            for n in p:
                if type(n) == list:
                    for x in n:
                        l.append(x)
                else:
                    l.append(n)
        return l
        
    def toString(self):
        return "".join(self.toList())

    def getByteLength(self):
        return len(self.toString()) / 2

    def toVariableByte(self, byteString):
        varByte = ""
        byteInt = int(byteString, 16)
        while True:
            encoded = int(byteInt % 128)
            byteInt = int(byteInt / 128)
            if byteInt > 0:
                encoded = encoded | 128

            varByte += "%.2x" % encoded
            if byteInt <= 0:
                break

        return varByte

    def getAlphanumHexString(self, stringLength):
        alphanum = string.ascii_letters + string.digits
        return ["%.2x" % ord(random.choice(alphanum)) for i in range(stringLength)]

    def sendToBroker(self, host, port):
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((host, port))
        try:
            s.send(bytearray.fromhex(self.toString()))
        except ValueError:
            print("Error caused by following payload:")
            print(self.toString())
            exit(0)
        s.close()