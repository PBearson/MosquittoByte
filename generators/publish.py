from connect import Connect
from packet import Packet
from packet import packetTest
import random

class PublishFixedHeader(Packet):
    def __init__(self):
        super().__init__()

        self.dup = random.getrandbits(1)
        self.qos = min(2, random.getrandbits(2))
        self.retain = random.getrandbits(1)

        payload_tmp = [0b11, self.dup, self.qos & 1, (self.qos >> 1) & 1, self.retain]

        self.payload = ["%.2x" % int("".join(bin(s)[2:] for s in payload_tmp), 2)]

class PublishProperties(Packet):
    def __init__(self):
        super().__init__()

        self.payload_format_indicator = self.toBinaryData(0x01, 1, True, 1)
        self.appendPayloadRandomly(self.payload_format_indicator)

        self.message_expiry_interval = self.toBinaryData(0x02, 4, True)
        self.appendPayloadRandomly(self.message_expiry_interval)

        self.topic_alias = self.toBinaryData(0x23, 2, True, 8)
        self.appendPayloadRandomly(self.topic_alias)

        self.response_topic_length = random.randint(0, 30)
        self.response_topic = self.toEncodedString(0x08, self.response_topic_length)
        self.appendPayloadRandomly(self.response_topic)

        self.correlation_data_length = random.randint(0, 30)
        self.correlation_data = self.toBinaryData(0x09, self.correlation_data_length)
        self.appendPayloadRandomly(self.correlation_data)

        self.user_property_name_length = random.randint(0, 30)
        self.user_property_value_length = random.randint(0, 30)
        self.user_property = self.toEncodedStringPair(0x26, self.user_property_name_length, self.user_property_value_length)
        self.appendPayloadRandomly(self.user_property)

        self.subscription_identifier_value = random.randint(0, 268435455)
        self.subscription_identifier = "0b" + self.toVariableByte("%x" % self.subscription_identifier_value)
        self.appendPayloadRandomly(self.subscription_identifier)

        self.content_type_length = random.randint(0, 30)
        self.content_type = self.toEncodedString(0x03, self.content_type_length)
        self.appendPayloadRandomly(self.content_type)

        self.prependPayloadLength()

class PublishVariableHeader(Packet):
    def __init__(self, qos, protocol_version):
        super().__init__()

        self.topic_name_length = random.randint(0, 30)
        self.topic_name = self.toEncodedString(None, self.topic_name_length)
        self.payload.append(self.topic_name)

        self.packet_id = self.toBinaryData(None, 2, True, 8)
        if qos > 0:
            self.payload.append(self.packet_id)

        self.properties = PublishProperties()
        if protocol_version == 5:
            self.payload.append(self.properties.toString())
    

class Publish(Packet):
    def __init__(self, protocol_version = None):
        super().__init__()

        if protocol_version is None:
            protocol_version = random.randint(3, 5)

        self.fixed_header = PublishFixedHeader()
        self.variable_header = PublishVariableHeader(self.fixed_header.qos, protocol_version)
        self.publish_message_length = random.randint(0, 100)
        self.publish_message = self.getAlphanumHexString(self.publish_message_length)

        remaining_length = self.variable_header.getByteLength() + self.publish_message_length
        self.payload = [self.fixed_header.toString(), self.toVariableByte("%x" % remaining_length), self.variable_header.toString(), self.publish_message]

if __name__ == "__main__":
    packetTest([Connect, Publish], 10)