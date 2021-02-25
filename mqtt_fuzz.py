import socket
import random
import os
import time

host = "127.0.0.1"
port = 1883

params = {"min_mutate": 10, "max_mutate": 100}
fuzz_delay = 0.05

connect_payload = b'\x10\x0c\x00\x04MQTT\x04\x02\x00<\x00\x00'
publish_payload = b'0\x08\x00\x04testhi'
disconnect_payload = b'\xe0\x00'

# Add bytes in a string
# f : the fuzzable object
# nb : the number of bytes to add to f
def add(f, nb):
    bits = random.sample(range(len(f)), min(nb, len(f)))
    return f

# Mutate bytes in a string
# f : the fuzzable object
# nb : the number of bytes to mutate in f
def mutate(f, nb):
    bits = random.sample(range(len(f)), min(nb, len(f)))

    for b in bits:
        f = f[0:b] + os.urandom(1) + f[b + 1:]

    return f

def fuzz_target(f, params):
    minm = params["min_mutate"]
    maxm = params["max_mutate"]
    num_mutate_bytes = round(random.choice(range(minm, maxm)) / 100 * len(f))
    f = mutate(f, num_mutate_bytes)
    
    return f

# Fuzz MQTT
# params: A dictionary with various parameters
def fuzz(params):

    fuzzable = ["DISCONNECT"]

    connect_payload_tmp = connect_payload
    publish_payload_tmp = publish_payload
    disconnect_payload_tmp = disconnect_payload

    for f in fuzzable:
        min_mutate = params["min_mutate"]
        max_mutate = params["max_mutate"]

        if f == "CONNECT":
            connect_payload_tmp = fuzz_target(connect_payload_tmp, params)

        elif f == "PUBLISH":
            publish_payload_tmp = fuzz_target(publish_payload_tmp, params)
        
        elif f == "DISCONNECT":
            disconnect_payload_tmp = fuzz_target(disconnect_payload_tmp, params)

        else:
            raise Exception("Error: %s is not a valid fuzz target" % f)

    payload = connect_payload_tmp + publish_payload_tmp + disconnect_payload_tmp
    print(payload)

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((host, port))
    s.send(payload)
    s.close()
    

# TODO:
# - Look at the server output as we fuzz
# - Adapt to output

while True:
    fuzz(params)
    time.sleep(fuzz_delay)