import socket

# Set up 3 different subscribe clients for each protocol version. Every
# 10 seconds, send a PINGREQ packet to keep the connections alive.

# If client disconnects, reconnect it

# Client should be able to handle publish with qos 1 and qos 2

host = "localhost"
port = 1883

subscribe_request_v31 = bytearray.fromhex("102500064d51497364700302003c00176d6f73712d55784763707a49717a75774e59754b30627a8206000100012302")

subscribe_request_v311 = bytearray.fromhex("100c00044d5154540402003c00008206000100012302")

subscribe_request_v5 = bytearray.fromhex("101000044d5154540502003c032100140000820700010000012300")


sock_v31 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock_v31.connect(("localhost", 1883))
sock_v31.send(subscribe_request_v31)

sock_v311 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock_v311.connect(("localhost", 1883))
sock_v311.send(subscribe_request_v311)

sock_v5 = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock_v5.connect(("localhost", 1883))
sock_v5.send(subscribe_request_v5)

while True:
    
    sock_v31_resp = sock_v31.recv(2048)
    sock_v311_resp = sock_v311.recv(2048)
    sock_v5_resp = sock_v5.recv(2048)

    sock_v31_resp_str = "".join(["%02X" % b for b in sock_v31_resp])
    print(sock_v31_resp_str)

    sock_v311_resp_str = "".join(["%02X" % b for b in sock_v311_resp])
    print(sock_v311_resp_str)

    sock_v5_resp_str = "".join(["%02X" % b for b in sock_v5_resp])
    print(sock_v5_resp_str)