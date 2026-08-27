# Day 0 — Environment Setup

## Objective

Set up the complete development environment required for the eight-week backend engineering training and verify that the main tools work together.

## What I learned

## 1. Python 
I  learned that a Python virtual environment (`.venv`) keeps a project's Python packages isolated from the system Python installation.

The virtual environment itself should not be committed to Git because it is machine-specific and can be recreated when needed.

## 2. WSL

WSL stands for **Windows Subsystem for Linux**.
It allows Linux environments to run on Windows without needing a traditional separate virtual machine.
Docker Desktop on my Windows setup uses WSL 2 as part of its Linux based container environment.
I installed WSL and Ubuntu because Docker Desktop initially could not start without WSL.

## 3. Docker

Docker allows applications and services to run inside containers.

A container packages an application together with the environment it needs, which makes the application easier to run consistently across different machines.

I verified my Docker installation using:

```docker run --rm hello-world```

## 4. Docker Desktop

Docker Desktop provides the tools needed to work with Docker on Windows.
It provides the Docker CLI, Docker Engine integration, Docker Compose support, and a graphical interface for managing Docker resources.
On Windows, Docker Desktop can use **WSL 2** as its backend.

## 5. Git

Git is a **version-control system**. It tracks changes to files and allows me to create checkpoints of my work.


### `git add`

`git add` selects changes that should be included in the next commit.

Example:

```git add README.md```

### `git commit`

`git commit` creates a checkpoint in the local Git history.

Example:

```git commit -m "chore: initialize intern training repository"```

### `git push`

`git push` sends local commits to the remote GitHub repository.

Example:

```git push```

## 6. GitHub

GitHub is a platform for hosting Git repositories remotely.
Git itself works locally on my computer, while GitHub provides the remote repository where code can be stored, shared, reviewed, and collaborated on.

I created the training repository:

```intern-training```

The repository contains the training material and the ScanFlow project.

## 7. Git Repository

A Git repository contains the project's Git history and configuration.

The `.git` directory is what makes a directory a Git repository.

## 11. SSH

SSH provides secure authentication between my computer and GitHub.

I generated an **Ed25519 SSH key pair**:

```text
id_ed25519
id_ed25519.pub
```

The private key stays on my computer.

The public key is uploaded to GitHub.

I verified the connection with:

```ssh -T git@github.com```

GitHub successfully authenticated me as:

```Atri-0342```

This means my computer can authenticate with GitHub using SSH.

## 12. SSH Passphrase

When generating my SSH key, I created a passphrase.

The passphrase protects the private key if someone gains access to the key file. The private key should never be uploaded to GitHub or shared with anyone.

## 13. GitHub SSH Authentication

SSH allows my computer to securely authenticate with GitHub. I keep the private key on my computer and add the public key to GitHub. When I connect to GitHub, GitHub checks whether the keys match. If they match, GitHub authenticates my computer.

I verified this using:

```ssh -T git@github.com```

The successful response confirmed that GitHub recognizes my SSH key.

# Problems I Encountered

## 1. Docker

Docker initially failed because the Docker Linux engine could not be reached.

The reason was that WSL was not installed. I installed WSL and Ubuntu, configured the environment, and then verified
Docker successfully using:

```docker run hello-world```

The command completed successfully and displayed:

```Hello from Docker!```

This confirmed that the Docker installation was working.