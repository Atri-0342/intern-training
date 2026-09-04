Use perf stat to get basic performance statistics for a program of your choice. What do the different counters mean?

I created a simple C program called perf_test.c that performs a large loop and calculates a sum.

I compiled it with:

gcc -O2 -g perf_test.c -o perf_test

The normal program output was:

Result: 4999999950000000

I first tried:

perf stat ./perf_test

but the hardware performance counters were not available in my WSL2 environment.

I then used software counters:

perf stat -e task-clock,context-switches,cpu-migrations,page-faults ./perf_test

The result was:

0.61 msec task-clock
0      context-switches
0      cpu-migrations
58     page-faults
Where
task-clock — CPU time used by the program.
context-switches — number of times the operating system switched the CPU away from the process.
cpu migrations — number of times the process moved between CPU cores.
page faults — memory-page faults that occurred while the program was running.

The program also took about 0.006 seconds of elapsed time.

## What I learned

perf stat can provide basic performance information about a program. My WSL2 environment did not provide the required hardware PMU counters, but software counters such as task-clock, context-switches, CPU migrations, and page faults were available.