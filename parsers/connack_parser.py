from parser import Parser

class ConnackParser(Parser):
    def __init__(self, payload, protocol_version):
        super().__init__(payload, protocol_version)

        self.G_fields["acknowledge flags"] = self.indexToByte()
        self.index += 2

        self.G_fields["reason code"] = self.indexToByte()
        self.index += 2

        if protocol_version == 5:
            self.parseProperties()