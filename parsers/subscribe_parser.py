from parser import Parser

class SubscribeParser(Parser):
    def __init__(self, payload, protocol_version):
        super().__init__(payload, protocol_version)

        self.index = self.insertTwoBytesNoIdentifier("packet identifier", payload, self.index, False)

        if protocol_version == 5:
            self.parseProperties()

        while self.index < len(payload):
            self.index = self.insertStringListNoIdentifier("topic", payload, self.index, False)
            self.index = self.insertByteListNoIdentifier("subscription options", payload, self.index, True)