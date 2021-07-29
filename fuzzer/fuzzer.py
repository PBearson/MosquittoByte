# We can think of some fuzz modifiers:

# Overflow - Strings and variable byte lengths are increased incrementally
# Lots of Wildcards - Topic names will contain a disproportionate number of wildcards
# Long sessions - Sessions and message expirations are set to the highest possible value
# Bad strings - Strings can contain non-printable characters
# Many user properties - The number of user properties are increased incrementally
# Fixed Client - All packets come from the same client
# Null bytes - Strings and binary data will contain a disproportionate number of null bytes
# Padded payloads - Payloads are padding with many null bytes and the "remaining length" fields are updated accordingly

# Flow:
# - Generate 100 valid packets and add them to a queue. We will know it is valid if the server responds CONNACK with success return code.

import sys
sys.path.append("generators")
sys.path.append("parsers")
from packet import sendToBroker
from connect import Connect
from publish import Publish
from connack import Connack
from auth import Auth
from pingreq import Pingreq
from pingresp import Pingresp
from disconnect import Disconnect
from puback import Puback
from pubcomp import Pubcomp
from pubrec import Pubrec
from pubrel import Pubrel
from suback import Suback
from subscribe import Subscribe
from unsuback import Unsuback
from unsubscribe import Unsubscribe

from parse_initializer import ParseInitializer

import binascii
import pyradamsa
import random
import time
import socket

def sendShort(payload, port):
    sendToBroker("localhost", port, payload)

def testSocket(socket):
    try:
        for i in range(3):
            time.sleep(0.01)
            socket.send(bytearray.fromhex('c000'))
    except (ConnectionResetError, BrokenPipeError):
        return False
    return True

def bytearrayToString(value):
    return "".join(["%.02x" % r for r in value])

# Given a full payload, return a list of individual packets
# Do this by parsing the "remaining length" fields
def full_payload_to_packets(payload, packets = []):
        if len(payload) == 0:
            return packets

        index = 2
        multiplier = 1
        while True:
            encodedByte = int(payload[index:index+2], 16)
            index += 2
            multiplier *= 128
            if encodedByte & 128 == 0:
                break

        value = int(payload[2:index], 16)
        payload_length = value*2 + 4
        packet = payload[0:payload_length]
        packets.append(packet)
        return full_payload_to_packets(payload[payload_length:], packets)

def run():
    rad = pyradamsa.Radamsa()
    packet_headers = {
        "2": "connack",
        "3": "publish",
        "4": "puback",
        "5": "pubrec",
        "6": "pubrel",
        "7": "pubcomp",
        "8": "subscribe",
        "9": "suback",
        "a": "unsubscribe",
        "b": "unsuback",
        "c": "pingreq",
        "d": "pingresp",
        "e": "disconnect",
        "f": "auth"
        }
    packets = [Connect, Disconnect, Publish, Connack, Auth, Pingreq, Pingresp, Puback, Pubcomp, Pubrec, Pubrel, Suback, Subscribe, Unsuback, Unsubscribe]

    observed_gfields = {}
    requests_queue = []

    host = "localhost"
    port = 1883

    max_attempts = 1000

    packets_index = 0
    queue_selection = ""

    attempts = max_attempts

    while attempts > 0:
        attempts -= 1

        protocol_version = random.randint(3, 5)

        request = Connect(protocol_version).toString()

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect((host, port))
        s.send(bytearray.fromhex(request))
        try:
            response = bytearrayToString(s.recv(1024))
            s.close()
        except ConnectionResetError:
            continue

        responses = full_payload_to_packets(response, [])

        for r in responses:

            packet_type = packet_headers[r[0]]
            
            parser = ParseInitializer(r, protocol_version).parser
        
            if parser is not None:
                g_fields = parser.G_fields

                if packet_type not in observed_gfields.keys():
                    observed_gfields[packet_type] = {}

                new_find = False
                for (k, v) in g_fields.items():
                    if k in observed_gfields[packet_type]:
                        if v in observed_gfields[packet_type][k]:
                            continue
                        else:
                            observed_gfields[packet_type][k].append(v)
                            new_find = True
                    else:
                        observed_gfields[packet_type][k] = [v]
                        new_find = True

                if new_find:
                    attempts = max_attempts
                    requests_queue.append(request)
    for o in observed_gfields:
        print(o, observed_gfields[o])
            

if __name__ == "__main__":
    run()
