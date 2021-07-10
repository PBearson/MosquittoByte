from packet import Packet

class Properties(Packet):

    def conditionalAppend(self, whitelist, code, packet):
        if whitelist is None or code in whitelist:
            self.appendPayloadRandomly(packet)

    def __init__(self, whitelist = None, useWhitelist = True):
        super().__init__()

        self.payload_format_indicator = self.toBinaryData(0x01, 1, True)
        self.conditionalAppend(whitelist, 0x01, self.payload_format_indicator)

        self.message_expiry_interval = self.toBinaryData(0x02, 4, True)
        self.conditionalAppend(whitelist, 0x02, self.message_expiry_interval)

        self.session_expiry_interval = self.toBinaryData(0x11, 4, True)
        self.conditionalAppend(whitelist, 0x11, self.session_expiry_interval)

        self.prependPayloadLength()