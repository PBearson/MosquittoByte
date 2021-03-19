TODO randomize which packets we fuzz

TODO give the option of sending identical packets repeatedly

TODO track and log interesting results

TODO need to explain parameters

TODO need an argument for returning the selected packet before fuzzing and an argument for returning the selected packet after fuzzing (don't send the packet)

TODO add verbosity option

TODO options for constructing payload:
    - intensity = 0-3: start with CONNECT, end with DISCONNECT. No ACKs allowed. No repeat packets.
    - intensity = 4-6: Packets can be arranged in any order. All packet types allowed. No repeat packets.
    - intensity = 7-9: Same as above. Packets can be repeated up to 3 times.
    - intensity = 10: Same as above. Packets can be repeated up to 10 times, and payloads themselves can be repeated up to 5 times.