# Live Debugging Notes

## 1. Container exits instantly on startup

Check container logs:
docker compose logs api

Check the resolved Compose configuration:
docker compose config

Check container status:
docker compose ps

## 2. API cannot reach the database
Check whether the database container is running and healthy:
docker compose ps

Check database logs:
docker compose logs db

Check DNS resolution from the API container:
docker compose exec api getent hosts db

Test PostgreSQL connectivity from the API container:
docker compose exec api pg_isready -h db -U postgres -d scanflow

Check the database health directly:
docker compose exec db pg_isready -U postgres -d scanflow

## 3. Code changed but behaviour did not
Check the running container:
docker compose ps

Check the image currently used by the API:
docker compose images api

Rebuild the API image:
docker compose up -d --build api

Check the API logs after rebuilding:
docker compose logs api --tail=50

## 4. Logs are empty
Check the container logs:
docker compose logs api

Check the last lines:
docker compose logs api --tail=100

Check whether the process is writing to stdout/stderr:
docker compose exec api sh -c 'ls -l /proc/1/fd/1 /proc/1/fd/2'

Check the configured logging level:
docker compose exec api env | grep -i log

## 5. 504 Gateway Time-out — API unavailable

Stopped the API:

docker compose stop api

Tested through Nginx:

curl.exe -i http://localhost:8000/v1/scans

Observed:

HTTP/1.1 504 Gateway Time-out

Checked Nginx logs:

docker compose logs nginx --tail=50

Nginx reported:

upstream timed out (110: Operation timed out) while connecting to upstream

The upstream was:

http://172.19.0.3:80/v1/scans

The request took approximately 5 seconds:

request_time=5.002
upstream_response_time=5.005
upstream_status=504

Checked service state:

docker compose ps

Restored API:

docker compose start api

Verified recovery:

curl.exe http://localhost:8000/healthz