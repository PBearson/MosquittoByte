from packet import Packet

class Disconnect(Packet):
    def __init__(self):
        super().__init__()

if __name__ == "__main__":
    Packet().test(Disconnect)