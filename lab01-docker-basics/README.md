# Lab 1 - Docker Basics

## Objective

Learn the basic Docker architecture and verify that Docker can successfully create and run containers.

Topics covered:

- Docker CLI
- Docker daemon
- Docker images
- Docker containers
- Docker Hub
- Docker socket
- Linux permissions
- Docker group

## Verify Docker Installation

```bash
docker --version
```

This verifies that the Docker CLI is installed.

To verify communication between the Docker client and Docker Engine:

```bash
docker version
```

A working installation should show both:

- Client
- Server

Additional Docker Engine information can be displayed with:

```bash
docker info
```

## Run the First Container

```bash
docker run hello-world
```

Docker performs the following actions:

1. Checks whether the `hello-world` image exists locally.
2. Downloads the image from Docker Hub if it is not available locally.
3. Creates a container from the image.
4. Starts the container.
5. Executes the main process contained in the image.
6. The process prints the Docker welcome message.
7. The container exits because its main process has finished.

## Images

List locally available images:

```bash
docker images
```

Equivalent command:

```bash
docker image ls
```

An image is the template Docker uses to create containers.

Example:

```text
hello-world
```

## Containers

Show running containers:

```bash
docker ps
```

Show all containers, including stopped containers:

```bash
docker ps -a
```

The `hello-world` container appears as stopped because its process exits immediately after printing the message.

## Docker CLI and Docker Daemon

The Docker CLI is the command-line interface used to send requests to Docker Engine.

Example:

```bash
docker run hello-world
```

The Docker daemon (`dockerd`) performs the actual work, including:

- downloading images
- creating containers
- starting and stopping containers
- managing networks
- managing volumes

On Linux, the Docker CLI normally communicates with the daemon using:

```text
/var/run/docker.sock
```

## Docker Socket Permission Error

The following error may occur:

```text
permission denied while trying to connect to the Docker API at unix:///var/run/docker.sock
```

This means the current Linux user does not have permission to access the Docker socket.

Docker commands may work with `sudo`:

```bash
sudo docker run hello-world
```

However, the preferred setup for these labs is to allow the user to run Docker without `sudo`.

## Docker Group

Create the Docker group if required:

```bash
sudo groupadd docker
```

If the group already exists, no action is required.

Add the current user to the Docker group:

```bash
sudo usermod -aG docker $USER
```

Options:

- `usermod` modifies a Linux user.
- `-a` appends the new group without removing existing groups.
- `-G` specifies supplementary groups.
- `docker` is the target group.
- `$USER` contains the current username.

Check the current username:

```bash
echo $USER
```

Check group membership:

```bash
groups
```

or:

```bash
id
```

After modifying group membership, log out and log back in so the new group membership is loaded.

Exit the Linux session:

```bash
exit
```

After reconnecting, verify that `docker` appears in the user's groups:

```bash
groups
```

Then test Docker without `sudo`:

```bash
docker run hello-world
```

## Inspect an Image

```bash
docker image inspect hello-world
```

This displays image metadata such as:

- image ID
- architecture
- operating system
- layers
- environment configuration
- entrypoint
- command

## Key Commands

```bash
docker --version
docker version
docker info
docker run hello-world
docker images
docker ps
docker ps -a
docker image inspect hello-world
groups
id
sudo usermod -aG docker $USER
```

## Key Takeaways

- Docker images are templates.
- Docker containers are instances created from images.
- The Docker CLI sends requests to Docker Engine.
- Docker Engine performs the actual container operations.
- Linux users need permission to access the Docker socket.
- Adding the user to the `docker` group allows Docker commands to run without `sudo`.
