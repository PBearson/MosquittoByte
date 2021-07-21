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
import pyradamsa
import random
import time
import socket

def sendShort(payload):
    sendToBroker("localhost", 1883, payload)

def testSocket(socket):
    try:
        for i in range(3):
            time.sleep(0.01)
            socket.send(bytearray.fromhex('c000'))
    except (ConnectionResetError, BrokenPipeError):
        return False
    return True
        

# def test

def run():
    rad = pyradamsa.Radamsa()
    packets = [Connect, Disconnect, Publish, Connack, Auth, Pingreq, Pingresp, Puback, Pubcomp, Pubrec, Pubrel, Suback, Subscribe, Unsuback, Unsubscribe]

    saved_payload = ""
    saved_protocol = 0
    attempts = 300
    while True:
        if len(saved_payload) == 0:
            protocol = random.randint(3, 5)
            payload = Connect(protocol).toString()
            saved_protocol = protocol
        else:
            payload = saved_payload
            nextPayload = random.choice(packets)(saved_protocol).toString()
            payload += nextPayload

        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.connect(("localhost", 1883))
        s.send(bytearray.fromhex(payload))
        if testSocket(s):
            attempts = 300
            saved_payload = payload
            s.close()
            print(len(saved_payload))

        else:
            attempts -= 1
            if attempts == 0:
                print("Fuzzing now")
                attempts = 300
                for j in range(500):
                    fuzzed = rad.fuzz(bytearray.fromhex(saved_payload))
                    sendShort(fuzzed)

                saved_payload = ""

if __name__ == "__main__":
    run()