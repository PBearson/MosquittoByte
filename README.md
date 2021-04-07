# MosquittoByte

Mosquitto Byte is a versatile mutation-based fuzzer for MQTT brokers. It is written completely in Python, so it is largely portable. It can fuzz MQTT brokers on your local system or on remote servers. It can run for a fixed number of iterations or indefinitely. It can replay payloads that triggered interesting (or devastating) responses. It can display payload details (i.e., what packets were sent, and how were they fuzzed) without actually sending them. It can log network responses and even stdout/stderr responses, which may guide the fuzzing engine. It can send fuzzed packets in-order (e.g., CONNECT, SUBSCRIBE, DISCONNECT) or unfuzzed packets out-of-order (e.g., SUBSCRIBE, PUBREL, CONNECT). It can fuzz as fast or as slow as you want, as gently or intensely as you want. In short, it can do almost anything.

## Get Started

Assuming you have an MQTT broker running on your system (on port 1883), using Mosquitto Byte is as simple as this:

```
python mosquitto_byte.py
```

If you want to fuzz a remote broker, or if the broker is running on another port, you can customize the host/port as follows:

```
python mosquitto_byte.py -H <host> -P <port> 
```

Mosquitto Byte supports over 20 different options for customizing your fuzzing strategy. They will not all be covered here; however, you can see what is available to you by running the help option:

```
python mosquitto_byte.py -h
```

## Fuzzing Details

At its core, Mosquitto Byte is a simple mutation based fuzzer. Valid MQTT packets are sampled from the ___mqtt_corpus___ directory. Each packet can be fuzzed either by removing bytes, adding bytes, or mutating bytes. The number of bytes added, removed, or mutated is mostly random, but configurable. Furthermore, fuzzed packets can still be sent in a typical order (e.g., begin with CONNECT and end with DISCONNECT, never send server-to-client packets such as CONNACK, and so forth), or they can be sent out-of-order, which is also configurable. 

## The Outputs Directory

## Some Examples

## Findings

This section will be gradually updated as the software discovers more bugs.
