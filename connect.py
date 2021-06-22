import random
import binascii
import string
import time
import socket

from packet import Packet

class ConnectProperties(Packet):
    def __init__(self):

        self.property_length = 0
        self.session_expiry_interval = ["%.2x" % 0x11, "%.8x" % random.getrandbits(32)]
        self.receive_maximum = ["%.2x" % 0x21, "%.4x" % max(1, random.getrandbits(16))]
        self.maximum_packet_size = ["%.2x" % 0x27, "%.8x" % max(1, random.getrandbits(32))]
        self.topic_alias_maximum = ["%.2x" % 0x22, "%.4x" % random.getrandbits(16)]
        self.request_response_information = ["%.2x" % 0x19, "%.2x" % random.getrandbits(1)]
        self.request_problem_information = ["%.2x" % 0x17, "%.2x" % random.getrandbits(1)]
        self.user_property_name_len = 1#random.randint(1, 20)
        self.user_property_name = ["%.2x" % ord(random.choice(string.printable)) for i in range(self.user_property_name_len)]
        self.user_property_value_len = 1#random.randint(1, 20)
        self.user_property_value = ["%.2x" % ord(random.choice(string.printable)) for i in range(self.user_property_value_len)]
        self.user_property = ["%.2x" % 0x26, "%.2x" % self.user_property_name_len, self.user_property_name, "%.2x" % self.user_property_value_len, self.user_property_value]
        self.authentication_method_len = 1#random.randint(1, 20)
        self.authentication_method = ["%.2x" % 0x15, "%.2x" % self.authentication_method_len, ["%.2x" % ord(random.choice(string.printable)) for i in range(self.authentication_method_len)]]
        self.authentication_data_len = 1#random.randint(1, 100)
        self.authentication_data = ["%.2x" % 0x16, "%.2x" % self.authentication_data_len, "%.2x" % random.getrandbits(8 * self.authentication_data_len)]

        self.payload = [self.property_length]
        properties_bitmap = 0#random.getrandbits(9)

        if properties_bitmap & 1 == 0:
            self.payload.append(self.session_expiry_interval)
            self.property_length += 5

        if (properties_bitmap >> 1) & 1 == 0:
            self.payload.append(self.receive_maximum)
            self.property_length += 3
        
        if (properties_bitmap >> 2) & 1 == 0:
           self.payload.append(self.maximum_packet_size)
           self.property_length += 5

        if (properties_bitmap >> 3) & 1 == 0:
            self.payload.append(self.topic_alias_maximum)
            self.property_length += 3
        
        if (properties_bitmap >> 4) & 1 == 0:
            self.payload.append(self.request_response_information)
            self.property_length += 2

        if (properties_bitmap >> 5) & 1 == 0:
            self.payload.append(self.request_problem_information)
            self.property_length += 2

        if (properties_bitmap >> 6) & 1 == 0:
            self.payload.append(self.user_property)
            self.property_length += 5 + self.user_property_name_len + self.user_property_value_len
        
        if (properties_bitmap >> 7) & 1 == 0:
            self.payload.append(self.authentication_method)
            self.property_length += 3 + self.authentication_method_len

            if (properties_bitmap >> 8) & 1 == 0:
                self.payload.append(self.authentication_data)
                self.property_length += 3 + self.authentication_method_len
        
        self.payload[0] = ["%.4x" % self.property_length]
        
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

        self.payload = ["%.2x" % self.username_flag, "%.2x" % self.password_flag, "%.2x" % self.will_retain, "%.2x" % self.will_qos, "%.2x" % self.will_flag, "%.2x" % self.clean_start]
        self.payload_length = 1

class ConnectVariableHeader(Packet):
    def __init__(self):
        self.name = ["%.2x" % 0b0, "%.2x" % 0b100, "%.2x" % 0b1001101, "%.2x" % 0b1010001, "%.2x" % 0b1010100, "%.2x" % 0b1010100]
        self.protocol_version = ["%.2x" % random.choice([0b11, 0b100, 0b101])]
        self.flags = ConnectFlags()
        self.keepalive = ["%.4x" % random.getrandbits(16)]
        self.properties = ConnectProperties()

        self.payload = [self.name, self.protocol_version, self.flags.toList(), self.keepalive, self.properties.toList()]
        self.payload_length = 11 + self.flags.payload_length + self.properties.property_length

class WillProperties(Packet):
    def __init__(self, header):
        self.property_length = 0
        self.will_delay_interval = ["%.2x" % 0x18, "%.8x" % random.getrandbits(32)]
        self.payload_format_indicator = ["%.2x" % 0x01, "%.2x" % random.getrandbits(1)]
        self.message_expiry_interval = ["%.2x" % 0x02, "%.8x" % random.getrandbits(32)]
        self.content_type_length = random.randint(1, 20)
        self.content_type = ["%.2x" % 0x03, "%.4x" % self.content_type_length, ["%.2x" % ord(random.choice(string.printable)) for i in range(self.content_type_length)]]
        self.response_topic_length = random.randint(1, 20)
        self.response_topic = ["%.2x" % 0x08, "%.4x" % self.response_topic_length, ["%.2x" % ord(random.choice(string.printable)) for i in range(self.response_topic_length)]]
        self.correlation_data_length = random.randint(1, 30)
        self.correlation_data = ["%.2x" % 0x09, "%.4x" % self.correlation_data_length, ["%.2x" % random.getrandbits(8) for i in range(self.correlation_data_length)]]
        self.user_property_name_len = random.randint(1, 20)
        self.user_property_name = ["%.2x" % ord(random.choice(string.printable)) for i in range(self.user_property_name_len)]
        self.user_property_value_len = random.randint(1, 20)
        self.user_property_value = ["%.2x" % ord(random.choice(string.printable)) for i in range(self.user_property_value_len)]
        self.user_property = ["%.2x" % 0x26, "%.4x" % self.user_property_name_len, self.user_property_name, "%.4x" % self.user_property_value_len, self.user_property_value]

        self.payload = [self.property_length]
        properties_bitmap = random.getrandbits(7)

        if properties_bitmap & 1 == 0:
            self.payload.append(self.will_delay_interval)
            self.property_length += 5

        if (properties_bitmap >> 1) & 1 == 0:
            self.payload.append(self.payload_format_indicator)
            self.property_length += 2
        
        if (properties_bitmap >> 2) & 1 == 0:
            self.payload.append(self.message_expiry_interval)
            self.property_length += 5

        if (properties_bitmap >> 3) & 1 == 0:
            self.payload.append(self.content_type)
            self.property_length += 3 + self.content_type_length

        if (properties_bitmap >> 4) & 1 == 0:
            self.payload.append(self.response_topic)
            self.property_length += 3 + self.response_topic_length

        if (properties_bitmap >> 5) & 1 == 0:
            self.payload.append(self.correlation_data)
            self.property_length += 3 + self.correlation_data_length

        if (properties_bitmap >> 6) & 1 == 0:
            self.payload.append(self.user_property)
            self.property_length += 5 + self.user_property_name_len + self.user_property_value_len

        self.payload[0] = ["%.4x" % self.property_length]

class ConnectPayload(Packet):
    def __init__(self, header):
        
        self.clientid_len = random.randint(1, 30)
        self.clientid = ["%.4x" % self.clientid_len, ["%.2x" % ord(random.choice(string.printable)) for i in range(self.clientid_len)]]
        self.will_properties = WillProperties(header)
        self.will_topic_length = random.randint(1, 30)
        self.will_topic = ["%.4x" % self.will_topic_length, ["%.2x" % ord(random.choice(string.printable)) for i in range(self.will_topic_length)]]
        self.will_payload_length = random.randint(1, 100)
        self.will_payload = ["%.4x" % self.will_payload_length, ["%.2x" % random.getrandbits(8) for i in range(self.will_payload_length)]]
        self.username_length = random.randint(1, 20)
        self.username = ["%.4x" % self.username_length, ["%.2x" % ord(random.choice(string.printable)) for i in range(self.username_length)]]
        self.password_length = random.randint(1, 20)
        self.password = ["%.4x" % self.password_length, ["%.2x" % ord(random.choice(string.printable)) for i in range(self.password_length)]]

        self.payload = [self.clientid]
        self.payload_length = self.clientid_len

        if header.flags.will_flag == 1:
            self.payload.append(self.will_properties.toList())
            self.payload.append(self.will_topic)
            self.payload.append(self.will_payload)
            self.payload_length += 6 + self.will_properties.property_length + self.will_topic_length + self.will_payload_length
        
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
        
        self.payload_length = 4 + self.variable_header.payload_length + self.connect_payload.payload_length

        self.payload = [self.fixed_header, "%.4x" % self.payload_length, self.variable_header.toList(), self.connect_payload.toList()]

    def printComponentsAsList(self):
        print("Fixed header: ", self.fixed_header)
        print("Connect flags: ", self.variable_header.flags.toList())
        print("Connect properties: ", self.variable_header.properties.toList())
        print("Variable header: ", self.variable_header.toList())
        print("Will properties: ", self.connect_payload.will_properties.toList())
        print("Payload: ", self.connect_payload.toList())
        print("Final packet: ", self.toList())

    def printComponentSizes(self):
        print("Fixed header: 2 bytes")
        print("Connect flags: %.1f bytes" % self.variable_header.flags.getByteLength())
        print("Connect properties: %.1f bytes" % self.variable_header.properties.getByteLength())
        print("Variable header: %.1f bytes" % self.variable_header.getByteLength())
        print("Will properties: %.1f bytes" % self.connect_payload.will_properties.getByteLength())
        print("Payload: %.1f bytes" % self.connect_payload.getByteLength())
        print("Final packet: %.1f bytes" % self.getByteLength())

def test():
    host = "127.0.0.1"
    port = 1883

    while True:
        packet = Connect()
        packet.printComponentsAsList()
        packet.printComponentSizes()     
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((host, port))
        try:
            s.send(bytearray.fromhex(packet.toString()))
        except ValueError:
            print("Error caused by following payload:")
            print(packet.toString())
            exit(0)
        s.close()
        time.sleep(0.25)

if __name__ == "__main__":
    test()