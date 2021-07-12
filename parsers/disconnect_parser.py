from parser import Parser

class DisconnectParser(Parser):

    def __init__(self, payload, protocol_version):
        super().__init__(payload, protocol_version)

        if protocol_version == 5:
            self.index = self.insertByteNoIdentifier("reason code", payload, self.index, True)

        if protocol_version == 5:
            self.parseProperties()