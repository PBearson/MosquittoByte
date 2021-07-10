# Session properties:
#   - The set of client subscriptions (and subscription IDs)
#   - QoS 1 messages sent to the client, but not completely ACK'd
#   - QoS 2 messages sent to the client, but not completely ACK'd
#   - QoS 0 messages pending transmission to the client
#   - QoS 1 messages pending transmission to the client
#   - QoS 2 messages pending transmission to the client
#   - QoS 2 messages received from the client, but not completely ACK'd
#   - Client will message and will delay interval
#   - Session expiry time
#   - Whether or not the client is currently connected

class ClientSession:
    def __init__(self):
        return