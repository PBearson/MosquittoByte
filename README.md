TODO need to explain parameters

We may want to modify the crash behavior so that it only logs unique crashes, i.e., a crash which triggers SIGPIPE should only be logged once, even if the payloads are different.

TODO should maybe clean up the code

TODO should implement some kind of check in broker_start so that it only returns when the broker has started (since some brokers can initialize slowly)