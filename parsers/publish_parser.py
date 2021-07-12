from parser import Parser

class PublishParser(Parser):

    # Given the fixed header, return the QoS version, defined by bits 1 and 2.
    def getQoSVersion(self, fixed_header):
        return int(bin(fixed_header)[-3:-1], 2)

    def __init__(self, payload, protocol_version):
        super().__init__(payload, protocol_version)

        self.index = self.insertStringNoIdentifier("topic name", payload, self.index, False)

        fixed_header = int(self.G_fields["fixed header"], 16)
        if self.getQoSVersion(fixed_header) > 0:
            self.index = self.insertTwoBytesNoIdentifier("packet identifier", payload, self.index, False)

        if protocol_version == 5:
            self.parseProperties()

        self.H_fields["message"] = payload[self.index:]