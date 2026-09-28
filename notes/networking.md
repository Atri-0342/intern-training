curl -v https://example.com

* Host example.com:443 was resolved.
* IPv6: 2606:4700:8d95:72db:f264:aa5:ef6b:ff98
* IPv4: 104.20.23.154, 172.66.147.243
*   Trying [2606:4700:8d95:72db:f264:aa5:ef6b:ff98]:443...
* Immediate connect fail for 2606:4700:8d95:72db:f264:aa5:ef6b:ff98: Network is unreachable
*   Trying 104.20.23.154:443...
* ALPN: curl offers h2,http/1.1
* TLSv1.3 (OUT), TLS handshake, Client hello (1):
* SSL Trust Anchors:
*   CAfile: /etc/ssl/certs/ca-certificates.crt
*   CApath: /etc/ssl/certs
* TLSv1.3 (IN), TLS handshake, Server hello (2):
* TLSv1.3 (IN), TLS change cipher, Change cipher spec (1):
* TLSv1.3 (IN), TLS handshake, Encrypted Extensions (8):
* TLSv1.3 (IN), TLS handshake, Certificate (11):
* TLSv1.3 (IN), TLS handshake, CERT verify (15):
* TLSv1.3 (IN), TLS handshake, Finished (20):
* TLSv1.3 (OUT), TLS change cipher, Change cipher spec (1):
* TLSv1.3 (OUT), TLS handshake, Finished (20):
* SSL connection using TLSv1.3 / TLS_AES_256_GCM_SHA384 / X25519MLKEM768 / id-ecPublicKey
* ALPN: server accepted h2
* Server certificate:
*   subject: CN=example.com
*   start date: Jul 29 22:10:08 2026 GMT
*   expire date: Oct 27 22:17:21 2026 GMT
*   issuer: C=US; O=SSL Corporation; CN=Cloudflare TLS Issuing ECC CA 3
*   Certificate level 0: Public key type EC/prime256v1 (256/128 Bits/secBits), signed using ecdsa-with-SHA256
*   Certificate level 1: Public key type EC/prime256v1 (256/128 Bits/secBits), signed using ecdsa-with-SHA384
*   Certificate level 2: Public key type EC/secp384r1 (384/192 Bits/secBits), signed using ecdsa-with-SHA384
*   Certificate level 3: Public key type EC/secp384r1 (384/192 Bits/secBits), signed using ecdsa-with-SHA384
*   subjectAltName: "example.com" matches cert's "example.com"
* SSL certificate verified via OpenSSL.
* Established connection to example.com (104.20.23.154 port 443) from 172.26.244.161 port 50472
* using HTTP/2
* [HTTP/2] [1] OPENED stream for https://example.com/
* [HTTP/2] [1] [:method: GET]
* [HTTP/2] [1] [:scheme: https]
* [HTTP/2] [1] [:authority: example.com]
* [HTTP/2] [1] [:path: /]
* [HTTP/2] [1] [user-agent: curl/8.18.0]
* [HTTP/2] [1] [accept: */*]
> GET / HTTP/2
> Host: example.com
> User-Agent: curl/8.18.0
> Accept: */*
>
* Request completely sent off
* TLSv1.3 (IN), TLS handshake, Newsession Ticket (4):
* TLSv1.3 (IN), TLS handshake, Newsession Ticket (4):
< HTTP/2 200
< date: Sat, 26 Sep 2026 08:26:28 GMT
< content-type: text/html
< server: cloudflare
< last-modified: Tue, 22 Sep 2026 20:16:57 GMT
< allow: GET, HEAD
< accept-ranges: bytes
< age: 4293
< cf-cache-status: HIT
< cf-ray: a410e24808dff4d3-IXC
<
<!doctype html><html lang="en"><head><title>Example Domain</title><link rel="icon" href="data:,"><meta name="viewport" content="width=device-width, initial-scale=1"><style>body{background:#eee;width:60vw;margin:15vh auto;font-family:system-ui,sans-serif}h1{font-size:1.5em}div{opacity:0.8}a:link,a:visited{color:#348}</style></head><body><div><h1>Example Domain</h1><p>This domain is for use in documentation examples without needing permission. Avoid use in operations.</p><p><a href="https://iana.org/domains/example">Learn more</a></p></div></body></html>
* Connection #0 to host example.com:443 left intact

1. DNS resolution
* Host example.com:443 was resolved.

Curl successfully resolved example.com to IP addresses.

The :443 indicates that HTTPS is being requested on TCP port 443.

* IPv6: 2606:4700:8d95:72db:f264:aa5:ef6b:ff98

DNS returned an IPv6 address for example.com.

* IPv4: 104.20.23.154, 172.66.147.243

DNS also returned two IPv4 addresses.

So the DNS stage succeeded.

2. IPv6 connection attempt
*   Trying [2606:4700:8d95:72db:f264:aa5:ef6b:ff98]:443...

Curl first attempted to connect to the IPv6 address on port 443.

* Immediate connect fail for 2606:4700:8d95:72db:f264:aa5:ef6b:ff98: Network is unreachable

The IPv6 connection failed because this WSL environment does not currently have a usable route to that IPv6 network.

This does not mean that example.com does not support IPv6. It means that my local environment could not reach it over IPv6.

3. IPv4 fallback
*   Trying 104.20.23.154:443...

Curl then tried the first IPv4 address returned by DNS. This connection succeeded, allowing curl to continue with HTTPS.

4. ALPN
* ALPN: curl offers h2,http/1.1

ALPN means Application-Layer Protocol Negotiation.

Curl tells the server that it supports:

h2 = HTTP/2
http/1.1 = HTTP/1.1

The server can select which HTTP protocol to use.

5. TLS handshake starts
* TLSv1.3 (OUT), TLS handshake, Client hello (1):

OUT means the message is being sent from the client to the server.

The TLS ClientHello starts the TLS handshake.

The client provides information such as supported TLS features and cryptographic options.

6. Certificate trust configuration
* SSL Trust Anchors:
*   CAfile: /etc/ssl/certs/ca-certificates.crt
*   CApath: /etc/ssl/certs

Curl/OpenSSL shows where it gets trusted Certificate Authorities from.

The CA file contains trusted CA certificates used to verify the server certificate.

The CA path is another location containing trusted certificates.

This is part of the certificate trust process.

7. Server responds to the TLS handshake
* TLSv1.3 (IN), TLS handshake, Server hello (2):

IN means the message was received from the server.

The server sends its ServerHello and selects the TLS parameters for the connection.

* TLSv1.3 (IN), TLS change cipher, Change cipher spec (1):

The TLS connection is progressing toward encrypted communication.

* TLSv1.3 (IN), TLS handshake, Encrypted Extensions (8):

The server sends TLS extensions that are encrypted in TLS 1.3.

* TLSv1.3 (IN), TLS handshake, Certificate (11):

The server sends its certificate chain.

The client will use this information to verify the server's identity.

* TLSv1.3 (IN), TLS handshake, CERT verify (15):

The server proves that it possesses the private key corresponding to its certificate.

This helps authenticate the server.

* TLSv1.3 (IN), TLS handshake, Finished (20):

The server indicates that its part of the TLS handshake is complete.

* TLSv1.3 (OUT), TLS change cipher, Change cipher spec (1):

The client progresses to encrypted communication.

* TLSv1.3 (OUT), TLS handshake, Finished (20):

The client completes its side of the TLS handshake.

8. TLS connection established
* SSL connection using TLSv1.3 / TLS_AES_256_GCM_SHA384 / X25519MLKEM768 / id-ecPublicKey

The HTTPS connection is using TLS 1.3.

The negotiated cryptographic information includes:

TLS 1.3
AES-256-GCM for symmetric encryption
X25519MLKEM768 for key exchange
an EC public key

The important observation is that the HTTP connection is now protected by TLS.

9. HTTP protocol negotiation
* ALPN: server accepted h2

The server selected h2, meaning HTTP/2.

Curl therefore uses HTTP/2 instead of HTTP/1.1.

10. Server certificate
* Server certificate:

Curl begins displaying information about the certificate presented by the server.

*   subject: CN=example.com

The certificate's subject identifies example.com.

*   start date: Jul 29 22:10:08 2026 GMT

The certificate became valid at this time.

*   expire date: Oct 27 22:17:21 2026 GMT

The certificate expires at this time.

*   issuer: C=US; O=SSL Corporation; CN=Cloudflare TLS Issuing ECC CA 3

This identifies the Certificate Authority that issued the certificate.

The issuer is different from the subject:

Subject:
example.com

Issuer:
Cloudflare TLS Issuing ECC CA 3

11. Certificate chain
*   Certificate level 0: Public key type EC/prime256v1 (256/128 Bits/secBits), signed using ecdsa-with-SHA256

Certificate level 0 is the server certificate.

It uses an elliptic-curve public key and is signed using ECDSA with SHA-256.

*   Certificate level 1: Public key type EC/prime256v1 (256/128 Bits/secBits), signed using ecdsa-with-SHA384

This is the next certificate in the presented chain.

*   Certificate level 2: Public key type EC/secp384r1 (384/192 Bits/secBits), signed using ecdsa-with-SHA384

Another certificate in the chain.

*   Certificate level 3: Public key type EC/secp384r1 (384/192 Bits/secBits), signed using ecdsa-with-SHA384

Another certificate level in the chain.

The output therefore shows a multi-level certificate chain.

12. Hostname verification
*   subjectAltName: "example.com" matches cert's "example.com"

The certificate's Subject Alternative Name contains example.com.

This matches the hostname curl requested.

This is important because a certificate must be valid for the hostname being accessed.

13. Certificate verification succeeded
* SSL certificate verified via OpenSSL.

OpenSSL successfully verified the server certificate against the trusted CA information available on the system.

Therefore curl trusts the certificate.

14. TCP connection established
* Established connection to example.com (104.20.23.154 port 443) from 172.26.244.161 port 50472

The connection is now established.

Remote side:

104.20.23.154:443

Local side:

172.26.244.161:50472

Port 50472 is an ephemeral client-side port chosen for this connection.

15. HTTP/2 connection
* using HTTP/2

Curl confirms that the request will use HTTP/2.

* [HTTP/2] [1] OPENED stream for https://example.com/

HTTP/2 uses streams inside a connection.

Curl opened stream 1 for this request.

16. HTTP/2 request headers
* [HTTP/2] [1] [:method: GET]

The HTTP method is GET.

* [HTTP/2] [1] [:scheme: https]

The scheme is HTTPS.

* [HTTP/2] [1] [:authority: example.com]

The requested authority/host is example.com.

* [HTTP/2] [1] [:path: /]

The requested path is /, meaning the root resource.

* [HTTP/2] [1] [user-agent: curl/8.18.0]

Curl identifies itself as version 8.18.0.

* [HTTP/2] [1] [accept: */*]

Curl indicates that it can accept any response media type.

17. HTTP request
> GET / HTTP/2

Curl sends a GET request for / using HTTP/2.

> Host: example.com

The request is addressed to example.com.

> User-Agent: curl/8.18.0

The User-Agent identifies the client.

> Accept: */*

The client accepts any response media type.

>

The empty line marks the end of the HTTP request headers.

18. Request completed
* Request completely sent off

Curl has finished sending the HTTP request.

19. TLS session tickets
* TLSv1.3 (IN), TLS handshake, Newsession Ticket (4):
* TLSv1.3 (IN), TLS handshake, Newsession Ticket (4):

The server sends TLS session tickets.

These can help establish future TLS connections more efficiently.

They are part of TLS session resumption.

20. HTTP response
< HTTP/2 200

The server responded with HTTP status 200.

200 means the request succeeded.

21. Response headers
< date: Sat, 26 Sep 2026 08:26:28 GMT

The server gives the response date/time.

< content-type: text/html

The response body is HTML.

< server: cloudflare

The response identifies Cloudflare as the server/proxy layer.

< last-modified: Tue, 22 Sep 2026 20:16:57 GMT

This gives the last-modified time associated with the resource.

< allow: GET, HEAD

The resource indicates that GET and HEAD methods are allowed.

< accept-ranges: bytes

The server supports byte-range requests.

< age: 4293

The response has been in the cache for approximately 4293 seconds according to the cache metadata.

< cf-cache-status: HIT

Cloudflare indicates that the response was served from its cache.

< cf-ray: a410e24808dff4d3-IXC

This is a Cloudflare request/edge identifier.

<

The response headers have ended.

22. Response body
<!doctype html><html lang="en">...

This is the actual HTML response body returned by example.com.

The browser would use this HTML to render the Example Domain page.

23. Connection remains available
* Connection #0 to host example.com:443 left intact

Curl kept the connection available rather than immediately closing it.

This can allow the connection to be reused.