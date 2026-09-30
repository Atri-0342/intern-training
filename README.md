# ScanFlow

ScanFlow is a FastAPI-based radiology scan intake and analysis API backed by PostgreSQL.

## Prerequisites

Before running ScanFlow, install:

- [Docker Desktop](https://www.docker.com/products/docker-desktop/)
- [Git](https://git-scm.com/)

Docker Desktop must be running before starting the application.

## Environment Variables

Create the following two files in the project root. Neither is committed to Git.

### `.env`

```env
DB_NAME=scanflow
DB_USER=postgres
DB_HOST=db
DB_PORT=5432
TEST_DB_NAME=scanflow_test

POSTGRES_USER=postgres
POSTGRES_DB=scanflow

JWT_ALGORITHM=HS256
JWT_EXPIRE_MINUTES=30
```

### `.env.secret`

```env
DB_PASSWORD=YOUR_DATABASE_PASSWORD
POSTGRES_PASSWORD=YOUR_DATABASE_PASSWORD
JWT_SECRET=YOUR_JWT_SECRET
```

Replace the placeholder values with your own local secrets.

> **Do not commit `.env` or `.env.secret` to Git.**

## Start the Application

From the project root, run:

```bash
docker compose up --build
```

This starts the ScanFlow API and PostgreSQL database. Database migrations are applied automatically when the API container starts.

The API is available at:

```text
http://localhost:8000
```

## API Documentation

Interactive Swagger documentation:

```text
http://localhost:8000/docs
```

Raw OpenAPI specification:

```text
http://localhost:8000/openapi.json
```

## Health Check

```text
http://localhost:8000/healthz
```

A healthy application returns:

```json
{
  "status": "ok",
  "database": "connected"
}
```

## Run Tests

```bash
py -m pytest
```

With coverage:

```bash
py -m pytest --cov=app
```

## Stop the Application

To stop the containers **without** removing the PostgreSQL volume:

```bash
docker compose down
```

The PostgreSQL volume is intentionally preserved, so database data is not deleted.

> **Warning:** `docker compose down -v` removes the PostgreSQL volume and permanently deletes the database stored in it.