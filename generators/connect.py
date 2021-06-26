import random
import binascii
import string
import time

from packet import Packet

class ConnectProperties(Packet):
    def __init__(self):
        super().__init__()

        self.payload.append(["00"])

        self.session_expiry_interval = self.toBinaryData(0x11, 4, True)
        self.appendPayloadRandomly(self.session_expiry_interval)

        self.receive_maximum = self.toBinaryData(0x21, 2, True)
        self.appendPayloadRandomly(self.receive_maximum)

        self.maximum_packet_size = self.toBinaryData(0x27, 4, True, 8, 1)
        self.appendPayloadRandomly(self.maximum_packet_size)

        self.topic_alias_maximum = self.toBinaryData(0x22, 2, True)
        self.appendPayloadRandomly(self.topic_alias_maximum)

        self.request_response_information = self.toBinaryData(0x19, 1, True, 1)
        self.appendPayloadRandomly(self.request_response_information)

        self.request_problem_information = self.toBinaryData(0x17, 1, True, 1)
        self.appendPayloadRandomly(self.request_problem_information)

        self.user_property_name_len = random.randint(1, 20)
        self.user_property_value_len = random.randint(1, 20)
        self.user_property = self.toEncodedStringPair(0x26, self.user_property_name_len, self.user_property_value_len)
        self.appendPayloadRandomly(self.user_property)

        self.authentication_method_len = random.randint(1, 20)
        self.authentication_method = self.toEncodedString(0x15, self.authentication_method_len)
        self.appendPayloadRandomly(self.authentication_method)

        self.authentication_data_len = random.randint(1, 20)
        self.authentication_data = self.toEncodedString(0x16, self.authentication_data_len)
        self.appendPayloadRandomly(self.authentication_data)
        
        # Subtract 1 since the reported length includes the length field itself
        self.payload[0] = [self.toVariableByte("%x" % (self.getByteLength() - 1))]
        
class ConnectFlags(Packet):
    def __init__(self):        
        self.username_flag = random.getrandbits(1)
        self.password_flag = random.getrandbits(1)
        self.will_retain = random.getrandbits(1)
        self.will_qos = min(2, random.getrandbits(2))
        self.will_flag = random.getrandbits(1)
        self.clean_start = random.getrandbits(1)
        self.reserved = 0
        
        if self.will_flag == 0:
            self.will_qos = 0

        if self.will_flag == 0:
            self.will_retain = 0

        payload_tmp = [self.username_flag, self.password_flag, self.will_retain, self.will_qos & 1, (self.will_qos >> 1) & 1, self.will_flag, self.clean_start, self.reserved]

        self.payload = ["%.2x" % int("".join(bin(s)[2:] for s in payload_tmp), 2)]

class ConnectVariableHeader(Packet):
    def __init__(self):
        self.name = ["%.2x" % 0b0, "%.2x" % 0b100, "%.2x" % 0b1001101, "%.2x" % 0b1010001, "%.2x" % 0b1010100, "%.2x" % 0b1010100]
        self.protocol_version = ["%.2x" % random.choice([0b11, 0b100, 0b101])]
        self.flags = ConnectFlags()
        self.keepalive = self.toBinaryData(None, 2, True)
        self.properties = ConnectProperties()

        self.payload = [self.name, self.protocol_version, self.flags.toList(), self.keepalive]

        if int(self.protocol_version[0]) == 5:
            self.payload.append(self.properties.toList())

class WillProperties(Packet):
    def __init__(self, header):
        super().__init__()
        self.payload.append(['00'])

        self.will_delay_interval = self.toBinaryData(0x18, 4, True)
        self.appendPayloadRandomly(self.will_delay_interval)

        self.payload_format_indicator = self.toBinaryData(0x01, 1, True, 1) 
        self.appendPayloadRandomly(self.payload_format_indicator)

        self.message_expiry_interval = self.toBinaryData(0x02, 4, True)
        self.appendPayloadRandomly(self.message_expiry_interval)

        self.content_type_length = random.randint(1, 20)
        self.content_type = self.toEncodedString(0x03, self.content_type_length)
        self.appendPayloadRandomly(self.content_type)

        self.response_topic_length = random.randint(1, 20)
        self.response_topic = self.toEncodedString(0x08, self.response_topic_length)
        self.appendPayloadRandomly(self.response_topic)

        self.correlation_data_length = random.randint(1, 30)
        self.correlation_data = self.toBinaryData(0x09, self.correlation_data_length)
        self.appendPayloadRandomly(self.correlation_data)

        self.user_property_name_len = random.randint(1, 20)
        self.user_property_value_len = random.randint(1, 20)
        self.user_property = self.toEncodedStringPair(0x26, self.user_property_name_len, self.user_property_value_len)
        self.appendPayloadRandomly(self.user_property)

        # Subtract 1 since the reported length includes the length field itself
        self.payload[0] = [self.toVariableByte("%x" % (self.getByteLength() - 1))]

class ConnectPayload(Packet):
    def __init__(self, header):
        self.clientid_len = random.randint(1, 30)
        self.clientid = self.toEncodedString(None, self.clientid_len)
        self.will_properties = WillProperties(header)
        self.will_topic_length = random.randint(1, 30)
        self.will_topic = self.toEncodedString(None, self.will_topic_length)
        self.will_payload_length = random.randint(1, 30)
        self.will_payload = self.toEncodedString(None, self.will_payload_length)
        self.username_length = random.randint(1, 20)
        self.username = self.toEncodedString(None, self.username_length)
        self.password_length = random.randint(1, 20)
        self.password = self.toEncodedString(None, self.password_length)

        self.payload = [self.clientid]

        if header.flags.will_flag == 1:
            if int(header.protocol_version[0]) == 5:
                self.payload.append(self.will_properties.toList())

            self.payload.append(self.will_topic)
            self.payload.append(self.will_payload)
            
        if header.flags.username_flag == 1:
            self.payload.append(self.username)
        
        if header.flags.password_flag == 1:
            self.payload.append(self.password)

class Connect(Packet):
    def __init__(self):
        self.fixed_header = ["%.2x" % 0b10000]
        self.variable_header = ConnectVariableHeader()
        self.connect_payload = ConnectPayload(self.variable_header)

        remaining_length = self.variable_header.getByteLength() + self.connect_payload.getByteLength()
        
        self.payload = [self.fixed_header, self.toVariableByte("%x" % remaining_length), self.variable_header.toList(), self.connect_payload.toList()]

if __name__ == "__main__":
    Packet().test(Connect)