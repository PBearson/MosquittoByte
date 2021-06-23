import random
import binascii
import string
import time

from packet import Packet

class ConnectProperties(Packet):
    def __init__(self):
        super().__init__()
        self.session_expiry_interval = ["%.2x" % 0x11, "%.8x" % random.getrandbits(32)]
        self.receive_maximum = ["%.2x" % 0x21, "%.4x" % max(1, random.getrandbits(16))]
        self.maximum_packet_size = ["%.2x" % 0x27, "%.8x" % max(1, random.getrandbits(32))]
        self.topic_alias_maximum = ["%.2x" % 0x22, "%.4x" % random.getrandbits(16)]
        self.request_response_information = ["%.2x" % 0x19, "%.2x" % random.getrandbits(1)]
        self.request_problem_information = ["%.2x" % 0x17, "%.2x" % random.getrandbits(1)]
        self.user_property_name_len = random.randint(1, 20)
        self.user_property_name = self.getAlphanumHexString(self.user_property_name_len)
        self.user_property_value_len = random.randint(1, 20)
        self.user_property_value = self.getAlphanumHexString(self.user_property_value_len)
        self.user_property = ["%.2x" % 0x26, "%.4x" % self.user_property_name_len, self.user_property_name, "%.4x" % self.user_property_value_len, self.user_property_value]
        self.authentication_method_len = random.randint(1, 20)
        self.authentication_method = ["%.2x" % 0x15, "%.4x" % self.authentication_method_len, self.getAlphanumHexString(self.authentication_method_len)]
        self.authentication_data_len = random.randint(1, 100)
        self.authentication_data = ["%.2x" % 0x16, "%.4x" % self.authentication_data_len, ["%.2x" % random.getrandbits(8) for i in range(self.authentication_data_len)]]

        self.payload = [self.payload_length]
        properties_bitmap = random.getrandbits(9)

        if properties_bitmap & 1 == 0:
            self.payload.append(self.session_expiry_interval)
            self.payload_length += 5

        if (properties_bitmap >> 1) & 1 == 0:
            self.payload.append(self.receive_maximum)
            self.payload_length += 3
        
        if (properties_bitmap >> 2) & 1 == 0:
           self.payload.append(self.maximum_packet_size)
           self.payload_length += 5

        if (properties_bitmap >> 3) & 1 == 0:
            self.payload.append(self.topic_alias_maximum)
            self.payload_length += 3
        
        if (properties_bitmap >> 4) & 1 == 0:
            self.payload.append(self.request_response_information)
            self.payload_length += 2

        if (properties_bitmap >> 5) & 1 == 0:
            self.payload.append(self.request_problem_information)
            self.payload_length += 2

        if (properties_bitmap >> 6) & 1 == 0:
            self.payload.append(self.user_property)
            self.payload_length += 5 + self.user_property_name_len + self.user_property_value_len
        
        if (properties_bitmap >> 7) & 1 == 0:
            self.payload.append(self.authentication_method)
            self.payload_length += 3 + self.authentication_method_len

            if (properties_bitmap >> 8) & 1 == 0:
                self.payload.append(self.authentication_data)
                self.payload_length += 3 + self.authentication_method_len
        
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

        payload_tmp = [self.username_flag, self.password_flag, self.will_retain, self.will_qos, self.will_flag, self.clean_start, self.reserved]

        self.payload = ["%.2x" % int("".join(bin(s)[2:] for s in payload_tmp), 2)]

        self.payload_length = 1

class ConnectVariableHeader(Packet):
    def __init__(self):
        self.name = ["%.2x" % 0b0, "%.2x" % 0b100, "%.2x" % 0b1001101, "%.2x" % 0b1010001, "%.2x" % 0b1010100, "%.2x" % 0b1010100]
        self.protocol_version = ["%.2x" % 0b101]#random.choice([0b11, 0b100, 0b101])]
        self.flags = ConnectFlags()
        self.keepalive = ["%.4x" % random.getrandbits(16)]
        self.properties = ConnectProperties()

        self.payload = [self.name, self.protocol_version, self.flags.toList(), self.keepalive]
        self.payload_length = 11 + self.flags.payload_length
        if int(self.protocol_version[0]) == 5:
            self.payload.append(self.properties.toList())
            self.payload_length += self.properties.payload_length

class WillProperties(Packet):
    def __init__(self, header):
        super().__init__()
        self.will_delay_interval = ["%.2x" % 0x18, "%.8x" % random.getrandbits(32)]
        self.payload_format_indicator = ["%.2x" % 0x01, "%.2x" % random.getrandbits(1)]
        self.message_expiry_interval = ["%.2x" % 0x02, "%.8x" % random.getrandbits(32)]
        self.content_type_length = random.randint(1, 20)
        self.content_type = ["%.2x" % 0x03, "%.4x" % self.content_type_length, self.getAlphanumHexString(self.content_type_length)]
        self.response_topic_length = random.randint(1, 20)
        self.response_topic = ["%.2x" % 0x08, "%.4x" % self.response_topic_length, self.getAlphanumHexString(self.response_topic_length)]
        self.correlation_data_length = random.randint(1, 30)
        self.correlation_data = ["%.2x" % 0x09, "%.4x" % self.correlation_data_length, ["%.2x" % random.getrandbits(8) for i in range(self.correlation_data_length)]]
        self.user_property_name_len = random.randint(1, 20)
        self.user_property_name = self.getAlphanumHexString(self.user_property_name_len)
        self.user_property_value_len = random.randint(1, 20)
        self.user_property_value = self.getAlphanumHexString(self.user_property_value_len)
        self.user_property = ["%.2x" % 0x26, "%.4x" % self.user_property_name_len, self.user_property_name, "%.4x" % self.user_property_value_len, self.user_property_value]

        self.payload = [self.payload_length]
        properties_bitmap = random.getrandbits(7)

        if properties_bitmap & 1 == 0:
            self.payload.append(self.will_delay_interval)
            self.payload_length += 5

        if (properties_bitmap >> 1) & 1 == 0:
            self.payload.append(self.payload_format_indicator)
            self.payload_length += 2
        
        if (properties_bitmap >> 2) & 1 == 0:
            self.payload.append(self.message_expiry_interval)
            self.payload_length += 5

        if (properties_bitmap >> 3) & 1 == 0:
            self.payload.append(self.content_type)
            self.payload_length += 3 + self.content_type_length

        if (properties_bitmap >> 4) & 1 == 0:
            self.payload.append(self.response_topic)
            self.payload_length += 3 + self.response_topic_length

        if (properties_bitmap >> 5) & 1 == 0:
            self.payload.append(self.correlation_data)
            self.payload_length += 3 + self.correlation_data_length

        if (properties_bitmap >> 6) & 1 == 0:
            self.payload.append(self.user_property)
            self.payload_length += 5 + self.user_property_name_len + self.user_property_value_len

        self.payload[0] = [self.toVariableByte("%x" % self.payload_length)]

class ConnectPayload(Packet):
    def __init__(self, header):
        
        self.clientid_len = random.randint(1, 30)
        self.clientid = ["%.4x" % self.clientid_len, self.getAlphanumHexString(self.clientid_len)]
        self.will_properties = WillProperties(header)
        self.will_topic_length = random.randint(1, 30)
        self.will_topic = ["%.4x" % self.will_topic_length, self.getAlphanumHexString(self.will_topic_length)]
        self.will_payload_length = random.randint(1, 100)
        self.will_payload = ["%.4x" % self.will_payload_length, ["%.2x" % random.getrandbits(8) for i in range(self.will_payload_length)]]
        self.username_length = random.randint(1, 20)
        self.username = ["%.4x" % self.username_length, self.getAlphanumHexString(self.username_length)]
        self.password_length = random.randint(1, 20)
        self.password = ["%.4x" % self.password_length, self.getAlphanumHexString(self.password_length)]

        self.payload = [self.clientid]
        self.payload_length = self.clientid_len

        if header.flags.will_flag == 1:
            self.payload.append(self.will_properties.toList())
            self.payload.append(self.will_topic)
            self.payload.append(self.will_payload)
            self.payload_length += 6 + self.will_properties.payload_length + self.will_topic_length + self.will_payload_length
        
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

    def printComponents(self):
        print("Fixed Header:", self.fixed_header)
        print("Message length:", self.payload_length - 4)
        print("Protocol name:", self.variable_header.name)
        print("Protocol version:", self.variable_header.protocol_version)
        print("Connect flags:", self.variable_header.flags.toString())
        print("Keep alive:", self.variable_header.keepalive)
        print("Property length:", self.variable_header.properties.payload_length)
        print("Properties: ", self.variable_header.properties.toString())
        print("Will length:", self.connect_payload.will_properties.payload_length)
        print("Will properties:", self.connect_payload.will_properties.toString())
        print("Will topic length:", self.connect_payload.will_topic_length)
        print("Will topic:", self.connect_payload.will_topic)

def test():
    host = "127.0.0.1"
    port = 1883

    for i in range(1):
        packet = Connect()
        packet.printComponents()
        packet.sendToBroker(host, port)
        time.sleep(0.1)

if __name__ == "__main__":
    test()