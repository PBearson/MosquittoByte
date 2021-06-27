from packet import Packet
import random

class DisconnectProperties(Packet):
    def __init__(self):
        super().__init__()

        self.session_expiry_interval = self.toBinaryData(0x11, 4, True)
        self.appendPayloadRandomly(self.session_expiry_interval)

        self.reason_string_length = random.randint(1, 30)
        self.reason_string = self.toEncodedString(0x1f, self.reason_string_length)
        self.appendPayloadRandomly(self.reason_string)

        self.user_property_name_length = random.randint(1, 30)
        self.user_property_value_length = random.randint(1, 30)
        self.user_property = self.toEncodedStringPair(0x25, self.user_property_name_length, self.user_property_value_length)
        self.appendPayloadRandomly(self.user_property)

        self.server_reference_length = random.randint(1, 30)
        self.server_reference = self.toEncodedString(0x1c, self.server_reference_length)
        self.appendPayloadRandomly(self.server_reference)

        self.prependPayloadLength()

class DisconnectVariableHeader(Packet):
    def __init__(self):
        super().__init__()

        self.reason_code = self.toBinaryData(None, 1, True)
        self.payload.append(self.reason_code)

        self.properties = DisconnectProperties()
        self.payload.append(self.properties.toString())
    

class Disconnect(Packet):
    def __init__(self):
        super().__init__()

        self.fixed_header = ['e0']
        self.variable_header = DisconnectVariableHeader()

        remaining_length = self.variable_header.getByteLength()

        self.payload = [self.fixed_header, self.toVariableByte("%x" % remaining_length), self.variable_header.toString()]

if __name__ == "__main__":
    Packet().test(Disconnect)