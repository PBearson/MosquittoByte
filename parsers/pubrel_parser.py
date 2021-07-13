from parser import Parser

class PubrelParser(Parser):
    def __init__(self, payload, protocol_version):
        super().__init__(payload, protocol_version)

        self.index = self.insertTwoBytesNoIdentifier("packet identifier", payload, self.index, False)

        if protocol_version == 5:
            self.index = self.insertByteNoIdentifier("reason code", payload, self.index, True)

            self.parseProperties()