from parser import Parser

class SubackParser(Parser):
    def __init__(self, payload, protocol_version):
        super().__init__(payload, protocol_version)

        self.index = self.insertTwoBytesNoIdentifier("packet identifier", payload, self.index, False)

        if protocol_version == 5:
            self.parseProperties()

        while self.index < len(payload):
            self.index = self.insertByteListNoIdentifier("return code", payload, self.index, True)