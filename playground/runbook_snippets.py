RUNBOOKS = [
    {
        "id": "rb-db-unavailable",
        "services": ["payment-worker", "payment-outbox-relay", "queue-service"],
        "title": "Postgres connection refused or unavailable",
        "text": (
            "Workers log OperationalError connection refused to Postgres and retry the same offset "
            "every few seconds. Processing is blocked, so consumer lag grows. Check that the database "
            "container is running and healthy, disk space, max connections and name resolution. "
            "Restore the database; the worker resumes by itself because the offset was never committed. "
            "Verify that lag drains."
        ),
    },
    {
        "id": "rb-kafka-publish",
        "services": ["queue-outbox-relay", "payment-outbox-relay"],
        "title": "Outbox relay cannot publish to Kafka",
        "text": (
            "Outbox messages are not delivered: message timed out or broker not available. Outbox rows "
            "stay unpublished and downstream services receive no events. Check broker health, advertised "
            "listeners and the network path from the relay container. Restore the broker; the relay "
            "retries. Verify that the unpublished row count drops."
        ),
    },
    {
        "id": "rb-notification-retry",
        "services": ["notification-worker", "notification-retry-worker"],
        "title": "Notification provider errors and retry topics",
        "text": (
            "The SMS or email provider returns 5xx errors or times out. Failed messages are routed to "
            "retry topics with increasing delay and finally to the dead-letter queue. Check provider "
            "status, credentials and rate limits. Transient errors need no action; watch retry topic depth."
        ),
    },
    {
        "id": "rb-dlq-schema",
        "services": ["payment-worker", "notification-worker"],
        "title": "Message parked in a dead-letter queue",
        "text": (
            "A consumer cannot process a message, for example an unsupported event_version or a schema "
            "mismatch, and parks it in the DLQ. Compare producer and consumer versions and check Schema "
            "Registry compatibility. Deploy a consumer that understands the version, then replay the DLQ "
            "messages. Never delete DLQ messages without review."
        ),
    },
    {
        "id": "rb-rebalance",
        "services": ["notification-worker", "payment-worker", "queue-saga-worker"],
        "title": "Consumer group rebalance",
        "text": (
            "Partitions assigned or removed during a consumer group rebalance. Normal after a deploy or "
            "restart. Investigate only if rebalances are frequent: flapping consumers, session timeouts "
            "or long processing."
        ),
    },
    {
        "id": "rb-saga-timeout",
        "services": ["queue-saga-worker"],
        "title": "Saga timeout cancelled expired reservations",
        "text": (
            "The saga worker cancels reservations that expired before payment completed. This is normal "
            "behaviour. Investigate if the count spikes: payment slow or down, or the deposit flow is stalled."
        ),
    },
    {
        "id": "rb-idempotency",
        "services": ["notification-worker", "payment-worker"],
        "title": "Duplicate event ignored",
        "text": (
            "Kafka delivers at least once, so events can be redelivered. Consumers deduplicate by event id "
            "and ignore repeats. Normal. Investigate only if duplicates spike: commit failures or frequent "
            "rebalances."
        ),
    },
    {
        "id": "rb-schema-registry",
        "services": ["queue-service", "payment-worker", "notification-worker"],
        "title": "Schema Registry unreachable or incompatible",
        "text": (
            "Producers fail to serialize or consumers fail to deserialize because the Schema Registry is "
            "unreachable or a subject is incompatible. Check the registry container, the compatibility "
            "mode and recent schema changes."
        ),
    },
]

# (raw log line, id of the runbook that should be the top match)
CASES = [
    (
        "payment-worker  | 2026-11-14 10:02:11,532 WARNING payment.worker: Retrying offset 4812 in 5s: "
        'OperationalError: connection to server at "payment-postgres" (172.19.0.6), port 5432 failed: Connection refused',
        "rb-db-unavailable",
    ),
    (
        "queue-outbox-relay  | 2026-11-14 10:03:40,118 WARNING app.events.publisher: Outbox message "
        '9b1e6c2a-31f4-4d0e-8a77-5c1f0d2e9a10 not delivered: KafkaError{code=_MSG_TIMED_OUT,val=-192,str="Local: Message timed out"}',
        "rb-kafka-publish",
    ),
    (
        "notification-worker  | 2026-11-14 10:04:02,771 WARNING notification.worker: Offset 977 failed "
        "(HTTPError: SMS provider returned 503) -> sent to queue.events.notification-service.retry-10s",
        "rb-notification-retry",
    ),
    (
        "payment-worker  | 2026-11-14 10:06:48,290 ERROR payment.worker: Offset 5120 parked in "
        "queue.events.payment-service.dlq: unsupported event_version 2 for TicketReserved",
        "rb-dlq-schema",
    ),
    (
        "notification-worker  | 2026-11-14 10:07:30,455 INFO notification.worker: "
        "Partitions removed: ['queue.events[1]', 'queue.events[2]']",
        "rb-rebalance",
    ),
    (
        "queue-saga-worker  | 2026-11-14 10:05:15,004 INFO queue.saga_worker: Saga timeout: cancelled 3 expired reservation(s)",
        "rb-saga-timeout",
    ),
    (
        "notification-worker  | 2026-11-14 10:08:21,903 INFO app.handlers: Duplicate event "
        "3f2a91c4-77de-4b0a-9c11-0d5e6a7b8c92 ignored (already sent)",
        "rb-idempotency",
    ),
    (
        "queue-service  | 2026-11-14 10:09:55,310 ERROR app.events.producer: Failed to serialize event for subject "
        "queue.events-value: Connection refused (http://schema-registry:8081)",
        "rb-schema-registry",
    ),
]
