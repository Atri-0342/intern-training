# Day 17 — curl HTTP Exercise

## 1. Check curl

```powershell
curl.exe --version
```

## 2. GET Request

```powershell
curl.exe -v https://httpbin.org/get
```

Look for:

```text
> GET /get HTTP/1.1
> Host: httpbin.org
> User-Agent: curl/...
> Accept: */*

< HTTP/1.1 200 OK
< Content-Type: application/json
```

Understand:

* `>` = request sent by curl
* `<` = response received from server
* `GET` = HTTP method
* `/get` = request path
* `200 OK` = response status
* JSON after the headers = response body

## 3. POST Request with JSON

```powershell
curl.exe -v -X POST https://httpbin.org/post -H "Content-Type: application/json" -d "{\"name\":\"ScanFlow\",\"role\":\"backend\"}"
```

The JSON being sent is:

```json
{
  "name": "ScanFlow",
  "role": "backend"
}
```

Look for:

```text
> POST /post HTTP/1.1
> Content-Type: application/json
> Content-Length: ...

< HTTP/1.1 200 OK
```

Understand:

* HTTP method
* Request path
* Request headers
* `Content-Type`
* Request body
* Response status
* Response headers
* Response body

## 4. Malformed Header

```powershell
curl.exe -v https://httpbin.org/get -H "This-Is-Not-A-Valid-Header"
```

Check whether:

* curl rejects the request itself
* or curl sends the request and the server responds

The important question is:

```text
Did the request actually reach the server?
```

## 5. 404 Request

```powershell
curl.exe -v https://httpbin.org/status/404
```

Look for:

```text
< HTTP/1.1 404 NOT FOUND
```

Understand:

```text
Client
  |
  | GET request
  v
Server
  |
  | 404 response
  v
Client
```

The server received the request but could not find the requested resource.

## 6. 422 Request

For this one, use your local FastAPI application.

Example endpoint:

```python
from fastapi import FastAPI
from pydantic import BaseModel

app = FastAPI()

class User(BaseModel):
    name: str
    age: int

@app.post("/users")
def create_user(user: User):
    return user
```

Start FastAPI:

```powershell
uvicorn main:app --reload
```

Send a valid request:

```powershell
curl.exe -v -X POST http://127.0.0.1:8000/users -H "Content-Type: application/json" -d "{\"name\":\"Jrrity\",\"age\":24}"
```

Now deliberately send invalid data:

```powershell
curl.exe -v -X POST http://127.0.0.1:8000/users -H "Content-Type: application/json" -d "{\"name\":\"Jrrity\",\"age\":\"not-a-number\"}"
```

Look for:

```text
< HTTP/1.1 422 Unprocessable Entity
```

Then identify:

* Which field failed?
* Why did validation fail?
* What did FastAPI return in the response body?

## 7. Save the Transcripts

GET:

```powershell
curl.exe -v https://httpbin.org/get 2>&1 | Tee-Object -FilePath notes/curl-get.txt
```

POST:

```powershell
curl.exe -v -X POST https://httpbin.org/post -H "Content-Type: application/json" -d "{\"name\":\"ScanFlow\",\"role\":\"backend\"}" 2>&1 | Tee-Object -FilePath notes/curl-post.txt
```

Malformed header:

```powershell
curl.exe -v https://httpbin.org/get -H "This-Is-Not-A-Valid-Header" 2>&1 | Tee-Object -FilePath notes/curl-malformed-header.txt
```

404:

```powershell
curl.exe -v https://httpbin.org/status/404 2>&1 | Tee-Object -FilePath notes/curl-404.txt
```

422:

```powershell
curl.exe -v -X POST http://127.0.0.1:8000/users -H "Content-Type: application/json" -d "{\"name\":\"Jrrity\",\"age\":\"not-a-number\"}" 2>&1 | Tee-Object -FilePath notes/curl-422.txt
```
