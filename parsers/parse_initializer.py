# This file will receive the payload and decide which parser to pass it to, 
# based on the first byte in the fixed header.

import sys
sys.path.append("generators")
from connack_parser import ConnackParser
from publish_parser import PublishParser
from disconnect_parser import DisconnectParser
from connack import Connack
from publish import Publish
from connect import Connect
from disconnect import Disconnect
from packet import sendToBroker
import random

class ParseInitializer:
    def __init__(self, payload, protocol_version):
        assert type(payload) == str
        if payload[0] == '2':
            self.parser = ConnackParser(payload, protocol_version)
        elif payload[0] == '3':
            self.parser = PublishParser(payload, protocol_version)
        elif payload[0] == 'e':
            self.parser = DisconnectParser(payload, protocol_version)

def test():
    protocol_version = random.randint(3, 5)
    connect = Connect(protocol_version)
    payload = Disconnect(protocol_version)
    sendToBroker("localhost", 1883, connect.toString() + payload.toString())
    parser = ParseInitializer(payload.toString(), protocol_version).parser
    g_fields = parser.G_fields
    h_fields = parser.H_fields
    print(g_fields)
    print(h_fields)
    

if __name__ == "__main__":
    test()