import socket
import random
import time
import sys
import math

host = "127.0.0.1"
port = 1883

fuzz_delay = 0.5

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
        byte = random.getrandbits(8).to_bytes(1, sys.byteorder)
        f = f[0:b] + byte + f[b + 1:]

    return f

def get_payload(file):
    f = open(file, "r")
    packets = f.read().splitlines()
    selection = random.choice(packets)
    f.close()
    return bytearray.fromhex(selection)#encode(errors='ignore').encode()

def fuzz_target(f, params):
    minm = params["min_mutate"]
    maxm = params["max_mutate"]
    if minm == maxm:
        num_mutate_bytes = round(minm / 100) * len(f)
    else:
        num_mutate_bytes = round(random.choice(range(minm, maxm)) / 100 * len(f))
    f = mutate(f, num_mutate_bytes)
    
    return f

def set_params(seed):
    params = {"min_mutate": 0, "max_mutate": 100}
    return params

# Fuzz MQTT
# params: A dictionary with various parameters
def fuzz(seed):

    random.seed(seed)

    params = set_params(seed)

    fuzzable = ["CONNECT", "PUBLISH", "DISCONNECT"]

    connect_payload = get_payload("mqtt_corpus/CONNECT")
    publish_payload = get_payload("mqtt_corpus/PUBLISH")
    disconnect_payload = get_payload("mqtt_corpus/DISCONNECT")

    for f in fuzzable:
        min_mutate = params["min_mutate"]
        max_mutate = params["max_mutate"]

        if f == "CONNECT":
            connect_payload = fuzz_target(connect_payload, params)

        elif f == "PUBLISH":
            publish_payload = fuzz_target(publish_payload, params)
        
        elif f == "DISCONNECT":
            disconnect_payload = fuzz_target(disconnect_payload, params)

        else:
            raise Exception("Error: %s is not a valid fuzz target" % f)

    payload = connect_payload + publish_payload + disconnect_payload
    print(payload)

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    s.connect((host, port))
    s.send(payload)
    s.close()
    

# TODO:
# - Look at the server output as we fuzz
# - Adapt to output

seed = math.floor(time.time())
while True:
    fuzz(seed)
    time.sleep(fuzz_delay)
    seed += 1