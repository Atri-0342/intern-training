Use htop to monitor your system while running a resource-intensive program. Try using taskset to limit which CPUs a process can use: taskset --cpu-list 0,2 stress -c 3. Why doesn’t stress use three CPUs?

# Exercise — Monitoring CPU Usage with `htop` and `taskset`

I used `htop` to monitor CPU usage while running a CPU-intensive program.

I ran:

htop

I then used `taskset` to restrict the CPUs available to `stress`:

taskset --cpu-list 0,2 stress -c 3

### What the command means

* `taskset` — controls CPU affinity for a process.
* `--cpu-list 0,2` — allows the process to run only on CPU 0 and CPU 2.
* `stress` — creates artificial CPU workload.
* `-c 3` — creates 3 CPU workers.

### Why doesn't `stress` use three CPUs?

Although `stress -c 3` creates three workers, `taskset` restricts them to only **two CPUs: CPU 0 and CPU 2**.

Therefore, the three workers cannot run simultaneously on three different CPU cores. The third worker must share CPU 0 or CPU 2 with another worker.

### What I learned

`htop` can be used to observe CPU and process usage, while `taskset` can control which CPU cores a process is allowed to use. The number of workers a program creates does not necessarily equal the number of CPUs it can use because CPU affinity can restrict the available cores.
