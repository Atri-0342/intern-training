Use strace (Linux) or dtruss (macOS) to trace the system calls made by a command like ls -l. What system calls is it making? Try tracing a more complex program and see what files it opens.

I used strace on Linux to see the system calls made by ls -l.

Command used:

strace ls -l

There were many system calls. Some important ones I observed were:

execve() — starts the ls program.
openat() — opens files or directories.
getdents64() — reads directory entries.
newfstatat() — gets information about files and directories.
read() — reads data.
write() — writes output to the terminal.
mmap() — maps memory.
close() — closes files.
exit_group() — exits the program.

## What I learned

strace shows the system calls that a Linux program makes to interact with the operating system. It can be useful for debugging problems involving files, processes, and other operating-system resources.