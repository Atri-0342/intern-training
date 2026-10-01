# Docker Notes

## Image

An image is the packaged template used to create a container. It contains the application, its dependencies, libraries, and the filesystem needed to run the application. An image itself is not the running application.

For example, `postgres:17` is an image that can be used to create PostgreSQL containers.

## Container

A container is a running or stopped instance created from an image. A container has its own writable filesystem layer and its own process environment. When the container is deleted, data stored only inside that container can be lost.

For example, when we ran:

    docker run postgres:17

Docker created a PostgreSQL container from the `postgres:17` image.

## Layer

An image is built from multiple layers. Each layer represents a filesystem change made while building the image. Layers can be reused between images, which helps Docker avoid downloading or rebuilding the same data repeatedly. The container gets a writable layer on top of the image's read only layers.

## Volume

A volume is persistent storage managed by Docker. A volume exists separately from the container that uses it. This means a container can be deleted and recreated while the data in the volume remains.

We tested this with PostgreSQL. With a named volume: postgres-data

the `volume_test` database survived after the PostgreSQL container was deleted and recreated.

Without a volume, the `volume_test` database disappeared when the container was deleted and a new PostgreSQL container was created.
