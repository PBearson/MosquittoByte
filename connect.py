import random
import binascii
import string
import time

from packet import Packet

class ConnectProperties(Packet):
    def __init__(self):
        super().__init__()
        self.session_expiry_interval = self.toBinaryData(0x11, 4, True)
        self.receive_maximum = self.toBinaryData(0x21, 2, True)
        self.maximum_packet_size = self.toBinaryData(0x27, 4, True, 8, 1)
        self.topic_alias_maximum = self.toBinaryData(0x22, 2, True)
        self.request_response_information = self.toBinaryData(0x19, 1, True, 1)
        self.request_problem_information = self.toBinaryData(0x17, 1, True, 1)
        self.user_property_name_len = random.randint(1, 20)
        self.user_property_value_len = random.randint(1, 20)
        self.user_property = self.toEncodedStringPair(0x26, self.user_property_name_len, self.user_property_value_len)
        self.authentication_method_len = random.randint(1, 20)
        self.authentication_method = self.toEncodedString(0x15, self.authentication_method_len)
        self.authentication_data_len = random.randint(1, 20)
        self.authentication_data = self.toEncodedString(0x16, self.authentication_data_len)

        self.payload = [self.payload_length]
        properties_bitmap = random.getrandbits(9)

        if self.getKthBit(0, properties_bitmap):
            self.payload.append(self.session_expiry_interval)
            self.payload_length += 5

        if self.getKthBit(1, properties_bitmap):
            self.payload.append(self.receive_maximum)
            self.payload_length += 3
        
        if self.getKthBit(2, properties_bitmap):
           self.payload.append(self.maximum_packet_size)
           self.payload_length += 5

        if self.getKthBit(3, properties_bitmap):
            self.payload.append(self.topic_alias_maximum)
            self.payload_length += 3
        
        if self.getKthBit(4, properties_bitmap):
            self.payload.append(self.request_response_information)
            self.payload_length += 2

        if self.getKthBit(5, properties_bitmap):
            self.payload.append(self.request_problem_information)
            self.payload_length += 2

        if self.getKthBit(6, properties_bitmap):
            self.payload.append(self.user_property)
            self.payload_length += 5 + self.user_property_name_len + self.user_property_value_len
        
        if self.getKthBit(7, properties_bitmap):
            self.payload.append(self.authentication_method)
            self.payload_length += 3 + self.authentication_method_len

            if self.getKthBit(8, properties_bitmap):
                self.payload.append(self.authentication_data)
                self.payload_length += 3 + self.authentication_data_len
        
        self.payload[0] = [self.toVariableByte("%x" % self.payload_length)]
        
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

        self.payload_length = 1

class ConnectVariableHeader(Packet):
    def __init__(self):
        self.name = ["%.2x" % 0b0, "%.2x" % 0b100, "%.2x" % 0b1001101, "%.2x" % 0b1010001, "%.2x" % 0b1010100, "%.2x" % 0b1010100]
        self.protocol_version = ["%.2x" % random.choice([0b11, 0b100, 0b101])]
        self.flags = ConnectFlags()
        self.keepalive = self.toBinaryData(None, 2, True)
        self.properties = ConnectProperties()

        self.payload = [self.name, self.protocol_version, self.flags.toList(), self.keepalive]
        self.payload_length = 11 + self.flags.payload_length
        if int(self.protocol_version[0]) == 5:
            self.payload.append(self.properties.toList())
            self.payload_length += self.properties.payload_length

class WillProperties(Packet):
    def __init__(self, header):
        super().__init__()
        self.will_delay_interval = self.toBinaryData(0x18, 4, True)
        self.payload_format_indicator = self.toBinaryData(0x01, 1, True, 1) 
        self.message_expiry_interval = self.toBinaryData(0x02, 4, True)       
        self.content_type_length = random.randint(1, 20)
        self.content_type = self.toEncodedString(0x03, self.content_type_length)
        self.response_topic_length = random.randint(1, 20)
        self.response_topic = self.toEncodedString(0x08, self.response_topic_length)
        self.correlation_data_length = random.randint(1, 30)
        self.correlation_data = self.toBinaryData(0x09, self.correlation_data_length)
        self.user_property_name_len = random.randint(1, 20)
        self.user_property_value_len = random.randint(1, 20)
        self.user_property = self.toEncodedStringPair(0x26, self.user_property_name_len, self.user_property_value_len)

        self.payload = [self.payload_length]
        properties_bitmap = random.getrandbits(7)

        if self.getKthBit(0, properties_bitmap):
            self.payload.append(self.will_delay_interval)
            self.payload_length += 5

        if self.getKthBit(1, properties_bitmap):
            self.payload.append(self.payload_format_indicator)
            self.payload_length += 2
        
        if self.getKthBit(2, properties_bitmap):
            self.payload.append(self.message_expiry_interval)
            self.payload_length += 5

        if self.getKthBit(3, properties_bitmap):
            self.payload.append(self.content_type)
            self.payload_length += 3 + self.content_type_length

        if self.getKthBit(4, properties_bitmap):
            self.payload.append(self.response_topic)
            self.payload_length += 3 + self.response_topic_length

        if self.getKthBit(5, properties_bitmap):
            self.payload.append(self.correlation_data)
            self.payload_length += 3 + self.correlation_data_length

        if self.getKthBit(6, properties_bitmap):
            self.payload.append(self.user_property)
            self.payload_length += 5 + self.user_property_name_len + self.user_property_value_len

        self.payload[0] = [self.toVariableByte("%x" % self.payload_length)]

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
        self.payload_length = self.clientid_len

        if header.flags.will_flag == 1:
            if int(header.protocol_version[0]) == 5:
                self.payload.append(self.will_properties.toList())
                self.payload_length += 1 + self.will_properties.payload_length

            self.payload.append(self.will_topic)
            self.payload.append(self.will_payload)
            self.payload_length += 2 + self.will_topic_length + self.will_payload_length
            
        if header.flags.username_flag == 1:
            self.payload.append(self.username)
            self.payload_length += 2 + self.username_length
        
        if header.flags.password_flag == 1:
            self.payload.append(self.password)
            self.payload_length += 2 + self.password_length

class Connect(Packet):
    def __init__(self):
        self.fixed_header = ["%.2x" % 0b10000]
        self.variable_header = ConnectVariableHeader()
        self.connect_payload = ConnectPayload(self.variable_header)
        
        self.payload_length = int(4 + self.variable_header.getByteLength() + self.connect_payload.getByteLength())

        self.payload = [self.fixed_header, self.toVariableByte("%x" % (self.payload_length - 4)), self.variable_header.toList(), self.connect_payload.toList()]

def test():
    host = "127.0.0.1"
    port = 1883

    for i in range(250):
        packet = Connect()
        packet.sendToBroker(host, port)
        time.sleep(0.01)

if __name__ == "__main__":
    test()