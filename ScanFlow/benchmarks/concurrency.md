# Concurrency Benchmark

## Objective

The goal of this benchmark was to run the same workloads in four different ways:

1. Sequential
2. Threads
3. Processes
4. Asyncio

I used two different types of workloads because concurrency behaves very differently depending on whether the program is mostly **waiting for I/O** or **using the CPU**.

The purpose was not just to get faster timings, but to understand *why* each approach behaves differently and how the GIL affects CPU-bound Python code.

## Workloads

### I/O-bound workload

For the I/O test, I created a small local FastAPI server with a `/sleep` endpoint.

  
http://127.0.0.1:8000/sleep
 

Every request waits for 0.2 seconds before returning a response.

I sent 50 requests using each execution model.

The important part of this workload is that the program spends most of its time **waiting** for the server rather than doing CPU-heavy calculations.

### CPU-bound workload

For the CPU test, I calculated the sum of all prime numbers below:

  
2,000,000
 

The calculation was performed 8 times.

Unlike the I/O test, this workload spends most of its time actively using the CPU. There is very little waiting involved.

This makes it useful for seeing the difference between threads and processes in Python.

## Results

| Method     |      I/O-bound |       CPU-bound |
| Sequential | 10.376 seconds | 114.938 seconds |
| Threads    |  1.112 seconds | 108.669 seconds |
| Processes  |  2.090 seconds |  37.917 seconds |
| Asyncio    |  0.278 seconds | 111.193 seconds |

## Observations

### 1. Sequential execution

The sequential version is the easiest one to understand.

For the I/O workload, the program sends one request and waits for it to finish before sending the next one.

Each request takes approximately 0.2 seconds of server-side waiting time.

With 50 requests, the total waiting time is therefore roughly:

  
50 × 0.2 = 10 seconds
 

The measured result was:

  
10.376 seconds
 

So the result is very close to what we would expect.

The program is basically doing:

  
Request 1  -> wait
Request 2  -> wait
Request 3  -> wait
...
Request 50  -> wait
 

Nothing overlaps.

For the CPU workload, the same idea applies. The program calculates the prime sum once, finishes it, then starts the next calculation.

The result was:

  
114.938 seconds
 

This gives us a useful baseline for comparing the other approaches.

 

### 2. Threads for I/O-bound work

The threaded I/O version reduced the runtime from:

  
10.376 seconds  -> 1.112 seconds
 

This is a major improvement.

The reason is that the threads do not need to sit idle while waiting for the server.

For example, while one thread is waiting for:

  
Request A  -> server response
 

another thread can work on:

  
Request B  -> server response
 

So instead of doing:

  
Request 1  -> wait  -> finish
Request 2  -> wait  -> finish
Request 3  -> wait  -> finish
 

the program can have several requests waiting at the same time:

  
Request 1 ───── waiting ───── response
Request 2 ───── waiting ───── response
Request 3 ───── waiting ───── response
Request 4 ───── waiting ───── response
...
 

The CPU is not spending most of its time calculating something. It is spending a lot of time waiting for I/O.

That is exactly where threads can be useful.

The result:

  
1.112 seconds
 

shows that overlapping those waits makes a large difference.

For the CPU-bound workload, however, threads barely helped:

  
114.938 seconds  -> 108.669 seconds
 

That is only a small improvement.

The important thing is that eight threads do not mean eight Python CPU calculations are freely running in parallel inside the same process.

For traditional CPython, the GIL limits execution of Python bytecode to one thread at a time.

Therefore, the threads are competing for execution rather than giving us the kind of true CPU parallelism we were looking for.

There can still be small differences because of scheduling, interpreter behavior, system activity, and other overhead, but the benchmark does not show the large parallel speedup we saw with processes.

 

### 3. Processes for I/O-bound work

The process-based I/O version took:

  
2.090 seconds
 

This is still much faster than sequential execution:

  
10.376 seconds  -> 2.090 seconds
 

because multiple processes can work concurrently.

However, it was slower than both threads and asyncio:

  
Threads  -> 1.112 seconds
Processes  -> 2.090 seconds
Asyncio  -> 0.278 seconds
 

This makes sense for this particular workload.

Creating and managing separate processes has more overhead than creating threads or scheduling asyncio tasks.

Each process is a separate Python process with its own interpreter and memory space.

For a simple task such as:

  
send HTTP request  -> wait 0.2 seconds  -> receive response
 

that additional process overhead does not provide much benefit.

So although processes can handle I/O concurrently, this benchmark shows why that does not automatically make them the best choice for I/O-bound work.

### 4. Asyncio for I/O-bound work

Asyncio produced the fastest I/O result:

  
0.278 seconds
 

This was significantly faster than sequential execution:

  
10.376 seconds  -> 0.278 seconds
 

The important idea here is that asyncio does not create 50 operating-system threads or 50 processes.

Instead, the event loop manages many asynchronous tasks.

When one request is waiting for the server, the event loop can move on and allow another request to make progress.

Conceptually:

  
Task 1  -> waiting for response
              ->
Task 2  -> waiting for response
              ->
Task 3  -> waiting for response
              ->
Task 4  -> waiting for response
              ->
...
 

The event loop keeps the work moving instead of blocking on one request at a time.

Because all 50 requests were made against the same local server and the server mostly spent its time sleeping, there was a lot of waiting that could overlap.

That is why asyncio performed particularly well here.

The result of:

  
0.278 seconds
 

also shows an important point: the total runtime does not need to be close to:

  
50 × 0.2 = 10 seconds
 

when the waits are allowed to overlap.

 

## CPU-bound workload observations

The CPU results are where the difference between threads and processes becomes much clearer.

### Sequential CPU

The sequential implementation took:

  
114.938 seconds
 

This is our baseline.

The eight prime calculations were performed one after another:

  
Calculation 1
      ->
Calculation 2
      ->
Calculation 3
      ->
...
Calculation 8
 

There is no parallelism here.

 

### Threads for CPU-bound work

The threaded version took:

  
108.669 seconds
 

At first glance, it may look like threads helped because the number is slightly lower than 114.938 seconds.

However, the improvement is small compared with the process result.

The important observation is that the workload is pure Python CPU work.

The threads are not spending most of their time waiting for a network response, a file, or some other external resource.

They are trying to execute Python code continuously.

In traditional CPython, the GIL means that only one thread can execute Python bytecode at a time within a process.

So adding eight threads does not simply turn the workload into:

  
8 calculations running fully in parallel
 

Instead, the threads have to take turns getting access to Python execution.

That is why the result stayed close to the sequential result:

  
Sequential  -> 114.938 s
Threads     -> 108.669 s
 

The benchmark made the GIL effect visible rather than just explaining it theoretically.

 

### Processes for CPU-bound work

This was the most noticeable CPU result.

The process version took:

  
37.917 seconds
 

compared with:

  
Sequential  -> 114.938 seconds
Processes   -> 37.917 seconds
 

This is a much larger improvement.

The reason is that processes are separate Python processes.

Each process has its own Python interpreter and therefore its own GIL.

This means CPU-heavy Python calculations can actually execute on different CPU cores at the same time, assuming the machine has available cores.

Instead of:

  
One process -> Calculation 1 -> Calculation 2 -> ...
 
we can have multiple processes doing calculations concurrently:
  
Process 1  -> Calculation
Process 2  -> Calculation
Process 3  -> Calculation
Process 4  -> Calculation
.........................
 

The operating system can schedule those processes across multiple CPU cores.

That is why the process implementation showed a much larger reduction in runtime.

The result of:

  
37.917 seconds
 

was the clearest evidence from this benchmark that processes are useful for CPU-bound Python work.

There is still process creation and communication overhead, so the runtime does not simply become exactly:

  
114.938 / 8
 

The actual speedup depends on the number of CPU cores, process overhead, scheduling, workload size, and the machine itself.

 

### Asyncio for CPU-bound work

The asyncio CPU result was:

  
111.193 seconds
 

which is very close to the sequential result:

  
Sequential  -> 114.938 s
Asyncio     -> 111.193 s
 

This is expected because asyncio is mainly designed to handle situations where tasks spend time **waiting**, especially for I/O.

A CPU-heavy calculation does not naturally give the event loop opportunities to switch to another useful task.

So asyncio does not magically make CPU calculations run in parallel.

In this benchmark, the CPU workload was offloaded using `asyncio.to_thread()`. Therefore, this particular result is technically an asyncio-orchestrated thread workload rather than a pure event-loop CPU implementation.

That is also why its result is close to the threaded CPU result.

The important lesson is that simply putting CPU-heavy work inside an async application does not make that work parallel.

For genuinely CPU-heavy Python work, processes are the approach that demonstrated the substantial improvement in this benchmark.


## Comparing the two workloads

The most useful part of the benchmark is comparing the same four approaches across the two workload types.

### I/O-bound

  
Sequential  -> 10.376 s
Threads     ->  1.112 s
Processes   ->  2.090 s
Asyncio     ->  0.278 s
 

Here, concurrency helps because the program spends a large amount of time waiting.

While one operation is waiting for I/O, another operation can make progress.

Threads and asyncio take advantage of this particularly well.

Processes can also overlap the work, but their additional overhead makes them less efficient for this small I/O workload.

### CPU-bound

  
Sequential  -> 114.938 s
Threads     -> 108.669 s
Processes   ->  37.917 s
Asyncio     -> 111.193 s
 

Here, the situation is different.

The program is not mainly waiting. It is continuously performing CPU calculations.

Threads therefore do not provide the same kind of improvement because of the GIL.

Asyncio also does not provide CPU parallelism.

Processes are different because each process has its own interpreter and GIL, allowing the operating system to run CPU work across multiple cores.

 

## What I actually learned from the benchmark

Before running this benchmark, it is easy to think:

> "Concurrency means doing things at the same time, so threads, processes, and asyncio should all make everything faster."

The measurements showed why that is not true.

The type of work matters.

For the I/O workload, the biggest problem was **waiting**.

So the useful strategy was to overlap the waiting time.

For the CPU workload, the problem was **computation**.

In that case, overlapping I/O waits does not solve the problem. We need actual CPU parallelism, which processes provided in this benchmark.

The benchmark therefore made the following distinction much clearer:

  
If the program is mostly WAITING:
    Threads / Asyncio can help

If the program is mostly CALCULATING:
    Processes can provide real CPU parallelism
 

The GIL is an important part of why threads behaved differently for the CPU-bound workload.

## Rule derived from the benchmark

Based on the actual measurements from this benchmark:

I/O-bound: Threads , Asyncio
CPU-bound: Processes

The important part is not that one method is universally faster.

The correct choice depends on **what the program is spending its time doing**.

For a backend application such as ScanFlow, this distinction is especially useful.

API calls, database queries, file uploads, object-storage operations, and external service requests are generally I/O-heavy, so asynchronous programming or controlled thread concurrency can be useful.

On the other hand, if the application performs a genuinely CPU-heavy operation such as large-scale image processing, expensive numerical computation, or other CPU-intensive Python work, processes may be more appropriate.

This benchmark gave me a practical understanding of that distinction instead of only learning it as a theoretical rule.

