from packet import Packet
from connect import Connect 
import time
import random

class ConnackProperties(Packet):
    def __init__(self):
        super().__init__()

        self.session_expiry_interval = self.toBinaryData(0x11, 4, True)
        self.receive_maximum = self.toBinaryData(0x21, 2, True, 8, 1)
        self.maximum_qos = self.toBinaryData(0x24, 1, True, 1)
        self.retain_available = self.toBinaryData(0x25, 1, True, 1)
        self.maximum_packet_size = self.toBinaryData(0x27, 4, True, 8, 1)
        self.assigned_client_id_length = random.randint(1, 30)
        self.assigned_client_id = self.toEncodedString(0x12, self.assigned_client_id_length)
        self.topic_alias_maximum = self.toBinaryData(0x22, 2, True)

        self.payload_length = 5 + 3 + 4 + 4 + 5 + 3 + self.assigned_client_id_length
        self.payload = [self.toVariableByte("%x" % self.payload_length), self.session_expiry_interval, self.receive_maximum, self.maximum_qos, self.retain_available, self.maximum_packet_size, self.assigned_client_id]


class ConnackVariableHeader(Packet):
    def __init__(self, connect_packet):
        super().__init__()

        self.acknowledgement_flags = self.toBinaryData(None, 1, True, 1)
        self.return_code = self.toBinaryData(None, 1, True)
        self.connack_properties = ConnackProperties()


        self.payload = [self.acknowledgement_flags, self.return_code, self.connack_properties.toList()]
        self.payload_length = 2 + self.connack_properties.payload_length - 3

class Connack(Packet):
    def __init__(self, connect_packet = None):
        super().__init__()

        if connect_packet is None:
            connect_packet = Connect()
        
        self.fixed_header = ['20']
        self.variable_header = ConnackVariableHeader(connect_packet)
        self.payload_length = 1 + self.variable_header.payload_length

        self.payload = [self.fixed_header, "%.2x" % (self.payload_length - 1), self.variable_header.toList()]


def test():
    host = "127.0.0.1"
    port = 1883

    for i in range(100):
        packet = Connack()
        packet.sendToBroker(host, port)
        print(packet.toString())
        time.sleep(0.01)

if __name__ == "__main__":
    test()