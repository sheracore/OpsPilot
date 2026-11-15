from enum import StrEnum

from pydantic import BaseModel, ConfigDict, Field


class Severity(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class Component(StrEnum):
    # values = docker compose service names in queueless
    QUEUE_SERVICE = "queue-service"
    QUEUE_OUTBOX_RELAY = "queue-outbox-relay"
    QUEUE_SAGA_WORKER = "queue-saga-worker"
    PAYMENT_WORKER = "payment-worker"
    PAYMENT_OUTBOX_RELAY = "payment-outbox-relay"
    NOTIFICATION_WORKER = "notification-worker"
    NOTIFICATION_RETRY_WORKER = "notification-retry-worker"
    NOTIFICATION_API = "notification-api"
    KAFKA = "kafka"
    POSTGRES = "postgres"
    SCHEMA_REGISTRY = "schema-registry"
    UNKNOWN = "unknown"


class LogExplanation(BaseModel):
    model_config = ConfigDict(extra="forbid")

    summary: str = Field(min_length=1, max_length=300)
    severity: Severity
    component: Component