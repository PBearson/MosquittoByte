TODO need to explain parameters

TODO we need a way to observe output from the broker besides just network traffic. This should be possible if we start the broker ourselves. Then we can look for key words like "Exception" or "Warning" in output from the broker, and we keep unique entries. Similar to how broker_responses works. We can build a corpus of key words.
    -Another possibility is just log everything that goes to stderr. But some error/warning messages may go to stdout. We have to check.

We may want to modify the crash behavior so that it only logs unique crashes, i.e., a crash which triggers SIGPIPE should only be logged once, even if the payloads are different.