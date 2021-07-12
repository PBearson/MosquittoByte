from parser import Parser

class ConnackParser(Parser):
    def __init__(self, payload, protocol_version):
        super().__init__(payload, protocol_version)

        self.index = self.insertByteNoIdentifier("acknowledge flags", payload, self.index, True)

        self.index = self.insertByteNoIdentifier("reason code", payload, self.index, True)

        if protocol_version == 5:
            self.parseProperties()