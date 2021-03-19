import socket
import random
import time
import sys
import argparse
import math

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
    return bytearray.fromhex(selection)

def fuzz_target(f, params):
    minm = params["min_mutate"]
    maxm = params["max_mutate"]
    if minm == maxm:
        num_mutate_bytes = round(minm / 100) * len(f)
    else:
        num_mutate_bytes = round(random.choice(range(minm, maxm)) / 100 * len(f))
    f = mutate(f, num_mutate_bytes)
    
    return f

def get_params(seed):
    mutate_a = random.randint(0, 100)
    mutate_b = random.randint(0, 100)
    min_mutate = min(mutate_a, mutate_b)
    max_mutate = max(mutate_a, mutate_b)
    params = {"min_mutate": min_mutate, "max_mutate": max_mutate}
    return params

# Fuzz MQTT
# params: A dictionary with various parameters
def fuzz(seed):

    random.seed(seed)

    params = get_params(seed)

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

def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("-H", "--host", help = "Fuzzing target host. Default is localhost.")
    parser.add_argument("-P", "--port", help = "Fuzzing target port. Default is 1883.")
    parser.add_argument("-s", "--seed", help = "Set the seed. If not set by the user, the system time is used as the seed.")
    parser.add_argument("-f", "--fuzz_delay", help = "Set the delay between each fuzzing attempt. Default is 0.1 seconds.")
    parser.add_argument("-r", "--runs", help = "Set the number of fuzz attempts made. If not set, the fuzzer will run indefinitely.")
    parser.add_argument("-p", "--params_only", help = "Do not fuzz. Simply return the parameters based on the seed value.", action = "store_true")

    args = parser.parse_args()

    global host, port

    if(args.host):
        host = args.host
    else:
        host = "localhost"

    if(args.port):
        port = int(args.port)
    else:
        port = 1883

    if(args.seed):  
        seed = int(args.seed)
    else:
        seed = math.floor(time.time())

    if(args.fuzz_delay):
        fuzz_delay = float(args.fuzz_delay)
    else:
        fuzz_delay = 0.1

    if(args.runs):
        runs = int(args.runs)


    print("Hello fellow fuzzer :)")
    print("Host: %s, Port: %d" % (host, port))
    print("Base seed: ", seed)

    if(args.params_only):
        random.seed(seed)
        params = get_params(seed)
        print("Your params: ", params)
        exit()

    while True:
        fuzz(seed)
        time.sleep(fuzz_delay)
        seed += 1
        if 'runs' in locals():
            runs -= 1
            if runs <= 0:
                break


if __name__ == "__main__":
    main(sys.argv[1:])