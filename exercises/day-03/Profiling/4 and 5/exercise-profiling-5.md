A common issue is that a port you want to listen on is already taken by another process. Learn how to discover that process: First execute python -m http.server 4444 to start a minimal web server on port 4444. On a separate terminal run ss -tlnp | grep 4444 to find the process. Terminate it with kill <PID>.

# Exercise — Finding and Terminating a Process Using a Port

I started a Python HTTP server on port `4444`:

python3 -m http.server 4444

I then used `ss` and `grep` to find the process listening on that port:

ss -tlnp | grep 4444

The output was:

LISTEN 0 5 0.0.0.0:4444 0.0.0.0:* users:(("python3",pid=6050,fd=3))

This showed that a `python3` process with PID `6050` was using port `4444`.

I terminated the process with:

kill 6050

Finally, I checked the port again:

ss -tlnp | grep 4444

There was no output, confirming that the process was terminated and port `4444` was available again.

### What I learned

When a port is already being used, `ss` can be used to identify the process listening on that port. The PID can then be passed to `kill` to terminate the process and release the port.

