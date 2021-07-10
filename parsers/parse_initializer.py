# This file will receive the payload and decide which parser to pass it to, based on the first byte in the fixed header.

import sys
sys.path.append("generators")
from connack_parser import ConnackParser
from connack import Connack

class ParseInitializer:
    def __init__(self, payload):
        assert type(payload) == str
        if payload[0] == '2':
            self.parser = ConnackParser(payload)
        
def test():
    connack = Connack()
    parser = ParseInitializer(connack.toString()).parser
    

if __name__ == "__main__":
    test()