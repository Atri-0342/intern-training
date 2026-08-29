## 02. Linux and things I Struggled With / Need More Practice

### Things I struggled with

- Understanding the difference between the Windows and Linux Python virtual environments `Scripts` vs `bin`.
- Understanding why WSL uses paths such as `/mnt/c/...` to access Windows files.
- Understanding how `xargs` works with commands such as `wc -l`.
- Understanding why `find` can return files from `.venv` and why virtual environments should be excluded.
- Understanding Linux file permissions, especially what the `x` permission means.
- Understanding the difference between a normal WSL terminal and a shell running inside a Docker container.
- Understanding how `docker exec` runs a command inside an already running container.
- Understanding why files such as `app.log` disappear when a container started with `--rm` is removed.

### Commands that I need more practice with

I understand the basic purpose of these commands, but I want more hands on practice with:

Level 1 — Linux Basics

pwd
ls
cd
mkdir
touch
cp
mv
rm
cat
less
head
tail

Level 2 — search & text

grep
find
sort
uniq
cut
sed
awk
xargs

Level 3 — permissions & processes

chmod
chown
ps
top
kill
jobs
bg
fg

Level 4 — shell environment

echo
env
export
which
history
man

Level 5 — system

df
du
free
uname

Level 6 — Docker

docker run
docker ps
docker exec
docker logs
docker stop
docker rm
docker images
docker pull
docker build

I especially want more practice combining commands with pipes (|), redirection (>, >>), command options, and conditions.

Before moving too far ahead, I want to become more comfortable with everyday Linux commands and shell usage.

I need more practice with:

File and directory navigation
Creating, copying, moving and deleting files
File permissions and ownership
Processes and process management
Searching files and text
Pipes and redirection
Environment variables
Shell scripting
Background and foreground processes
Understanding command options and flags

### Confusing but now understood

- `python3` is the Linux/Ubuntu command, while Windows commonly uses `python`.
- A Linux virtual environment normally contains `bin/`, while a Windows virtual environment contains `Scripts/`.
- `xargs` takes input and turns it into arguments for another command.
- `bash -c '...'` tells Bash to execute the command inside the quotes.
- `docker exec` does not create a new container; it runs a command inside an existing running container.
- `tail -f` does not simply print a file; it continues watching the file for new content.
- `--rm` makes Docker remove the container after it stops, which is why files created only inside that container, such as `app.log`, disappear.