# This file will receive the payload and decide which parser to pass it to, 
# based on the first byte in the fixed header.

import sys
sys.path.append("generators")

from connack_parser import ConnackParser
from publish_parser import PublishParser
from disconnect_parser import DisconnectParser
from puback_parser import PubackParser
from pubrec_parser import PubrecParser
from pubrel_parser import PubrelParser

from connack import Connack
from publish import Publish
from connect import Connect
from puback import Puback
from pubrec import Pubrec
from pubrel import Pubrel
from disconnect import Disconnect

from packet import sendToBroker
import random

class ParseInitializer:
    def __init__(self, payload, protocol_version):
        assert type(payload) == str
        packetDict = {
            '2': ConnackParser, 
            '3': PublishParser,
            '4': PubackParser,
            '5': PubrecParser,
            '6': PubrelParser,
            'e': DisconnectParser}

        self.parser = packetDict[payload[0]](payload, protocol_version)
        
def test():
    protocol_version = random.randint(3, 5)
    connect = Connect(protocol_version)
    payload = Pubrel(protocol_version)
    sendToBroker("localhost", 1883, connect.toString() + payload.toString())
    parser = ParseInitializer(payload.toString(), protocol_version).parser
    g_fields = parser.G_fields
    h_fields = parser.H_fields
    print(g_fields)
    print(h_fields)
    

if __name__ == "__main__":
    test()