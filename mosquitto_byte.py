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

def source_payload_with_filestream_response(params):
    f = open(output_directory + "/filestream_responses.txt", "r")
    packets = f.readlines()[1:]
    selection_index = random.randint(0, len(packets) - 1)
    selection = packets[selection_index].split(",")[0]
    payload = bytearray.fromhex(selection)
    f.close()

    return fuzz_target(payload, params), selection_index

def source_payload_with_network_response(params):
    f = open(output_directory + "/network_responses.txt", "r")
    packets = f.read().splitlines()[1:]
    selection_index = random.randint(0, len(packets) - 1)
    selection = packets[selection_index].split(",")[0]
    payload = bytearray.fromhex(selection)
    f.close()
    
    return fuzz_target(payload, params), selection_index

def source_payload_with_crash(params):
    f = open(output_directory + "/crashes.txt", "r")
    packets = f.read().splitlines()[1:]
    selection_index = random.randint(0, len(packets) - 1)
    selection = packets[selection_index].split(",")[11]
    payload = bytearray.fromhex(selection)
    f.close()
    
    return fuzz_target(payload, params), selection_index

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

    # However non-intuitive, a sourcing value of 0 means that the fuzzer WILL source from that target. For example, if sourcing_from_crash = 0 (i.e., source_frequency = 4), then we will source from the crashes log.

    if source_frequency == 0:
        sourcing_from_crash = 1
    elif source_frequency == 1:
        sourcing_from_crash = random.randint(0, 100)
    elif source_frequency == 2:
        sourcing_from_crash = random.randint(0, 10)
    elif source_frequency == 3:
        sourcing_from_crash = random.randint(0, 1)
    else:
        sourcing_from_crash = 0

    if network_response_frequency == 0:
        sourcing_from_network = 1
    elif network_response_frequency == 1:
        sourcing_from_network = random.randint(0, 100)
    elif network_response_frequency == 2:
        sourcing_from_network = random.randint(0, 10)
    elif network_response_frequency == 3:
        sourcing_from_network = random.randint(0, 1)
    else:
        sourcing_from_network = 0

    if filestream_response_frequency == 0:
        sourcing_from_filestream = 1
    elif filestream_response_frequency == 1:
        sourcing_from_filestream = random.randint(0, 100)
    elif filestream_response_frequency == 2:
        sourcing_from_filestream = random.randint(0, 10)
    elif filestream_response_frequency == 3:
        sourcing_from_filestream = random.randint(0, 1)
    else:
        sourcing_from_filestream = 0

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
        "sourcing_from_crash": sourcing_from_crash,
        "sourcing_from_network": sourcing_from_network,
        "sourcing_from_filestream": sourcing_from_filestream
        }
    return params

def check_duplicate_source(payload):
    f = open(output_directory + "/crashes.txt", "r")
    packets = f.read().splitlines()[1:]
    f.close()

    for p in packets:
        curr = p.split(",")[11].strip(" ")
        if payload.hex() == curr:
            return True
    return False

# Check for duplicate responses in the broker response log.
# This includes responses that are too similar, but not exactly
# duplicates.
def check_duplicate_network_response(response):
    if not path.exists(output_directory + "/network_responses_raw.txt"):
        return False
    f = open(output_directory + "/network_responses_raw.txt", "r")
    packets = f.read().splitlines()
    f.close()

    for p in packets:
        similarity = SequenceMatcher(None, p, response.hex()).ratio()
        if similarity >= max_network_response_threshold:
            return True
    return False

# Check for duplicate responses in the stream response log.
# This includes responses that are too similar, but not exactly
# duplicates.
def check_duplicate_stream_response(response):
    if not path.exists(output_directory + "/filestream_responses_raw.txt"):
        return False

    f = open(output_directory + "/filestream_responses_raw.txt", "r")
    packets = f.read().splitlines()
    f.close()

    for p in packets:
        similarity = SequenceMatcher(None, p, response).ratio()
        if similarity >= max_filestream_response_threshold:
            return True
    return False
        

def get_last_index():
    try:
        f = open(output_directory + "/crashes.txt", "r")
        last_entry = f.read().splitlines()[-1]
        last_index = last_entry.split(",")[0]
        f.close()
        return int(last_index)
    except (FileNotFoundError, ValueError):
        return -1

def handle_network_response(payload, response):
    if not path.exists(output_directory + "/network_responses.txt"):
        f = open(output_directory + "/network_responses.txt", "w")
        f.write("Payload, Response\n")
        f.close()

    duplicate_response = check_duplicate_network_response(response)

    f = open(output_directory + "/network_responses.txt", "r")
    f_len = len(f.read().splitlines())
    f.close()

    if not duplicate_response and f_len < max_network_response_entries:
        f = open(output_directory + "/network_responses.txt", "a")
        f.write("%s, %s\n" % (payload.hex(), response.hex()))
        f.close()
        f = open(output_directory + "/network_responses_raw.txt", "a")
        f.write("%s\n" % response.hex())
        f.close()

def stream_response_has_keyword(resp, payload):
    f = open("keywords.txt", "r")
    keywords = f.read().splitlines()
    for k in keywords:
        if k.upper() in resp.upper():
            return True
    return False

def handle_stream_response(proc):
    if not path.exists(output_directory + "/filestream_responses.txt"):
        f = open(output_directory + "/filestream_responses.txt", "w")
        f.write("Payload, Response\n")
        f.close()

    for line in iter(proc.stdout.readline, b''):

        # Remove in-line EOL characters
        line = line.decode("latin").replace(r"\n", "").replace(r"\r", "")

        if "current_payload" in globals():
            has_keyword = stream_response_has_keyword(line, current_payload)
            duplicate_response = check_duplicate_stream_response(line)
            if has_keyword and not duplicate_response:
                f = open(output_directory + "/filestream_responses.txt", "a")
                f.write("%s, %s" % (current_payload.hex(),line))
                f.close()
                f = open(output_directory + "/filestream_responses_raw.txt", "a")
                f.write(line)
                f.close()

def start_broker():
    try:
        proc = subprocess.Popen(broker_exe.split(), stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        broker_thread = threading.Thread(target=handle_stream_response, args=(proc,))
        broker_thread.start()

        if verbosity >= 1:
            print("Waiting for broker to start")
        while True:
            s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            try:
                s.connect((host, port))
                s.close()
                break
            except ConnectionRefusedError:
                time.sleep(0.1)

    except FileNotFoundError:
        print("The broker command/location you provided does not exist.")
        exit()

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
        if not path.exists(output_directory + "/crashes.txt"):
            f = open(output_directory + "/crashes.txt", "w")
            f.write("Index, Timestamp, Seed, Fuzz intensity, Construct intensity, Crash index, Network response index, Filestream response index, Crash source frequency, Network source frequency, Filestream source frequency, Payload\n")
            f.close()

        seed = last_fuzz["seed"]
        fi = last_fuzz["fuzz_intensity"]
        ci = last_fuzz["construct_intensity"]
        si = last_fuzz["crash_index"]
        nri = last_fuzz["network_response_index"]
        fri = last_fuzz["filestream_response_index"]
        sf = last_fuzz["source_frequency"]
        nrf = last_fuzz["network_response_frequency"]
        frf = last_fuzz["filestream_response_frequency"]
        payload = last_fuzz["payload"]
        if verbosity >= 1:
            print("The following payload crashed the program")
            print(payload.hex())

        index = get_last_index() + 1
        duplicate_source = check_duplicate_source(payload)
        if not duplicate_source:
            f = open(output_directory + "/crashes.txt", "a")
            f.write("%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s\n" % (index, datetime.now(), seed, fi, ci, si, nri, fri, sf, nrf, frf, payload.hex()))
            f.close()
            f = open(output_directory + "/crashes_raw.txt", "a")
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
c_len = -1
nr_len = -1
fr_len = -1

def fuzz(seed):

    global last_fuzz, current_payload, c_len, nr_len, fr_len

    random.seed(seed)

    params = get_params()

    if c_len < 2:
        # Get number of entries in crash file so far
        try:
            f = open(output_directory + "/crashes.txt", "r")
            c_len = len(f.read().splitlines())
            f.close()
        except FileNotFoundError:
            c_len = -1
    if nr_len < 2:
        # Get number of entries in network response file so far
        try:
            f = open(output_directory + "/network_responses.txt", "r")
            nr_len = len(f.read().splitlines())
            f.close()
        except FileNotFoundError:
            nr_len = -1
    if fr_len < 2:
        # Get number of entries in filestream response file so far
        try:
            f = open(output_directory + "/filestream_responses.txt", "r")
            fr_len = len(f.read().splitlines())
            f.close()
        except FileNotFoundError:
            fr_len = -1

    crash_index = None
    network_response_index = None
    filestream_response_index = None

    # Order of preference for sourcing: crash log > filestream log > network log

    # Don't source the fuzzer with anything
    if (c_len < 2 or not params["sourcing_from_crash"] == 0) and (nr_len < 2 or not params["sourcing_from_network"] == 0) and (fr_len < 2 or not params["sourcing_from_filestream"] == 0):
        all_payloads = fuzz_payloads(get_all_payloads(), params)
        payload, enumerated_payloads = construct_payload(all_payloads)

    # Source with previous crash
    elif c_len >= 2 and params["sourcing_from_crash"] == 0:
        payload, crash_index = source_payload_with_crash(params)

    # Source with filestream response
    elif fr_len >= 2 and params["sourcing_from_filestream"] == 0:
        payload, filestream_response_index = source_payload_with_filestream_response(params)

    # Source with network response
    else:
        payload, network_response_index = source_payload_with_network_response(params)

    
    if payload_only:
        print("\nCrash index: " + str(crash_index))
        print("Network response index: " + str(network_response_index))
        print("Filestream response index: " + str(filestream_response_frequency))
        if not params["sourcing_from_crash"] == 0 and not params["sourcing_from_network"] == 0 and not params["sourcing_from_filestream"] == 0:
            print("\nFuzzed payload:\t" + payload.hex())
            for p in enumerated_payloads:
                print("%s: %s" % (p, enumerated_payloads[p].hex()))
        else:
            print("\nFuzzed payload:\t" + payload.hex())     
        exit()


    current_payload = payload

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        s.connect((host, port))
        s.send(payload)
    except ConnectionRefusedError:
        handle_crash()
        return

    if(verbosity >= 4):
        print("Crash log index:\t", crash_index)
        print("Network log index:\t", network_response_index)
        print("Filestream log index:\t", filestream_response_index)

    if(verbosity >= 1):
        print("Fuzzed payload:\t\t", payload.hex())

    ready = select.select([s], [], [], response_delay)

    if ready[0]:
        try:
            response = s.recv(1024)
            if not no_network_response_log:
                handle_network_response(payload, response)
            if verbosity >= 5:
                print("Network response:\t", response.hex())
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
        "crash_index": crash_index,
        "network_response_index": network_response_index,
        "filestream_response_index": filestream_response_index,
        "source_frequency": source_frequency,
        "network_response_frequency": network_response_frequency,
        "filestream_response_frequency": filestream_response_frequency,
        "payload": payload
    }    

def main(argv):
    parser = argparse.ArgumentParser()
    parser.add_argument("-H", "--host", help = "Fuzzing target host. Default is localhost.")
    parser.add_argument("-P", "--port", help = "Fuzzing target port. Default is 1883.")
    parser.add_argument("-B", "--broker_exe", help = "Set the broker exe command/location. If the broker crashes, this can be used to restart it.")
    parser.add_argument("-R", "--restart_on_crash", help = "If set, the fuzzer will try to use the option provided by 'broker_exe' to restart the broker.", action = "store_true")
    parser.add_argument("-s", "--seed", help = "Set the seed. If not set by the user, the system time is used as the seed.")
    parser.add_argument("-fd", "--fuzz_delay", help = "Set the delay between each fuzzing attempt. Default is 0.1 seconds.")
    parser.add_argument("-I", "--index", help = "Source the fuzzer using an index in the crashes.txt log file.")
    parser.add_argument("-rd", "--response_delay", help="Set the delay between sending a packet and receiving the response from the broker. Default is whatever fuzz delay is set to.")
    parser.add_argument("-m", "--max_runs", help = "Set the number of fuzz attempts made. If not set, the fuzzer will run until the broker crashes.")
    parser.add_argument("-fi", "--fuzz_intensity", help = "Set the intensity of the fuzzer, from 0 to 10. 0 means packets are not fuzzed at all. Default is 3.")
    parser.add_argument("-ci", "--construct_intensity", help = "Set the intensity of the payload constructer, from 0 to 3. The constructor decides what order to send packets. For example, 0 means all packets begin with CONNECT and end wth DISCONNECT. Default is 0.")
    parser.add_argument("-sf", "--source_frequency", help = "Set the frequency of sourcing the fuzzer's input with a packet that previously triggered a crash, from 0 to 4. 0 means never source and 4 means always source. Default is 2.")
    parser.add_argument("-nrf", "--network_response_frequency", help = "Set the frequency of sourcing the fuzzer's input with a packet that previously triggered a unique network response from the broker, from 0 to 4. 0 means never source and 4 means always source. Default is 2.")
    parser.add_argument("-frf", "--filestream_response_frequency", help = "Set the frequency of sourcing the fuzzer's input with a packet that previously triggered an anamolous response to stdout or stderr, from 0 to 4. 0 means never source and 4 means always source. Default is 2.")
    parser.add_argument("-mnt", "--max_network_response_threshold", help = "Set the maximum similarity threshold for entries in the broker response file, from 0 to 1. For example, a threshold of 0.3 means entries will be NOT logged if they are at least 30 percent similar to any other entry. Default is 0.5.")
    parser.add_argument("-mft", "--max_filestream_response_threshold", help = "Set the maximum similarity threshold for entries in the filestream response file, from 0 to 1. Default is 0.5.")
    parser.add_argument("-mne", "--max_network_response_entries", help = "Set the maximum number of entries allowed in the broker responses file. Fuzzer will not write to this file if the number of entries exceeds this value. Default is 150.")
    parser.add_argument("-nnl", "--no_network_response_log", help = "If set, do not log network responses from the broker.", action="store_true")
    parser.add_argument("-a", "--autonomous_intensity", help = "If set, the fuzz intensity changes every 1000 runs and the construct intensity changes every 250 runs.", action="store_true")
    parser.add_argument("-v", "--verbosity", help = "Set verbosity, from 0 to 5. 0 means nothing is printed. Default is 1.")
    parser.add_argument("-p", "--payload_only", help = "Do not fuzz. Simply return the payload before and after it is fuzzed. Also return the params", action = "store_true")
    parser.add_argument("-O", "--output_directory", help = "Set the output directory for files generated by the fuzzer. Default is 'outputs.")

    args = parser.parse_args()

    global host, port, broker_exe, fuzz_intensity, construct_intensity, source_frequency, network_response_frequency, filestream_response_frequency, construct_payload, payload_only, verbosity, response_delay, restart_on_crash, no_network_response_log, max_network_response_entries, max_network_response_threshold, max_filestream_response_threshold, output_directory, output_directory

    if(args.host):
        host = args.host
    else:
        host = "localhost"

    if(args.port):
        port = int(args.port)
    else:
        port = 1883

    if args.output_directory:
        output_directory = args.output_directory
    else:
        output_directory = "outputs"
    if not path.exists(output_directory):
        os.mkdir(output_directory)

    # This arg means we just source from an index in crashes.txt. Handy for verifying a crash quickly.
    if args.index:
        crash_index = int(args.index)
        f = open(output_directory + "/crashes.txt", "r")
        selected_line = f.read().splitlines()[crash_index + 1].split(",")
        f.close()

        seed = int(selected_line[2])
        fuzz_intensity = int(selected_line[3])
        construct_intensity = int(selected_line[4])
        source_frequency = int(selected_line[8])
        network_response_frequency = int(selected_line[9])
        filestream_response_frequency = int(selected_line[10])
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

        if(args.network_response_frequency):
            network_response_frequency = int(args.network_response_frequency)
            if network_response_frequency < 0:
                network_response_frequency = 0
            if network_response_frequency > 4:
                network_response_frequency = 4
        else:
            network_response_frequency = 2

        if(args.filestream_response_frequency):
            filestream_response_frequency = int(args.filestream_response_frequency)
            if filestream_response_frequency < 0:
                filestream_response_frequency = 0
            if filestream_response_frequency > 4:
                filestream_response_frequency = 4
        else:
            filestream_response_frequency = 2  

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

    if(args.no_network_response_log):
        no_network_response_log = True
    else:
        no_network_response_log = False

    if(args.max_network_response_entries):
        max_network_response_entries = int(args.max_network_response_entries)
    else:
        max_network_response_entries = 150

    if(args.max_network_response_threshold):
        max_network_response_threshold = float(args.max_network_response_threshold)
        if max_network_response_threshold < 0:
            max_network_response_threshold = 0
        if max_network_response_threshold > 1:
            max_network_response_threshold = 1
    else:
        max_network_response_threshold = 0.5

    if(args.max_filestream_response_threshold):
        max_filestream_response_threshold = float(args.max_filestream_response_threshold)
        if max_filestream_response_threshold < 0:
            max_filestream_response_threshold = 0
        if max_filestream_response_threshold > 1:
            max_filestream_response_threshold = 1
    else:
        max_filestream_response_threshold = 0.5

    if(args.payload_only):
        payload_only = True
        random.seed(seed)
        params = get_params()
        print("\nYour params: ", params)
    else:
        payload_only = False

    if args.broker_exe and not payload_only:
        broker_exe = args.broker_exe
        start_broker()
        time.sleep(0.1)

    if(args.restart_on_crash):
        restart_on_crash = True
        if "broker_exe" not in globals():
            print("You cannot restart on crash if the broker exe is not defined.")
            exit()
    else:
        restart_on_crash = False  


        print("Hello fellow fuzzer :)")
    print("Host: %s, Port: %d" % (host, port))
    print("Base seed: ", seed)
    print("Fuzz Intensity: ", fuzz_intensity)
    print("Construct intensity: ", construct_intensity)
    print("Source frequency: ", source_frequency)
    print("Network response frequency: ", network_response_frequency)
    print("Filestream response frequency: ", filestream_response_frequency)
    print("\n")

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
                exit()

        if total_runs % 1000 == 0 and autonomous_intensity:
            fuzz_intensity = (fuzz_intensity + 1) % 11

        if total_runs % 250 == 0 and autonomous_intensity:
            construct_intensity = (construct_intensity + 1) % 4

if __name__ == "__main__":
    main(sys.argv[1:])