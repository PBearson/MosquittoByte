from boofuzz import *
import random

def main():
    port = 1883
    host = "127.0.0.1"

    connection = SocketConnection(host, port, proto = "tcp")
    proc = ProcessMonitor(host, 26002)
    proc_opts = ({
        "start_commands": ["/usr/sbin/mosquitto"],
    })
    proc.set_options(proc_opts)

    target = Target(connection = connection)

    session = Session(target = target, restart_threshold = 1, restart_sleep_time = 0)

    connect_payloads = []
    post_payloads = []
    disconnect_payloads = []
    post_files = [
        "mqtt_corpus/AUTH",
        "mqtt_corpus/CONNACK",
        "mqtt_corpus/PINGREQ",
        "mqtt_corpus/PINGRESP",
        "mqtt_corpus/PUBACK",
        "mqtt_corpus/PUBCOMP",
        "mqtt_corpus/PUBLISH",
        "mqtt_corpus/PUBREC",
        "mqtt_corpus/RESERVED",
        "mqtt_corpus/SUBACK",
        "mqtt_corpus/SUBSCRIBE",
        "mqtt_corpus/UNSUBACK",
        "mqtt_corpus/UNSUBSCRIBE",
    ]

    f_connect = open("mqtt_corpus/CONNECT", "r")
    for f in f_connect.readlines():
        connect_payloads.append(f)

    f_disconnect = open("mqtt_corpus/DISCONNECT", "r")
    for f in f_disconnect.readlines():
        disconnect_payloads.append(f)  
    
    for p in post_files:
        f_p = open(p, "r")
        for f in f_p.readlines():
            post_payloads.append(f)

    random.shuffle(connect_payloads)
    random.shuffle(post_payloads)

    index = 0
    for c in connect_payloads:
        for p in post_payloads:
            for d in disconnect_payloads:
                s_initialize("run_" + str(index))
                s_bytes(bytearray.fromhex(c))
                s_bytes(bytearray.fromhex(p))
                s_bytes(bytearray.fromhex(d), fuzzable = False)
                session.connect(s_get("run_" + str(index)))
                index += 1

    session.fuzz()

if __name__ == "__main__":
    main()
