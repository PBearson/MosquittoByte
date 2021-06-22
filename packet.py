import socket

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
