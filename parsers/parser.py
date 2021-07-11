class Parser:

    def indexToByte(self, index = None, numBytes = 1):
        if index is None:
            index = self.index
        return self.payload[index:index+(numBytes * 2)]

    def __init__(self, payload, protocol_version):
        self.payload = payload
        self.protocol_version = protocol_version
        self.G_fields = {}
        self.H_fields = {}
        self.index = 0

        # Fixed header always goes in G fields
        fixed_header = self.indexToByte()
        self.G_fields["fixed header"] = fixed_header

        # Skip over remaining length field
        self.index = 2
        while int(self.indexToByte(), 16) > 127:
            self.index += 2
        self.index += 2

        