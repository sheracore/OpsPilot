# (log line, expected component, expected severity)
SAMPLES = [
    (
        "payment-worker  | 2026-11-14 10:02:11,532 WARNING payment.worker: Retrying offset 4812 in 5s: "
        'OperationalError: connection to server at "payment-postgres" (172.19.0.6), port 5432 failed: Connection refused',
        "payment-worker",
        "high",
    ),
    (
        "queue-outbox-relay  | 2026-11-14 10:03:40,118 WARNING app.events.publisher: Outbox message "
        '9b1e6c2a-31f4-4d0e-8a77-5c1f0d2e9a10 not delivered: KafkaError{code=_MSG_TIMED_OUT,val=-192,str="Local: Message timed out"}',
        "queue-outbox-relay",
        "high",
    ),
    (
        "notification-worker  | 2026-11-14 10:04:02,771 WARNING notification.worker: Offset 977 failed "
        "(HTTPError: SMS provider returned 503) -> sent to queue.events.notification-service.retry-10s",
        "notification-worker",
        "medium",
    ),
    (
        "queue-saga-worker  | 2026-11-14 10:05:15,004 INFO queue.saga_worker: Saga timeout: cancelled 3 expired reservation(s)",
        "queue-saga-worker",
        "low",
    ),
    (
        "payment-worker  | 2026-11-14 10:06:48,290 ERROR payment.worker: Offset 5120 parked in "
        "queue.events.payment-service.dlq: unsupported event_version 2 for TicketReserved",
        "payment-worker",
        "high",
    ),
    (
        "notification-worker  | 2026-11-14 10:07:30,455 INFO notification.worker: "
        "Partitions removed: ['queue.events[1]', 'queue.events[2]']",
        "notification-worker",
        "low",
    ),
]
