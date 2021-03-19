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

    # Randomize which operations we do
    fuzz_opts = ["mutate", "add", "remove"]

    fuzz_rounds = random.randint(params["min_fuzz_rounds"], params["max_fuzz_rounds"])
    for fr in range(fuzz_rounds):
        fuzz_selection = random.sample(fuzz_opts, random.randint(1, 3))
        for s in fuzz_selection:
            if s == "mutate":
                f = mutate(f, num_mutate_bytes)
            elif s == "add":
                f = add(f, num_add_bytes)
            elif s == "remove":
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
    min_mutate, max_mutate = get_min_max(0, 10 * intensity)
    min_add, max_add = get_min_max(0, 10 * intensity)
    super_add_min, super_add_max = get_min_max(0, 1000 * intensity)
    super_add_enable = random.randint(0, 30)
    min_remove, max_remove = get_min_max(0, 10 * intensity)
    min_fuzz_rounds, max_fuzz_rounds = get_min_max(0, intensity)

    params = {
        "min_mutate": min_mutate, 
        "max_mutate": max_mutate, 
        "min_add": min_add, 
        "max_add": max_add, 
        "super_add_enable": super_add_enable, 
        "super_add_min": super_add_min,
        "super_add_max": super_add_max,
        "min_remove": min_remove,
        "max_remove": max_remove,
        "min_fuzz_rounds": min_fuzz_rounds,
        "max_fuzz_rounds": max_fuzz_rounds
        }
    return params

def construct_payload(all_payloads):
    # TODO
    payload = all_payloads["connect"] + all_payloads["publish"] + all_payloads["disconnect"]
    return payload
    

# Fuzz MQTT
# params: A dictionary with various parameters
def fuzz(seed):

    random.seed(seed)

    params = get_params()

    all_payloads = {
        "connect": get_payload("mqtt_corpus/CONNECT"),
        "auth": get_payload("mqtt_corpus/AUTH"),
        "publish": get_payload("mqtt_corpus/PUBLISH"),
        "disconnect": get_payload("mqtt_corpus/DISCONNECT")
    }

    all_payloads["connect"] = fuzz_target(all_payloads["connect"], params)
    all_payloads["auth"] = fuzz_target(all_payloads["auth"], params)
    all_payloads["publish"] = fuzz_target(all_payloads["publish"], params)
    all_payloads["disconnect"] = fuzz_target(all_payloads["disconnect"], params)

    payload = construct_payload(all_payloads)
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
    parser.add_argument("-m", "--max_runs", help = "Set the number of fuzz attempts made. If not set, the fuzzer will run indefinitely.")
    parser.add_argument("-i", "--intensity", help = "Set the intensity of the fuzzer, from 0 to 10. 0 means packets are not fuzzed at all. Default is 3.")
    parser.add_argument("-ai", "--autonomous_intensity", help = "If set, the intensity randomly changes every 1000 runs", action="store_true")
    parser.add_argument("-p", "--params_only", help = "Do not fuzz. Simply return the parameters based on the seed value.", action = "store_true")

    args = parser.parse_args()

    global host, port, intensity

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

    if(args.intensity):
        intensity = int(args.intensity)
        if intensity > 10:
            intensity = 10
        if intensity < 0:
            intensity = 0
    else:
        intensity = 3

    if(args.max_runs):
        max_runs = int(args.max_runs)

    if(args.autonomous_intensity):
        autonomous_intensity = True
    else:
        autonomous_intensity = False


    print("Hello fellow fuzzer :)")
    print("Host: %s, Port: %d" % (host, port))
    print("Base seed: ", seed)
    print("Intensity: ", intensity)

    if(args.params_only):
        random.seed(seed)
        params = get_params()
        print("Your params: ", params)
        exit()

    total_runs = 0
    while True:
        fuzz(seed)
        time.sleep(fuzz_delay)
        total_runs += 1
        seed += 1
        if 'max_runs' in locals():
            max_runs -= 1
            if max_runs <= 0:
                break

        if total_runs % 1000 == 0 and autonomous_intensity:
            intensity = (intensity + 1) % 11
            print("Changed intensity to", intensity)


if __name__ == "__main__":
    main(sys.argv[1:])