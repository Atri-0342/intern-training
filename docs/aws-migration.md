# ScanFlow — AWS Migration

## Scope

This document maps every component ScanFlow runs today with Docker Compose to the AWS service that would replace it, and says what is gained and what is given up. It is a design exercise: no AWS resources are created.

The cost model uses the Mumbai Region (`ap-south-1`) and a small, single-instance, single-AZ starting point. Prices are on-demand and illustrative; taxes and the items listed under [Excluded from the estimate](#excluded-from-the-estimate) are not included.

## 1. Service mapping

| Your stack | AWS service | Gain | Cost or trade-off |
|---|---|---|---|
| Docker Compose on a laptop | EC2 or ECS Fargate | Cloud-hosted compute. Fargate removes host management; EC2 keeps full host control | Ongoing compute cost. EC2 still needs OS patching; Fargate adds task-definition and networking configuration |
| PostgreSQL container + `postgres-data` volume | Amazon RDS for PostgreSQL | Managed provisioning, automated backups, patching, monitoring, storage growth | Higher cost than a container; less host-level control; RDS-specific limits |
| Moto S3 emulator (scan files) | Amazon S3 | Durable object storage independent of compute; scalable; lifecycle tiering; IAM access control. Fixes the "restart loses every file" problem | Needs bucket policy, IAM and lifecycle configuration; request and transfer charges |
| Nginx (reverse proxy) | Application Load Balancer | Managed public ingress, health checks, target routing | Not a one-for-one replacement (static serving and some rewrites move elsewhere); hourly + LCU charges |
| Cloudflare Quick Tunnel + self-signed cert | ALB + ACM certificate + Route 53 domain | Stable URL, managed certificate issuance and renewal | Needs a domain; the tunnel's "no account needed" convenience is gone |
| In-process asyncio worker | Amazon SQS + ECS service | Durable queue, retries, independent worker scaling, decoupled from the API lifecycle | More components; queue semantics (visibility timeout, duplicates) are now the application's problem. WebSocket events then need a shared channel (see Redis row) |
| Redis container (rate limits) | Amazon ElastiCache | Managed, replicated, patched cache; also the natural home for WebSocket fan-out between API processes | Extra monthly cost; network access must be locked down |
| `.env` / `.env.secret` | Secrets Manager / SSM Parameter Store | Central, IAM-controlled secrets with rotation | Another service dependency; Secrets Manager charges per secret and per API call |
| `docker logs` | Amazon CloudWatch Logs | Central, searchable, retained logs with alarms | Ingestion, storage and query charges |

### Storage distinction

The `postgres-data` volume holds PostgreSQL's files. **S3 is not its replacement.** In AWS the database container and its volume become **RDS**; the scan files that Moto stores become **S3**.

## 2. Request path on AWS

```text
Internet ──HTTPS :443──▶ ALB (ACM certificate, TLS terminates here)
                          │ HTTP, private subnets
                          ▼
                       ECS tasks: API + worker  ──TCP 5432──▶ RDS PostgreSQL
                          │                    └──TCP 6379──▶ ElastiCache
                          └──HTTPS (IAM role)──▶ S3 bucket
```

TLS terminates at the ALB. ALB → API is plain HTTP inside the VPC, which is acceptable at the start. Because ScanFlow holds patient data, the next step would be TLS to the targets and `sslmode=require` to RDS.

## 3. Security groups

```text
Internet
   │  HTTPS :443
   ▼
[ ALB SG ] ──▶ [ API / ECS SG ] ──▶ [ RDS SG ]
                     └─────────────▶ [ ElastiCache SG ]
```

| Security group | Port | Protocol | Source | Justification |
|---|---:|---|---|---|
| ALB | 443 | TCP | `0.0.0.0/0` | Public HTTPS entry point |
| ALB | 80 | TCP | `0.0.0.0/0` | Optional; only to redirect to HTTPS |
| API / ECS | container port (for example `80`) | TCP | the ALB security group | Only the load balancer may reach the API |
| RDS | 5432 | TCP | the API / ECS security group | Only the application needs the database |
| ElastiCache | 6379 | TCP | the API / ECS security group | Only the application needs the cache |

**Why 5432 is never open to `0.0.0.0/0`, even though the API needs the database.** The API needs *a* path to PostgreSQL, not the whole internet. Allowing `0.0.0.0/0` would let any host on earth attempt to authenticate to the database; referencing the API's security group as the source allows exactly the application tier and nothing else, and follows the API if its IP addresses change.

## 4. IAM policy for the API role

The API's role is limited to one bucket prefix. The policy is in [`aws-api-s3-policy.json`](aws-api-s3-policy.json):

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Sid": "ScanObjectsReadWriteDelete",
      "Effect": "Allow",
      "Action": [
        "s3:PutObject",
        "s3:GetObject",
        "s3:DeleteObject",
        "s3:AbortMultipartUpload"
      ],
      "Resource": "arn:aws:s3:::scanflow-scans/scans/*"
    }
  ]
}
```

The brief calls for `PutObject` and `GetObject` only. The code also calls `delete_file` (admin scan deletion, rollback of a failed upload, replacing a file on update), so `DeleteObject` is required or those paths would fail with `AccessDenied`. `AbortMultipartUpload` is included because boto3 splits files over 8 MB (the app allows up to 20 MB) into multipart uploads and needs it to clean up a failed one. Nothing else is granted: no `ListBucket` (so a `GetObject` for a missing key returns `403`, not `404`), no other prefixes, no other buckets. `scanflow-scans` is the development bucket name; a real bucket name must be globally unique.

**Why a role and not an access key.** A role gives the running task short-lived credentials that AWS rotates automatically and that never appear in the source tree, the image, a log, or a `.env` file. An access key is a long-lived secret that has to be stored, rotated and protected, and one leak grants its permissions until someone notices.

## 5. Moving file storage from Moto to S3

ScanFlow already talks to storage through boto3 and stores only `file_key` (`scans/{scan-id}.{ext}`) in PostgreSQL, so the application code does not change.

| Step | Change |
|---|---|
| 1 | Create the S3 bucket in `ap-south-1`; block all public access |
| 2 | Set `S3_BUCKET` and `S3_REGION`; **remove `S3_ENDPOINT_URL`** (that variable is what points boto3 at Moto) |
| 3 | Delete the dummy `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY`; attach the IAM role above to the task |
| 4 | Keep Moto for local development and automated tests |

**Later improvement: presigned uploads.** Today a 15 MB scan travels browser → FastAPI → S3, so the API handles every byte. With a presigned URL the API issues a short-lived, single-object URL (for example `POST /v1/scans/upload-url` for `scans/{id}.jpg`), the browser uploads straight to S3, and the API stores the key afterwards. The API no longer carries the file transfer. Two things would have to be rebuilt server-side, because today the API enforces them itself: the 20 MB and content-type limits (use a presigned *POST* with a `content-length-range` condition) and the idempotency check. This is planned, not implemented.

## 6. Cost estimate

### Assumptions

- Region: Asia Pacific (Mumbai), `ap-south-1`
- 1 × EC2 `t4g.micro`, Linux, on-demand, 730 h/month
- 1 × RDS PostgreSQL `db.t4g.micro`, Single-AZ, on-demand, 730 h/month
- 1 × Application Load Balancer, 730 h/month, about 1 LCU on average
- 50 GB S3 Standard
- 20 GB/month data transfer out to the internet

### Monthly calculation

| Line item | Assumption | Approx. monthly |
|---|---|---:|
| EC2 | `t4g.micro` × 730 h × $0.0056/h | $4.09 |
| RDS PostgreSQL | `db.t4g.micro` × 730 h × $0.021/h | $15.33 |
| ALB hours | 730 h × $0.0225/h | $16.43 |
| ALB LCU | 1 LCU × 730 h × $0.008/LCU-h | $5.84 |
| S3 | 50 GB × $0.025/GB-month | $1.25 |
| Data transfer out | 20 GB | $0 (inside the 100 GB/month free allowance) |
| **Total** | | **≈ $42.93 / month** |

The EC2 and RDS rates match published Mumbai on-demand prices. The ALB hourly and LCU rates are AWS's published baseline and were **not** confirmed for Mumbai; check them in the [AWS Pricing Calculator](https://calculator.aws/) before relying on the total.

### Excluded from the estimate

- Taxes; EBS volume and RDS storage/backup charges
- **Public IPv4 addresses**: billed hourly per address, and an ALB uses at least two, so this is a few dollars a month that is easy to forget
- NAT Gateway, CloudFront, CloudWatch ingestion and storage
- ElastiCache (the Redis row) and SQS/second ECS service (the worker row); the estimate covers the smallest *current* shape, not the full target mapping
- S3 request charges

### What surprised me

**The load balancer.** At this size the ALB (≈ $22/month for hours plus LCU) costs more than the EC2 instance and more than the database, before any real traffic. For a low-traffic app it is the largest line item, which is the opposite of what the architecture diagram suggests.

## 7. What I would move first

If this went to production on Monday I would move the PostgreSQL container to **RDS** first. The database is the only stateful part; the API, Nginx and Redis can be recreated from the repository at any time, but patient records cannot. RDS gives automated backups, point-in-time recovery and patching, and it separates the data from the compute so every later move (ECS, ALB, S3) happens on top of a durable foundation. It also removes today's single point of failure: a database volume on one laptop, protected only by a `pg_dump` someone has to remember to take.

## Notes

- Mumbai on-demand rates for `t4g.micro` ($0.0056/h) and `db.t4g.micro` ($0.021/h) were checked against public price lists. Regional prices change; the Pricing Calculator is the source of truth.
- This is a reproducible small-workload model, not a bill.

## References

- [Amazon EC2: get started](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/EC2_GetStarted.html)
- [EC2 security groups](https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-security-groups.html)
- [What is IAM?](https://docs.aws.amazon.com/IAM/latest/UserGuide/IAM_Introduction.html)
- [What is Amazon RDS?](https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/Welcome.html)
- [What is Amazon S3?](https://docs.aws.amazon.com/AmazonS3/latest/userguide/Welcome.html)
- [Elastic Load Balancing pricing](https://aws.amazon.com/elasticloadbalancing/pricing/)
- [AWS Pricing Calculator](https://calculator.aws/)
