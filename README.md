TODO need to explain parameters

TODO construct_intensity option:
    - intensity = 0: start with CONNECT, end with DISCONNECT. No ACKs allowed. No repeat packets.
    - intensity = 1: Packets can be arranged in any order. All packet types allowed. No repeat packets.
    - intensity = 2: Same as above. Packets can be repeated up to 3 times.
    - intensity = 3: Same as above. Packets can be repeated up to 10 times, and payloads themselves can be repeated up to 5 times.

TODO payloads that crash the broker should be used as input for other fuzz attempts. Just call fuzz_target on the payload we want to fuzz. Make sure duplicate packets are not saved to our log. Also, add a "sourced" option which indexes whuich payload we began with in our log.