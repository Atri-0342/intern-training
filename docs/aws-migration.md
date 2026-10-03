# ScanFlow — AWS Migration

## Scope

This document maps the ScanFlow components built locally with Docker Compose to AWS managed services. It is a design exercise; no production AWS resources are required for this checkpoint.

The cost model uses the Mumbai Region (`ap-south-1`) and a small, single-instance, single-AZ starting point. Prices are illustrative on-demand assumptions and exclude applicable taxes, backup/storage extras, NAT Gateway charges, and other services not listed in the assignment.

## 1. Service mapping

| Your stack | AWS service | Gain | Cost or trade-off |
|---|---|---|---|
| Docker Compose on a laptop | EC2 or ECS Fargate | Cloud-hosted compute; ECS/Fargate can replace container lifecycle management while EC2 gives more host control | Ongoing AWS compute cost. EC2 still requires OS/host management; Fargate reduces host management but adds ECS/task-definition/networking configuration |
| PostgreSQL container | Amazon RDS for PostgreSQL | Managed database provisioning, backups, patching, monitoring, and storage management | Higher service cost than a local container; less host-level control; RDS-specific limits/configuration |
| Named volume for uploads | Amazon S3 | Durable object storage independent of compute lifecycle; scalable storage and access controls | Requires S3 API usage, object-key design, IAM permissions, lifecycle/security configuration |
| Nginx | Application Load Balancer | Managed public ingress, health checks, target routing, and load balancing | ALB is not a one-for-one replacement for all Nginx features; hourly and LCU charges |
| Self-signed certificate | AWS Certificate Manager (ACM) | Managed certificate issuance/renewal and integration with ALB/CloudFront | Requires a domain and validation; certificate lifecycle moves to AWS |
| In-process asyncio worker | Amazon SQS + ECS service | Durable queue, retryable work, independent worker scaling, decoupling from API lifecycle | More components and operational configuration; queue semantics must be handled by the application |
| `.env` / `.env.secret` | AWS Secrets Manager / SSM Parameter Store | Centralized configuration/secrets with IAM-controlled access | Additional service dependency and configuration; Secrets Manager can add per-secret/per-API costs |
| `docker logs` | Amazon CloudWatch Logs | Centralized searchable logs, retention, monitoring and alert integration | Log ingestion, storage and queries can incur charges |

### Important storage distinction

The current `postgres-data` Docker volume stores PostgreSQL database files. S3 is **not** the replacement for that database volume. In an AWS design:

- PostgreSQL container + its volume → **RDS for PostgreSQL**
- Future scan/report object storage → **S3**

## 2. Security groups

A simple AWS layout is:

```text
Internet
   |
   | HTTPS :443
   v
+--------------------+
| ALB security group |
+---------+----------+
          |
          | application port
          v
+--------------------+
| ECS/API SG         |
+---------+----------+
          |
          | TCP :5432
          v
+--------------------+
| RDS PostgreSQL SG  |
+--------------------+
```

| Security group / resource | Port | Protocol | Source | Justification |
|---|---:|---|---|---|
| ALB security group | 443 | TCP | `0.0.0.0/0` | Public HTTPS entry point |
| ALB security group | 80 | TCP | `0.0.0.0/0` | Optional HTTP listener used only to redirect to HTTPS |
| ECS/API security group | Application port (for example `8000`, or the container listener port chosen for ECS) | TCP | ALB security group | Only the load balancer should reach the API |
| RDS security group | 5432 | TCP | ECS/API security group | Only the application service needs PostgreSQL access |

### Why 5432 is never open to `0.0.0.0/0`

Port 5432 is an internal database dependency. The API requires access to PostgreSQL, but public Internet clients do not. Allowing `0.0.0.0/0` would expose the database service to arbitrary Internet sources, so the RDS security group should instead allow TCP 5432 only from the API/ECS security group.

## 3. IAM policy for the API role

The API needs only object read/write access to one S3 prefix:

```text
arn:aws:s3:::scanflow-objects/scans/*
```

The least-privilege policy is stored separately in:

```text
`docs/aws-api-s3-policy.json`
```

The API should use an **IAM role** because the workload can receive temporary AWS credentials rather than carrying a long-lived access key in application configuration. This reduces the risk of a permanent credential leaking through source code, images, logs, or `.env` files.

## 4. Cost estimate

### Assumptions

Region:

```text
Asia Pacific (Mumbai) — ap-south-1
```

Workload:

- 1 small EC2 instance: `t4g.micro`, Linux, on-demand, 730 hours/month
- 1 small RDS PostgreSQL instance: `db.t4g.micro`, Single-AZ, on-demand, 730 hours/month
- 1 Application Load Balancer, 730 hours/month
- Assume approximately 1 average LCU for the ALB
- 50 GB S3 Standard storage
- 20 GB/month Internet data transfer out
- Excludes taxes, RDS backup/storage charges, EBS charges, public IPv4 charges, NAT Gateway, CloudFront, CloudWatch ingestion/storage, and request charges

### Illustrative monthly calculation

| Line item | Assumption | Approx. monthly |
|---|---|---:|
| EC2 | `t4g.micro` × 730 h × $0.0056/h | $4.09 |
| RDS PostgreSQL | `db.t4g.micro` × 730 h × $0.021/h | $15.33 |
| ALB | 730 h × $0.0225/h | $16.43 |
| ALB LCU | 1 LCU × 730 h × $0.008/h | $5.84 |
| S3 | 50 GB × $0.025/GB-month | $1.25 |
| Internet data transfer out | 20 GB/month | $0 under the applicable 100 GB/month allowance |
| **Total** |  | **~$42.93/month** |

AWS documents that Application Load Balancers incur an hourly running charge plus LCU usage charges. Actual regional pricing and the precise usage model should be entered in the AWS Pricing Calculator before a real deployment. AWS also states that applicable AWS Free Tier usage includes 100 GB/month of data transfer out to the internet, aggregated across eligible services and regions.

### What surprised me

**The Application Load Balancer is the surprising line item.** Even at low traffic, the ALB has a baseline hourly charge, and LCU usage is additional. It can therefore cost more than expected for a small low-traffic application, before considering other networking costs.

## 5. If this went to production Monday, which one of the twelve rows above would you move first, and why?

If ScanFlow went to production on Monday, I would move the PostgreSQL container to Amazon RDS for PostgreSQL first. PostgreSQL is the stateful part of the system, while the API and Nginx can be treated more like replaceable compute. Moving the database to RDS would separate persistent data from the application containers and shift database infrastructure responsibilities such as storage, backups, patching, and maintenance to a managed service. This would give the rest of the application a more stable foundation for later migrations to ECS/Fargate, S3, ALB, and other managed services.

## Notes on pricing and assumptions

- `t4g.micro` is available in `ap-south-1`.
- Current public pricing references list `t4g.micro` in Mumbai at about $0.0056/hour and `db.t4g.micro` in Mumbai at about $0.021/hour.
- S3 Standard in Mumbai is approximately $0.025/GB-month for the first 50 TB tier.
- The ALB example above uses AWS's published $0.0225/hour and $0.008/LCU-hour figures as an illustrative baseline; confirm the exact Mumbai estimate in the AWS Pricing Calculator.
- The cost estimate intentionally does not pretend to be an AWS bill. It is a reproducible small-workload model for the training checkpoint.

## References

- AWS EC2 documentation: https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/EC2_GetStarted.html
- AWS Security Groups documentation: https://docs.aws.amazon.com/AWSEC2/latest/UserGuide/ec2-security-groups.html
- AWS IAM documentation: https://docs.aws.amazon.com/IAM/latest/UserGuide/IAM_Introduction.html
- AWS RDS documentation: https://docs.aws.amazon.com/AmazonRDS/latest/UserGuide/Welcome.html
- AWS S3 documentation: https://docs.aws.amazon.com/AmazonS3/latest/userguide/Welcome.html
- AWS Elastic Load Balancing pricing: https://aws.amazon.com/elasticloadbalancing/pricing/
- AWS global network / data transfer FAQs: https://aws.amazon.com/about-aws/global-infrastructure/global-network/faqs/
- AWS Pricing Calculator: https://calculator.aws/
