# This file will receive the payload and decide which parser to pass it to, 
# based on the first byte in the fixed header.

from connack_parser import ConnackParser
from publish_parser import PublishParser
from disconnect_parser import DisconnectParser
from puback_parser import PubackParser
from pubrec_parser import PubrecParser
from pubrel_parser import PubrelParser
from pubcomp_parser import PubcompParser
from subscribe_parser import SubscribeParser
from suback_parser import SubackParser

class ParseInitializer:
    def __init__(self, payload, protocol_version):
        assert type(payload) == str
        packetDict = {
            '2': ConnackParser, 
            '3': PublishParser,
            '4': PubackParser,
            '5': PubrecParser,
            '6': PubrelParser,
            '7': PubcompParser,
            '8': SubscribeParser,
            '9': SubackParser,
            'e': DisconnectParser}

        self.parser = packetDict[payload[0]](payload, protocol_version)