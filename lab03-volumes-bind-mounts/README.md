# Lab 3 - Docker Volumes and Bind Mounts

## Objective

Learn how Docker stores persistent data outside the writable filesystem of a container.

Topics covered:

- Docker volumes
- persistent storage
- volume mounts
- bind mounts
- host directories
- container data persistence

## List Docker Volumes

```bash
docker volume ls
```

## Create a Volume

```bash
docker volume create web-data
```

Verify:

```bash
docker volume ls
```

The volume is managed by Docker and exists independently of any individual container.

## Run Nginx with a Docker Volume

```bash
docker run -d \
  --name volume-lab \
  -p 8080:80 \
  -v web-data:/usr/share/nginx/html \
  nginx
```

The `-v` option mounts storage.

```text
web-data:/usr/share/nginx/html
```

The left side is the Docker volume:

```text
web-data
```

The right side is the directory inside the container:

```text
/usr/share/nginx/html
```

## Write Data to the Volume

Enter the container:

```bash
docker exec -it volume-lab bash
```

Create an HTML file:

```bash
echo "Este archivo vive en un Docker Volume" > /usr/share/nginx/html/index.html
```

Exit:

```bash
exit
```

Test:

```bash
curl http://localhost:8080
```

Expected response:

```text
Este archivo vive en un Docker Volume
```

## Delete the Container

Stop the container:

```bash
docker stop volume-lab
```

Remove it:

```bash
docker rm volume-lab
```

Verify that the volume still exists:

```bash
docker volume ls
```

The `web-data` volume remains because its lifecycle is separate from the container.

## Reuse the Volume

Create a new container using the same volume:

```bash
docker run -d \
  --name volume-lab-2 \
  -p 8080:80 \
  -v web-data:/usr/share/nginx/html \
  nginx
```

Test:

```bash
curl http://localhost:8080
```

The previous content should still be available.

This demonstrates persistent storage.

## Inspect the Volume

```bash
docker volume inspect web-data
```

Important information includes:

- volume name
- driver
- mountpoint
- creation information

Docker normally stores local volume data under its own storage directories.

Applications should normally access the volume through Docker rather than modifying Docker's internal storage manually.

## Bind Mounts

A bind mount maps a specific host directory directly into a container.

First remove the previous container:

```bash
docker stop volume-lab-2
docker rm volume-lab-2
```

Create a host directory:

```bash
mkdir -p ~/docker-labs/web-content
```

Create content:

```bash
echo "Hola desde un Bind Mount" > ~/docker-labs/web-content/index.html
```

Verify:

```bash
cat ~/docker-labs/web-content/index.html
```

## Run Nginx with a Bind Mount

```bash
docker run -d \
  --name bind-lab \
  -p 8080:80 \
  -v ~/docker-labs/web-content:/usr/share/nginx/html \
  nginx
```

Test:

```bash
curl http://localhost:8080
```

Expected response:

```text
Hola desde un Bind Mount
```

## Modify the File from the Host

```bash
echo "Cambie el archivo desde Linux" > ~/docker-labs/web-content/index.html
```

Test again:

```bash
curl http://localhost:8080
```

The updated content appears immediately because the container and host are accessing the same mounted directory.

## Volume vs Bind Mount

Docker Volume:

```bash
-v web-data:/data
```

Docker manages the physical storage location.

Useful for:

- application data
- databases
- persistent container data

Bind Mount:

```bash
-v ~/project:/app
```

A specific host directory is mounted directly into the container.

Useful for:

- source code
- development
- configuration files
- local files that need to be edited outside the container

## Cleanup

Stop and remove the bind-mount container:

```bash
docker stop bind-lab
docker rm bind-lab
```

Remove the Docker volume:

```bash
docker volume rm web-data
```

Verify:

```bash
docker volume ls
```

The bind-mounted host directory still exists:

```bash
ls ~/docker-labs/web-content
```

Remove it if no longer needed:

```bash
rm -rf ~/docker-labs/web-content
```

## Key Commands

```bash
docker volume ls
docker volume create web-data
docker volume inspect web-data
docker volume rm web-data
docker run -v web-data:/data ...
docker run -v ~/host-directory:/container-directory ...
```

## Key Takeaways

- Data stored only in a container's writable filesystem disappears when the container is deleted.
- Docker volumes exist independently of containers.
- Volumes are managed by Docker.
- Bind mounts map a specific host directory into a container.
- Persistent application data should normally live outside the container's writable layer.
