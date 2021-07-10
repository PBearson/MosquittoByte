from packet import Packet
import random

class Properties(Packet):

    def conditionalAppend(self, whitelist, code, packet):
        if whitelist is None or code in whitelist:
            self.appendPayloadRandomly(packet)

    def __init__(self, whitelist = None):
        super().__init__()

        self.payload_format_indicator = self.toBinaryData(0x01, 1, True)
        self.conditionalAppend(whitelist, 0x01, self.payload_format_indicator)

        self.message_expiry_interval = self.toBinaryData(0x02, 4, True)
        self.conditionalAppend(whitelist, 0x02, self.message_expiry_interval)

        self.content_type_length = random.randint(0, 30)
        self.content_type = self.toEncodedString(0x03, self.content_type_length)
        self.conditionalAppend(whitelist, 0x03, self.content_type)

        self.response_topic_length = random.randint(0, 30)
        self.response_topic = self.toEncodedString(0x08, self.response_topic_length)
        self.conditionalAppend(whitelist, 0x08, self.response_topic)

        self.correlation_data_length = random.randint(0, 30)
        self.correlation_data = self.toBinaryData(0x09, self.correlation_data_length)
        self.conditionalAppend(whitelist, 0x09, self.correlation_data)

        self.subscription_identifier_value = random.randint(0, 268435455)
        self.subscription_identifier = "0b" + self.toVariableByte("%x" % self.subscription_identifier_value)
        self.conditionalAppend(whitelist, 0x0b, self.subscription_identifier)

        self.session_expiry_interval = self.toBinaryData(0x11, 4, True)
        self.conditionalAppend(whitelist, 0x11, self.session_expiry_interval)

        self.assigned_client_identifier_length = random.randint(0, 30)
        self.assigned_client_identifier = self.toEncodedString(0x12, self.assigned_client_identifier_length)
        self.conditionalAppend(whitelist, 0x12, self.assigned_client_identifier)

        self.server_keepalive = self.toBinaryData(0x13, 2, True)
        self.conditionalAppend(whitelist, 0x13, self.server_keepalive)

        

        self.prependPayloadLength()