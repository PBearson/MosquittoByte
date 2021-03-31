TODO need to explain parameters

We may want to modify the crash behavior so that it only logs unique crashes, i.e., a crash which triggers SIGPIPE should only be logged once, even if the payloads are different.

Instead of steadily incrementing the intensity when autonomous option is used, just randomize the intensity.

TODO should maybe clean up the code

TODO need to add an option to not log to the filestream log