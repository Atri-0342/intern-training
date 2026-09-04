## 4. Docker — Temporary Ubuntu Container

I started a temporary Ubuntu container using:

```docker run -it --rm ubuntu bash```

docker run creates and starts a new container from the Ubuntu image.

The -it options allowed me to interact with the container through my terminal, while bash started a Bash shell inside the container.

The --rm option is important because it tells Docker to automatically remove the container when I exit it.

Once inside the container, I used `ps` to see the processes running inside it:

I saw that bash was running as `PID 1`, and the `ps` command itself appeared as another process.

I also used:

`top`

to see the running processes and resource usage in real time. I exited top by pressing `q`.

To understand how processes can be stopped, I created a background process:

`sleep 1000 &`

I used ps to find its PID and then stopped it with:

`kill <PID>`

After running ps again, the sleep process was no longer there.

Working with logs I created a simple log file inside the container:

```echo "INFO: Server started" > app.log
echo "INFO: User logged in" >> app.log
echo "ERROR: Database connection failed" >> app.log```

I used grep to search for a specific type of message:

```grep "ERROR" app.log````

This returned only the line containing ERROR.

I then used:

```tail -f app.log```

```tail -f``` showed the existing end of the log and continued watching the file for new lines.

While ```tail -f``` was running, I added another line to the log from another terminal using:

```docker exec <CONTAINER ID> bash -c 'echo "INFO: New user logged in" >> /app.log'```

Here, docker exec runs a command inside an already running container.

```bash -c``` tells Bash to execute the command given inside the quotes. The ">>" operator appends the new text to app.log instead of replacing the existing contents.

The new line appeared immediately in the terminal running tail -f, which showed how tail -f can be used to monitor a log while another process is writing to it.

Understanding "--rm"

Finally, I exited the container: "exit"

Because I started the container with --rm, Docker removed the container after it stopped.

This also meant that the "app.log" file I created inside the container was gone. The file was part of the container's temporary filesystem, so when the container was removed, the file was removed with it.

## What I learned

This exercise helped me understand that a Docker container is an isolated environment where I can run Linux commands and applications.

I practiced viewing processes with ps, monitoring them with top, stopping them with kill, searching logs with grep, and continuously watching logs with tail -f.

I also learned that files created inside a container are not automatically permanent. In this case, --rm caused the entire container and its filesystem changes, including app.log, to disappear when I exited.