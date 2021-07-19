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

def sendShort(payload):
    sendToBroker("localhost", 1883, payload)

def run():
    rad = pyradamsa.Radamsa()
    packets = [Connect, Publish, Connack, Auth, Pingreq, Pingresp, Disconnect, Puback, Pubcomp, Pubrec, Pubrel, Suback, Subscribe, Unsuback, Unsubscribe]
        
    while True:
        numMiddle = random.randint(1, 10)
        protocol = random.randint(3, 5)
        connect = Connect(protocol).toString()
        middle = ""
        disconnect = Disconnect(protocol).toString()
        for n in range(numMiddle):
            middle += random.choice(packets)(protocol).toString()

        payload = bytearray.fromhex(connect + middle + disconnect)

        sendShort(payload)

        payload = rad.fuzz(payload)

        sendShort(payload)

if __name__ == "__main__":
    run()