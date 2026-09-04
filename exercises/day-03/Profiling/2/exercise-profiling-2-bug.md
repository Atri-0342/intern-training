# Exercise — Profiling with `perf record`

I created the provided `slow.c` program and compiled it with debug symbols:

gcc -g -O2 slow.c -o slow -lm

The program ran successfully:

Result: -122140.186478

I then tried to record a performance profile:

perf record -g ./slow

However, `perf` failed with:

failed to write perf data, error: Bad address

I also tried without call-graph recording:

perf record ./slow

but received the same error.

Because `perf record` could not create the profiling data in my WSL2 environment, I could not run `perf report` or generate a flame graph from the recorded data.

### What I learned

`perf record` is used to collect performance-sampling data from a running program. The `-g` option also records call-stack information, which can later be used by `perf report` to identify where the program spends its time.

In this environment, `perf stat` software counters worked, but `perf record` could not create the required profiling data.
