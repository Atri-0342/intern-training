# Queue and Worker Notes

## Current implementation

ScanFlow currently uses an asynchronous worker implemented as an `asyncio` task started during FastAPI application startup.

The worker continuously checks PostgreSQL for analysis jobs with status `uploaded`.

When it finds a job, it safely claims the job using:

SELECT ... FOR UPDATE SKIP LOCKED

The job is then changed to `running`.

The worker simulates analysis using an asynchronous sleep and writes a synthetic confidence value and finding before changing the job to `done`.

The API can retrieve the latest analysis result through:

GET /v1/scans/{scan_id}/analysis

## Job lifecycle

uploaded -> running -> done

If processing raises an exception:

running -> retry_count + 1 -> uploaded -> retry

After three failed attempts:

running -> failed

The error message is stored in the `error` column.

## Why PostgreSQL is being used as the job queue

For the training implementation, PostgreSQL acts as a simple persistent job queue.

The `analysis_jobs` table stores the state of each analysis job.

Using `FOR UPDATE SKIP LOCKED` allows multiple workers to safely claim different jobs without waiting for jobs already locked by another worker.

This prevents two workers from claiming the same job at the same time.

## What happens if the FastAPI process dies?

Consider this sequence:

uploaded -> worker claims job -> running -> FastAPI process crashes

The job may remain in the `running` state even though no worker is processing it anymore.

The current implementation includes stale-job recovery. A job that remains `running` beyond the configured recovery period can be returned to `uploaded`, allowing another worker cycle to process it.

This provides a basic recovery mechanism for the training project.

## What would happen in production?

A production system would normally use a dedicated durable queue or message broker instead of relying entirely on PostgreSQL polling.

Examples include:

* RabbitMQ
* Redis-based queues
* AWS SQS
* Kafka

A dedicated queue provides purpose-built mechanisms for message delivery, acknowledgements, visibility timeouts, retries, dead-letter queues, and worker coordination.

The production architecture could therefore look like:

Client -> FastAPI -> Create analysis job -> Durable Queue -> Worker Pool -> Inference -> PostgreSQL

## Important limitation of the current implementation

The current worker is an in-process `asyncio` task.

If the FastAPI process is terminated, the worker task also terminates.

The database preserves the analysis job, but the in-memory worker itself does not survive the process termination.

The stale-job recovery mechanism allows the database job to become eligible for processing again after the application restarts.

A dedicated production queue would provide stronger delivery and worker lifecycle guarantees.

## Training conclusion

The current implementation demonstrates:

* asynchronous job processing
* persistent job state
* safe job claiming
* `FOR UPDATE SKIP LOCKED`
* retry handling
* terminal failure handling
* stale-job recovery
* separation between HTTP request handling and background processing

It is intentionally simpler than a production distributed queue architecture.
