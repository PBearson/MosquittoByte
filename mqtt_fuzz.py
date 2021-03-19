import socket
import random
import time
import sys
import argparse
import math

# Remove bytes in a string
# f : the fuzzable object
# nb : the number of bytes to remove in f
def remove(f, nb):
    for n in range(nb):
        base = random.randint(0, len(f))
        f = f[0:base] + f[base + 1:]

    return f

# Add bytes in a string
# f : the fuzzable object
# nb : the number of bytes to add to f
def add(f, nb):
    for n in range(nb):
        base = random.randint(0, len(f))
        byte = random.getrandbits(8).to_bytes(1, sys.byteorder)
        f = f[0:base] + byte + f[base:]

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

# Return c / 100 * len(f), where c is a random number between a and b
# a : a number between 0 and 100
# b : a number between a and 100
# f : the fuzzable object 
def select_param_value(f, a, b):
    if a == b:
        c = round(a / 100 * len(f))
    else:
        c = random.choice(range(a, b))
        c = round(c / 100 * len(f))
    return c

def fuzz_target(f, params):
    # Get number of bytes to mutate
    num_mutate_bytes = select_param_value(f, params["min_mutate"], params["max_mutate"])

    # Get number of bytes to add
    if params["super_add_enable"] == 0:
        num_add_bytes = random.randint(params["super_add_min"], params["super_add_max"])
    else:
        num_add_bytes = select_param_value(f, params["min_add"], params["max_add"])

    # Get number of bytes to remove
    num_remove_bytes = select_param_value(f, params["min_remove"], params["max_remove"])

    f = mutate(f, num_mutate_bytes)
    f = add(f, num_add_bytes)
    f = remove(f, num_remove_bytes)
    
    return f

# Return a tuple (a, b) where a and b are between abs_min and abs_max and a <= b
def get_min_max(abs_min, abs_max):
    a = random.randint(abs_min, abs_max)
    b = random.randint(abs_min, abs_max)
    if a < b:
        return (a, b)
    return (b, a)

def get_params():
    min_mutate, max_mutate = get_min_max(0, 100)
    min_add, max_add = get_min_max(0, 100)
    super_add_min, super_add_max = get_min_max(0, 10000)
    super_add_enable = random.randint(0, 30)
    min_remove, max_remove = get_min_max(0, 100)

    params = {
        "min_mutate": min_mutate, 
        "max_mutate": max_mutate, 
        "min_add": min_add, 
        "max_add": max_add, 
        "super_add_enable": super_add_enable, 
        "super_add_min": super_add_min,
        "super_add_max": super_add_max,
        "min_remove": min_remove,
        "max_remove": max_remove
        }
    return params

# Fuzz MQTT
# params: A dictionary with various parameters
def fuzz(seed):

    random.seed(seed)

    params = get_params()

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
        params = get_params()
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