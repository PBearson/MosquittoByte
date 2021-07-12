from parser import Parser

class PublishParser(Parser):
    def __init__(self, payload, protocol_version):
        super().__init__(payload, protocol_version)
        print(payload, protocol_version)
