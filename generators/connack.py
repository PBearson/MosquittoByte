from packet import Packet
from connect import Connect 
import time
import random

class ConnackProperties(Packet):
    def __init__(self):
        super().__init__()

        self.session_expiry_interval = self.toBinaryData(0x11, 4, True)
        self.appendPayloadRandomly(self.session_expiry_interval)

        self.receive_maximum = self.toBinaryData(0x21, 2, True, 8, 1)
        self.appendPayloadRandomly(self.receive_maximum)

        self.maximum_qos = self.toBinaryData(0x24, 1, True, 1)
        self.appendPayloadRandomly(self.maximum_qos)

        self.retain_available = self.toBinaryData(0x25, 1, True, 1)
        self.appendPayloadRandomly(self.retain_available)

        self.maximum_packet_size = self.toBinaryData(0x27, 4, True, 8, 1)
        self.appendPayloadRandomly(self.maximum_packet_size)

        self.assigned_client_id_length = random.randint(1, 30)
        self.assigned_client_id = self.toEncodedString(0x12, self.assigned_client_id_length)
        self.appendPayloadRandomly(self.assigned_client_id)

        self.topic_alias_maximum = self.toBinaryData(0x22, 2, True)
        self.appendPayloadRandomly(self.topic_alias_maximum)

        self.reason_string_length = random.randint(1, 30)
        self.reason_string = self.toEncodedString(0x1f, self.reason_string_length)
        self.appendPayloadRandomly(self.reason_string)

        self.user_property_name_length = random.randint(1, 30)
        self.user_property_value_length = random.randint(1, 30)
        self.user_property = self.toEncodedStringPair(0x26, self.user_property_name_length, self.user_property_value_length)
        self.appendPayloadRandomly(self.user_property)

        self.wildcard_subscription_available = self.toBinaryData(0x28, 1, True, 1)
        self.appendPayloadRandomly(self.wildcard_subscription_available)

        self.subscription_identifiers_available = self.toBinaryData(0x29, 1, True, 1)
        self.appendPayloadRandomly(self.subscription_identifiers_available)

        self.shared_subscription_available = self.toBinaryData(0x2a, 1, True, 1)
        self.appendPayloadRandomly(self.shared_subscription_available)

        self.server_keepalive = self.toBinaryData(0x13, 2, True)
        self.appendPayloadRandomly(self.server_keepalive)

        self.response_information_length = random.randint(1, 30)
        self.response_information = self.toEncodedString(0x1a, self.response_information_length)
        self.appendPayloadRandomly(self.response_information)

        self.server_reference_length = random.randint(1, 30)
        self.server_reference = self.toEncodedString(0x1c, self.server_reference_length)
        self.appendPayloadRandomly(self.server_reference)

class ConnackVariableHeader(Packet):
    def __init__(self):
        super().__init__()

        self.acknowledgement_flags = self.toBinaryData(None, 1, True, 1)
        self.return_code = self.toBinaryData(None, 1, True)
        self.connack_properties = ConnackProperties()


        self.payload = [self.acknowledgement_flags, self.return_code, self.connack_properties.toList()]

class Connack(Packet):
    def __init__(self):
        super().__init__()

        self.fixed_header = ['20']
        self.variable_header = ConnackVariableHeader()
        remaining_length = self.toVariableByte("%x" % self.variable_header.getByteLength())

        self.payload = [self.fixed_header, remaining_length, self.variable_header.toList()]

if __name__ == "__main__":
    Packet().test(Connack)