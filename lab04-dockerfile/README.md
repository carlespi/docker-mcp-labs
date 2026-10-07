# Lab 4 - Dockerfile and Custom Images

## Objective

Learn how to build a custom Docker image using a Dockerfile.

Topics covered:

- Dockerfile
- build context
- `FROM`
- `COPY`
- `WORKDIR`
- `RUN`
- `CMD`
- image tags
- image rebuilds
- Docker build cache
- image layers

## Lab Files

```text
lab04-dockerfile/
├── Dockerfile
├── index.html
└── README.md
```

## Initial Dockerfile

```dockerfile
FROM nginx:latest

COPY index.html /usr/share/nginx/html/index.html
```

`FROM` specifies the base image.

```dockerfile
FROM nginx:latest
```

The custom image starts with the existing Nginx image.

`COPY` copies a file from the build context into the image.

```dockerfile
COPY index.html /usr/share/nginx/html/index.html
```

## Build the Image

```bash
docker build -t my-nginx-lab .
```

Options:

- `docker build` builds an image from a Dockerfile.
- `-t my-nginx-lab` assigns the image name/tag.
- `.` sets the current directory as the build context.

By default, Docker searches the build context for a file named:

```text
Dockerfile
```

## Build Context

The build context is the directory Docker can access while building the image.

In this lab:

```text
lab04-dockerfile/
├── Dockerfile
└── index.html
```

The `.` in:

```bash
docker build -t my-nginx-lab .
```

means that the current directory is the build context.

## List Images

```bash
docker images
```

The custom image should appear as:

```text
my-nginx-lab
```

## Run the Custom Image

```bash
docker run -d \
  --name my-web \
  -p 8080:80 \
  my-nginx-lab
```

Test:

```bash
curl http://localhost:8080
```

The page contained in `index.html` should be returned.

## Verify the File Inside the Container

```bash
docker exec -it my-web bash
```

Inside the container:

```bash
cat /usr/share/nginx/html/index.html
```

Exit:

```bash
exit
```

## Modify the Local File

Change the local file:

```bash
echo "<h1>Version 2</h1>" > index.html
```

The existing container does not change automatically.

```bash
curl http://localhost:8080
```

The old content remains because the container was created from the previous version of the image.

## Rebuild the Image

```bash
docker build -t my-nginx-lab .
```

The image is rebuilt using the updated source files.

The existing container still uses the image version from which it was originally created.

Stop and remove the old container:

```bash
docker stop my-web
docker rm my-web
```

Create a new one:

```bash
docker run -d \
  --name my-web \
  -p 8080:80 \
  my-nginx-lab
```

Verify:

```bash
curl http://localhost:8080
```

The new content should now appear.

## Image Tags

Build version 1:

```bash
docker build -t my-nginx-lab:v1 .
```

Build another version:

```bash
docker build -t my-nginx-lab:v2 .
```

List images:

```bash
docker images
```

Tags allow multiple versions of an image to be identified separately.

## WORKDIR

Update the Dockerfile:

```dockerfile
FROM nginx:latest

WORKDIR /usr/share/nginx/html

COPY index.html .
```

`WORKDIR` changes the working directory used by subsequent Dockerfile instructions.

After:

```dockerfile
WORKDIR /usr/share/nginx/html
```

this instruction:

```dockerfile
COPY index.html .
```

copies the file to:

```text
/usr/share/nginx/html/index.html
```

## RUN

Dockerfile:

```dockerfile
FROM nginx:latest

WORKDIR /usr/share/nginx/html

COPY index.html .

RUN echo "Built inside Docker image" > build-info.txt
```

`RUN` executes a command while the image is being built.

Build:

```bash
docker build -t my-nginx-lab .
```

The command:

```dockerfile
RUN echo "Built inside Docker image" > build-info.txt
```

creates:

```text
/usr/share/nginx/html/build-info.txt
```

inside the image.

After recreating the container:

```bash
curl http://localhost:8080/build-info.txt
```

Expected response:

```text
Built inside Docker image
```

## Build Time vs Runtime

Build time occurs during:

```bash
docker build
```

Docker processes instructions such as:

```text
FROM
WORKDIR
COPY
RUN
```

Runtime begins when:

```bash
docker run
```

creates and starts a container from the completed image.

## CMD

`CMD` specifies the default command executed when a container starts.

Example:

```dockerfile
CMD ["python", "app.py"]
```

This lab does not need its own `CMD` because the Nginx base image already defines the command required to start Nginx.

## Image Layers and Cache

Docker images contain layers.

When an image is rebuilt, Docker can reuse unchanged layers.

A repeated build may show:

```text
CACHED
```

If `index.html` changes, Docker can reuse earlier unchanged layers but rebuild the layer affected by the `COPY` instruction.

## Inspect the Image

```bash
docker image inspect my-nginx-lab
```

This displays image metadata.

## Image History

```bash
docker history my-nginx-lab
```

This shows the image layers and build history.

## Cleanup

```bash
docker stop my-web
docker rm my-web
```

Remove the image if desired:

```bash
docker rmi my-nginx-lab
```

Remove tagged versions if necessary:

```bash
docker rmi my-nginx-lab:v1
docker rmi my-nginx-lab:v2
```

## Key Commands

```bash
docker build -t my-nginx-lab .
docker images
docker run -d --name my-web -p 8080:80 my-nginx-lab
docker exec -it my-web bash
docker image inspect my-nginx-lab
docker history my-nginx-lab
```

## Key Takeaways

- A Dockerfile contains instructions used to build an image.
- Docker automatically reads `Dockerfile` unless another file is specified with `-f`.
- `FROM` defines the base image.
- `COPY` adds files to the image.
- `WORKDIR` changes the working directory for following instructions.
- `RUN` executes commands during image build.
- `CMD` defines the default runtime command.
- `docker build` creates an image.
- `docker run` creates a container from an image.
- Rebuilding an image does not automatically update existing containers.
