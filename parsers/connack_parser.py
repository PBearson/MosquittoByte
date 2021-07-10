from parser import Parser

class ConnackParser(Parser):
    def __init__(self, payload):
        super().__init__(payload)
        print(payload)
