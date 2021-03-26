import socket
import random
import time
import sys
import argparse
import math
import os
import os.path
import select
import subprocess
import difflib
import threading

from os import path
from datetime import datetime
from difflib import SequenceMatcher

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

def get_all_payloads():
    all_payloads = {
        "connect": get_payload("mqtt_corpus/CONNECT"),
        "connack": get_payload("mqtt_corpus/CONNACK"),
        "pingreq": get_payload("mqtt_corpus/PINGREQ"),
        "pingresp": get_payload("mqtt_corpus/PINGRESP"),
        "auth": get_payload("mqtt_corpus/AUTH"),
        "publish": get_payload("mqtt_corpus/PUBLISH"),
        "puback": get_payload("mqtt_corpus/PUBACK"),
        "pubrec": get_payload("mqtt_corpus/PUBREC"),
        "pubrel": get_payload("mqtt_corpus/PUBREL"),
        "pubcomp": get_payload("mqtt_corpus/PUBCOMP"),
        "subscribe": get_payload("mqtt_corpus/SUBSCRIBE"),
        "suback": get_payload("mqtt_corpus/SUBACK"),
        "unsubscribe": get_payload("mqtt_corpus/UNSUBSCRIBE"),
        "unsuback": get_payload("mqtt_corpus/UNSUBACK"),
        "disconnect": get_payload("mqtt_corpus/DISCONNECT"),
        "reserved": get_payload("mqtt_corpus/RESERVED")
    }
    return all_payloads


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

def source_payload_with_response(params):
    f = open("broker_responses.txt", "r")
    packets = f.read().splitlines()[1:]
    selection_index = random.randint(0, len(packets) - 1)
    selection = packets[selection_index].split(",")[0]
    payload = bytearray.fromhex(selection)
    f.close()
    
    return payload, fuzz_target(payload, params), selection_index

def source_payload_with_crash(params):
    f = open("crashes.txt", "r")
    packets = f.read().splitlines()[1:]
    selection_index = random.randint(0, len(packets) - 1)
    selection = packets[selection_index].split(",")[9]
    payload = bytearray.fromhex(selection)
    f.close()
    
    return payload, fuzz_target(payload, params), selection_index

# Return a tuple (a, b) where a and b are between abs_min and abs_max and a <= b
def get_min_max(abs_min, abs_max):
    a = random.randint(abs_min, abs_max)
    b = random.randint(abs_min, abs_max)
    if a < b:
        return (a, b)
    return (b, a)

def get_params():
    min_mutate, max_mutate = get_min_max(0, 10 * fuzz_intensity)
    min_add, max_add = get_min_max(0, 10 * fuzz_intensity)
    super_add_min, super_add_max = get_min_max(0, 1000 * fuzz_intensity)
    super_add_enable = random.randint(0, 50)
    min_remove, max_remove = get_min_max(0, 10 * fuzz_intensity)
    min_fuzz_rounds, max_fuzz_rounds = get_min_max(0, fuzz_intensity)

    if source_frequency == 0:
        sourcing = 1
    elif source_frequency == 1:
        sourcing = random.randint(0, 100)
    elif source_frequency == 2:
        sourcing = random.randint(0, 10)
    elif source_frequency == 3:
        sourcing = random.randint(0, 1)
    else:
        sourcing = 0

    if response_frequency == 0:
        responding = 1
    elif response_frequency == 1:
        responding = random.randint(0, 100)
    elif response_frequency == 2:
        responding = random.randint(0, 10)
    elif response_frequency == 3:
        responding = random.randint(0, 1)
    else:
        responding = 0

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
        "max_fuzz_rounds": max_fuzz_rounds,
        "sourcing": sourcing,
        "responding": responding
        }
    return params

def check_duplicate_source(payload):
    f = open("crashes.txt", "r")
    packets = f.read().splitlines()[1:]
    f.close()

    for p in packets:
        curr = p.split(",")[9].strip(" ")
        if payload.hex() == curr:
            return True
    return False

# Check for duplicate responses in the broker response log.
# This includes responses that are too similar, but not exactly
# duplicates.
def check_duplicate_response(response):
    f = open("broker_responses.txt", "r")
    packets = f.read().splitlines()[1:]
    f.close()

    for p in packets:
        curr = p.split(",")[1].strip(" ")
        similarity = SequenceMatcher(None, curr, response.hex()).ratio()
        if similarity >= max_response_threshold:
            return True
    return False


def get_last_index():
    try:
        f = open("crashes.txt", "r")
        last_entry = f.read().splitlines()[-1]
        last_index = last_entry.split(",")[0]
        f.close()
        return int(last_index)
    except (FileNotFoundError, ValueError):
        return -1

def handle_broker_response(payload, response):
    if not path.exists("broker_responses.txt"):
        f = open("broker_responses.txt", "w")
        f.write("Payload, Response\n")
        f.close()

    duplicate_response = check_duplicate_response(response)

    f = open("broker_responses.txt", "r")
    f_len = len(f.read().splitlines())
    f.close()

    if not duplicate_response and f_len < max_response_entries:
        f = open("broker_responses.txt", "a")
        f.write("%s, %s\n" % (payload.hex(), response.hex()))
        f.close()
        f = open("broker_responses_raw.txt", "a")
        f.write("%s\n" % response.hex())
        f.close()

def handle_stream_response(proc):
    for line in iter(proc.stdout.readline, b''):
        print(line.decode('latin'))

def start_broker():
    proc = subprocess.Popen([broker_exe], stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    t = threading.Thread(target=handle_stream_response, args=(proc,))
    t.start()

def handle_crash():
    if "last_fuzz" not in globals():
        if verbosity >= 5:
            print("There was an error connecting to the broker.")
        try:
            start_broker()
        except NameError:
            print("No MQTT process appears to be running at %s:%s, and you have not defined a broker exe. You must do one or the other." % (host, port))
            exit()
    else:
        if not path.exists("crashes.txt"):
            f = open("crashes.txt", "w")
            f.write("Index, Timestamp, Seed, Fuzz intensity, Construct intensity, Source Index, Response Index, Source Frequency, Response Frequency, Payload\n")
            f.close()

        seed = last_fuzz["seed"]
        fi = last_fuzz["fuzz_intensity"]
        ci = last_fuzz["construct_intensity"]
        si = last_fuzz["source_index"]
        ri = last_fuzz["response_index"]
        sf = last_fuzz["source_frequency"]
        rf = last_fuzz["response_frequency"]
        payload = last_fuzz["payload"]
        if verbosity >= 1:
            print("The following payload crashed the program")
            print(payload.hex())

        index = get_last_index() + 1
        duplicate_source = check_duplicate_source(payload)
        if not duplicate_source:
            f = open("crashes.txt", "a")
            f.write("%s, %s, %s, %s, %s, %s, %s, %s, %s, %s\n" % (index, datetime.now(), seed, fi, ci, si, ri, sf, rf, payload.hex()))
            f.close()
            f = open("crashes_raw.txt", "a")
            f.write("%s\n" % payload.hex())
            f.close()

        if not restart_on_crash:
            exit()
        else:
            subprocess.Popen([broker_exe], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            if(verbosity >= 3):
                print("Waiting a second to restart the broker")
            time.sleep(0.01)

# Construct the payload according the construct intensity
def construct_payload(all_payloads):
    selected_payloads = []

    if construct_intensity == 0:
        allowed_payloads = ["auth", "pingreq", "pubcomp", "publish", "pubrec", "pubrel", "subscribe", "unsubscribe"]
        payloads_subset = {e: all_payloads[e] for e in allowed_payloads}

        selected_payloads.append("connect")
        key, val = random.choice(list(payloads_subset.items()))
        selected_payloads.append(key)
        selected_payloads.append("disconnect")

    elif construct_intensity == 1:
        allowed_payloads = ["auth", "pingreq", "pubcomp", "publish", "pubrec", "pubrel", "subscribe", "unsubscribe"]
        payloads_subset = {e: all_payloads[e] for e in allowed_payloads}

        num_packets = random.randint(1, 5)
        selected_payloads = dict(random.sample(list(payloads_subset.items()), num_packets)).keys()

    elif construct_intensity == 2:
        num_packets = random.randint(1, 10)
        selected_payloads = dict(random.sample(list(all_payloads.items()), num_packets)).keys()
    else:
        num_packets = random.randint(1, 20)
        for n in range(num_packets):
            key, val = random.choice(list(all_payloads.items()))
            selected_payloads.append(key)
    
    enumerated_payloads = {}
    payload = b""
    for s in selected_payloads:
        payload = payload + all_payloads[s]
        enumerated_payloads[s] = all_payloads[s]
    
    return (payload, enumerated_payloads)
    
def fuzz_payloads(all_payloads, params):
    for a in all_payloads:
        all_payloads[a] = fuzz_target(all_payloads[a], params)
    return all_payloads

# Fuzz MQTT
f_len = -1
r_len = -1

def fuzz(seed):

    global last_fuzz, f_len, r_len

    random.seed(seed)

    params = get_params()

    if f_len == -1:
        # Get number of entries in crash file so far
        try:
            f = open("crashes.txt", "r")
            f_len = len(f.read().splitlines())
            f.close()
        except FileNotFoundError:
            f_len = -1
    if r_len == -1:
        # Get number of entries in response file so far
        try:
            r = open("broker_responses.txt", "r")
            r_len = len(r.read().splitlines())
            r.close()
        except FileNotFoundError:
            r_len = -1

    sourced_index = None
    response_index = None

    # Don't source the fuzzer with a previous crash
    if (f_len < 2 or not params["sourcing"] == 0) and (r_len < 2 or not params["responding"] == 0):
        all_payloads = get_all_payloads()
        all_payloads = fuzz_payloads(all_payloads, params)
        payload, enumerated_payloads = construct_payload(all_payloads)

    # Source with previous crash
    elif f_len >= 2 and params["sourcing"] == 0:
        unfuzzed_payload, payload, sourced_index = source_payload_with_crash(params)

    # Source with broker
    else:
        unfuzzed_payload, payload, response_index = source_payload_with_response(params)

    
    if payload_only:
        print("\nSourced index:\t\t" + str(sourced_index))
        print("Response index:\t\t" + str(response_index))
        if not params["sourcing"] == 0 and not params["responding"] == 0:
            print("\nFuzzed payload:\t" + payload.hex())
            for p in enumerated_payloads:
                print("%s: %s" % (p, enumerated_payloads[p].hex()))
        else:
            print("\nFuzzed payload:\t" + payload.hex())     
        exit()


    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.connect((host, port))
        s.send(payload)
    except ConnectionRefusedError:
        handle_crash()
        return

    if(verbosity >= 4):
        print("Sourced index:\t\t", sourced_index)
        print("Response index:\t\t", response_index)

    if(verbosity >= 1):
        print("Fuzzed payload:\t\t", payload.hex())

    ready = select.select([s], [], [], response_delay)

    if ready[0]:
        try:
            response = s.recv(1024)
            if not no_response_log:
                handle_broker_response(payload, response)
            if verbosity >= 5:
                print("Broker response:\t", response.hex())
        except ConnectionResetError:
            if verbosity >= 4:
                print("Error:\t\t\t Broker reset connection.")
    else:
        if verbosity >= 4:
            print("Error:\t\t\tBroker was not ready for reading.")
    s.close()

    # Update the last fuzz params
    last_fuzz = {
        "seed": seed,
        "fuzz_intensity": fuzz_intensity,
        "construct_intensity": construct_intensity,
        "source_index": sourced_index,
        "response_index": response_index,
        "source_frequency": source_frequency,
        "response_frequency": response_frequency,
        "payload": payload
    }    

def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("-H", "--host", help = "Fuzzing target host. Default is localhost.")
    parser.add_argument("-P", "--port", help = "Fuzzing target port. Default is 1883.")
    parser.add_argument("-B", "--broker_exe", help = "Set the broker exe location. If the broker crashes, this can be used to restart it.")
    parser.add_argument("-R", "--restart_on_crash", help = "If set, the fuzzer will try to use the option provided by 'broker_exe' to restart the broker.", action = "store_true")
    parser.add_argument("-s", "--seed", help = "Set the seed. If not set by the user, the system time is used as the seed.")
    parser.add_argument("-fd", "--fuzz_delay", help = "Set the delay between each fuzzing attempt. Default is 0.1 seconds.")
    parser.add_argument("-I", "--index", help = "Source the fuzzer using an index in the crashes.txt log file.")
    parser.add_argument("-rd", "--response_delay", help="Set the delay between sending a packet and receiving the response from the broker. Default is whatever fuzz delay is set to.")
    parser.add_argument("-m", "--max_runs", help = "Set the number of fuzz attempts made. If not set, the fuzzer will run indefinitely.")
    parser.add_argument("-fi", "--fuzz_intensity", help = "Set the intensity of the fuzzer, from 0 to 10. 0 means packets are not fuzzed at all. Default is 3.")
    parser.add_argument("-ci", "--construct_intensity", help = "Set the intensity of the payload constructer, from 0 to 3. The constructor decides what order to send packets. For example, 0 means all packets begin with CONNECT and end wth DISCONNECT. Default is 0.")
    parser.add_argument("-sf", "--source_frequency", help = "Set the frequency of sourcing the fuzzer's input with a packet that previously triggered a crash, from 0 to 4. 0 means never source and 4 means always source. Default is 2.")
    parser.add_argument("-rf", "--response_frequency", help = "Set the frequency of sourcing the fuzzer's input with a packet that previously triggered a unique response from the broker, from 0 to 4. 0 means never source and 4 means always source. Default is 3.")
    parser.add_argument("-mrt", "--max_response_threshold", help = "Set the maximum similarity threshold for entries in the broker response file, from 0 to 1. For example, a threshold of 0.3 means entries will be NOT logged if they are at least 30 percent similar to any other entry. Default is 0.7.")
    parser.add_argument("-mre", "--max_response_entries", help = "Set the maximum number of entries allowed in the broker responses file. Fuzzer will not write to this file if the number of entries exceeds this value. Default is 150.")
    parser.add_argument("-N", "--no_response_log", help = "If set, do not log unique responses from the broker to the broker responses file.", action="store_true")
    parser.add_argument("-a", "--autonomous_intensity", help = "If set, the fuzz intensity changes every 1000 runs and the construct intensity changes every 250 runs.", action="store_true")
    parser.add_argument("-v", "--verbosity", help = "Set verbosity, from 0 to 5. 0 means nothing is printed. Default is 1.")
    parser.add_argument("-p", "--payload_only", help = "Do not fuzz. Simply return the payload before and after it is fuzzed. Also return the params", action = "store_true")

    args = parser.parse_args()

    global host, port, broker_exe, fuzz_intensity, construct_intensity, source_frequency, response_frequency, construct_payload, payload_only, verbosity, response_delay, restart_on_crash, no_response_log, max_response_entries, max_response_threshold

    if(args.host):
        host = args.host
    else:
        host = "localhost"

    if(args.port):
        port = int(args.port)
    else:
        port = 1883

    if args.broker_exe:
        broker_exe = args.broker_exe
        if not path.exists(broker_exe):
            print("It seems like the broker exe you provided does not exist.")
            exit()
        else:
            start_broker()
            time.sleep(0.1)

    # This arg means we just source from an index in crashes.txt. Handy for verifying a crash quickly.
    if args.index:
        crash_index = int(args.index)
        f = open("crashes.txt", "r")
        selected_line = f.read().splitlines()[crash_index + 1].split(",")
        f.close()

        seed = int(selected_line[2])
        fuzz_intensity = int(selected_line[3])
        construct_intensity = int(selected_line[4])
        source_frequency = int(selected_line[7])
        response_frequency = int(selected_line[8])
    else:
        if(args.seed):  
            seed = int(args.seed)
        else:
            seed = math.floor(time.time())

        if(args.fuzz_intensity):
            fuzz_intensity = int(args.fuzz_intensity)
            if fuzz_intensity > 10:
                fuzz_intensity = 10
            if fuzz_intensity < 0:
                fuzz_intensity = 0
        else:
            fuzz_intensity = 3

        if(args.construct_intensity):
            construct_intensity = int(args.construct_intensity)
            if construct_intensity > 3:
                construct_intensity = 3
            if construct_intensity < 0:
                construct_intensity = 0
        else:
            construct_intensity = 0

        if(args.source_frequency):
            source_frequency = int(args.source_frequency)
            if source_frequency < 0:
                source_frequency = 0
            if source_frequency > 4:
                source_frequency = 4
        else:
            source_frequency = 2

        if(args.response_frequency):
            response_frequency = int(args.response_frequency)
            if response_frequency < 0:
                response_frequency = 0
            if response_frequency > 4:
                response_frequency = 4
        else:
            response_frequency = 3


    if(args.restart_on_crash):
        restart_on_crash = True
        if "broker_exe" not in globals():
            print("You cannot restart on crash if the broker exe is not defined.")
            exit()
    else:
        restart_on_crash = False    

    if(args.fuzz_delay):
        fuzz_delay = float(args.fuzz_delay)
    else:
        fuzz_delay = 0.1

    if(args.response_delay):
        response_delay = float(args.response_delay)
    else:
        response_delay = fuzz_delay

    if(args.max_runs):
        max_runs = int(args.max_runs)

    if(args.autonomous_intensity):
        autonomous_intensity = True
    else:
        autonomous_intensity = False

    if(args.verbosity):
        verbosity = int(args.verbosity)
        if verbosity > 5:
            verbosity = 5
        if verbosity < 0:
            verbosity = 0
    else:
        verbosity = 1

    if(args.no_response_log):
        no_response_log = True
    else:
        no_response_log = False

    if(args.max_response_entries):
        max_response_entries = int(args.max_response_entries)
    else:
        max_response_entries = 150

    if(args.max_response_threshold):
        max_response_threshold = float(args.max_response_threshold)
        if max_response_threshold < 0:
            max_response_threshold = 0
        if max_response_threshold > 1:
            max_response_threshold = 1
    else:
        max_response_threshold = 0.7

    print("Hello fellow fuzzer :)")
    print("Host: %s, Port: %d" % (host, port))
    print("Base seed: ", seed)
    print("Fuzz Intensity: ", fuzz_intensity)
    print("Construct intensity: ", construct_intensity)
    print("Source frequency: ", source_frequency)
    print("Response frequency: ", response_frequency)

    if(args.payload_only):
        payload_only = True
        random.seed(seed)
        params = get_params()
        print("\nYour params: ", params)
    else:
        payload_only = False

    total_runs = 1
    while True:

        if verbosity >= 1 and not payload_only:
            print("\nRun:\t\t\t", total_runs)

        if verbosity >= 3:
            print("Seed:\t\t\t", seed)

        if verbosity >= 4:
            print("Fuzz intensity:\t\t", fuzz_intensity)
            print("Construct intensity:\t", construct_intensity)

        fuzz(seed)
        time.sleep(fuzz_delay)
        total_runs += 1
        seed += 1
        
        if 'max_runs' in locals():
            max_runs -= 1
            if max_runs <= 0:
                break

        if total_runs % 1000 == 0 and autonomous_intensity:
            fuzz_intensity = (fuzz_intensity + 1) % 11

        if total_runs % 250 == 0 and autonomous_intensity:
            construct_intensity = (construct_intensity + 1) % 4

if __name__ == "__main__":
    main(sys.argv[1:])