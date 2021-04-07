# MosquittoByte

Mosquitto Byte is a versatile mutation-based fuzzer for MQTT brokers. It is written completely in Python, so it is largely portable. It can fuzz MQTT brokers on your local system or on remote servers. It can run for a fixed number of iterations or indefinitely. It can replay payloads that triggered interesting (or devastating) responses. It can display payload details (i.e., what packets were sent, and how were they fuzzed) without actually sending them. It can log network responses and even stdout/stderr responses, which may guide the fuzzing engine. It can send fuzzed packets in-order (e.g., CONNECT, SUBSCRIBE, DISCONNECT) or unfuzzed packets out-of-order (e.g., SUBSCRIBE, PUBREL, CONNECT). It can fuzz as fast or as slow as you want, as gently or intensely as you want. In short, it can do almost anything.

## Get Started

## Fuzzing Strategies

## The Outputs Directory

## Some Commands of Interest

## Findings

This section will be gradually updated as the software discovers more bugs.
