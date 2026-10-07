# Lab 2 - Nginx Container Lifecycle

## Objective

Learn how to run a long-running container and manage its lifecycle.

Topics covered:

- detached containers
- container names
- port publishing
- container logs
- interactive shell access
- stopping and starting containers
- removing containers
- container writable filesystem

## Run Nginx

```bash
docker run -d --name web-lab -p 8080:80 nginx
```

Options:

- `docker run` creates and starts a container.
- `-d` runs the container in detached mode.
- `--name web-lab` assigns a custom name.
- `-p 8080:80` maps host port `8080` to container port `80`.
- `nginx` is the image used to create the container.

## Verify the Container

```bash
docker ps
```

Nginx remains running because its main process is a web server.

## Test the Web Server

```bash
curl http://localhost:8080
```

Nginx listens on port `80` inside the container.

Docker publishes that port through port `8080` on the host.

The mapping:

```text
8080:80
```

means:

```text
host-port:container-port
```

## Container Logs

Display logs:

```bash
docker logs web-lab
```

Follow logs in real time:

```bash
docker logs -f web-lab
```

Exit log-follow mode with:

```text
Ctrl+C
```

This does not stop the container.

## Inspect the Container

```bash
docker inspect web-lab
```

This displays information such as:

- container state
- image
- networks
- IP addresses
- port mappings
- mounts
- environment variables

## Open a Shell Inside the Container

```bash
docker exec -it web-lab bash
```

Options:

- `exec` runs a command inside an existing container.
- `-i` keeps standard input open.
- `-t` creates a terminal.
- `bash` starts a Bash shell.

Inside the container:

```bash
pwd
ls
ls /usr/share/nginx/html
```

Read the default Nginx page:

```bash
cat /usr/share/nginx/html/index.html
```

Exit the container shell:

```bash
exit
```

The container continues running.

## Modify the Container Filesystem

Enter the container:

```bash
docker exec -it web-lab bash
```

Create a file:

```bash
echo "Hola desde mi contenedor" > /usr/share/nginx/html/test.txt
```

Exit:

```bash
exit
```

Test the file:

```bash
curl http://localhost:8080/test.txt
```

The response should be:

```text
Hola desde mi contenedor
```

The file exists in the container's writable filesystem.

## Stop the Container

```bash
docker stop web-lab
```

Running containers:

```bash
docker ps
```

All containers:

```bash
docker ps -a
```

The container still exists but is stopped.

## Start the Container Again

```bash
docker start web-lab
```

Verify:

```bash
docker ps
```

The previously created `test.txt` file still exists because the same container was restarted.

```bash
curl http://localhost:8080/test.txt
```

## Remove the Container

Stop it:

```bash
docker stop web-lab
```

Remove it:

```bash
docker rm web-lab
```

Verify:

```bash
docker ps -a
```

The container no longer exists.

The Nginx image still exists:

```bash
docker images
```

## Create a New Container from the Same Image

```bash
docker run -d --name web-lab-2 -p 8080:80 nginx
```

Try:

```bash
curl http://localhost:8080/test.txt
```

The file created in the previous container is not available.

This demonstrates that changes made to a container's writable filesystem belong to that specific container.

## Cleanup

```bash
docker stop web-lab-2
docker rm web-lab-2
```

Optionally remove the image:

```bash
docker rmi nginx
```

## Key Commands

```bash
docker run -d --name web-lab -p 8080:80 nginx
docker ps
docker ps -a
docker logs web-lab
docker logs -f web-lab
docker inspect web-lab
docker exec -it web-lab bash
docker stop web-lab
docker start web-lab
docker rm web-lab
```

## Key Takeaways

- `-d` runs a container in the background.
- `-p` publishes a container port through the host.
- `docker exec` runs additional commands inside an existing container.
- `docker stop` does not delete a container.
- `docker start` restarts an existing stopped container.
- `docker rm` deletes the container.
- Files written directly inside a container are lost when that container is deleted.
